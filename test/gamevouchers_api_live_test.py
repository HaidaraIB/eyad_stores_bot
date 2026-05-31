"""
GameVouchers API live test script.

Run from project root:
    python test/gamevouchers_api_live_test.py

Uncomment one test call at a time in main() to inspect raw HTTP status + JSON in the terminal.

Recommended order:
  1. discover_sample_products() — copy suggested product IDs into config below
  2. Read-only tests (products, balance, auth errors)
  3. Purchase error tests (no balance spend)
  4. Paid purchase tests (SPENDS REAL BALANCE — use with care)
  5. Operation status tests (paste operation IDs into config first)
"""

import asyncio
import json
import os
import sys
import uuid
from typing import Any, Dict, Optional

import aiohttp
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Config import Config
from services.providers.gamevouchers_provider import (
    gv_product_requires_player_id,
    gv_product_uses_quantity_flow,
)

# ---------------------------------------------------------------------------
# Config — edit before running
# ---------------------------------------------------------------------------

INVALID_API_KEY = "invalid-key-for-testing"
FAKE_PRODUCT_ID = 999_999_999
FAKE_OPERATION_ID = "00000000-0000-0000-0000-000000000000"
TEST_GAME_UID = "1234567890"

VOUCHER_PRODUCT_ID: Optional[int] = None
TOPUP_PRODUCT_ID: Optional[int] = None
OPERATION_ID_PROCESSING: Optional[str] = None
OPERATION_ID_PENDING: Optional[str] = None
OPERATION_ID_COMPLETED: Optional[str] = None
OPERATION_ID_FAILED: Optional[str] = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api_key(api_key: Optional[str] = None) -> str:
    return api_key or Config.GAMEVOUCHERS_API_KEY


def _base_url() -> str:
    return Config.GAMEVOUCHERS_BASE_URL.rstrip("/")


async def raw_request(
    method: str,
    path: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Low-level HTTP call; never raises on HTTP errors."""
    url = f"{_base_url()}{path}"
    headers = {
        "Authorization": f"Bearer {_api_key(api_key)}",
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    async with aiohttp.ClientSession() as session:
        async with session.request(
            method, url, headers=headers, json=json_body
        ) as response:
            text = await response.text()
            body: Any = None
            if response.status != 204 and text:
                try:
                    body = json.loads(text)
                except json.JSONDecodeError:
                    body = None
            return {"status": response.status, "body": body, "text": text}


def print_result(label: str, result: Dict[str, Any]) -> None:
    print("\n" + "=" * 72)
    print(f"  {label}")
    print("=" * 72)
    print(f"HTTP {result['status']}")
    if result["body"] is not None:
        print(json.dumps(result["body"], indent=2, ensure_ascii=False))
    elif result["text"]:
        print(result["text"])
    else:
        print("(empty body)")
    print("=" * 72 + "\n")


def _require_product_id(product_id: Optional[int], label: str) -> int:
    if product_id is None:
        raise ValueError(
            f"{label}: set product ID in config (run discover_sample_products() first)"
        )
    return product_id


def _require_operation_id(operation_id: Optional[str], label: str) -> str:
    if not operation_id:
        raise ValueError(
            f"{label}: set operation ID in config (from a real purchase response)"
        )
    return operation_id


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


async def discover_sample_products() -> None:
    """List products and suggest voucher vs top-up IDs for config."""
    result = await raw_request("GET", "/api/v1/products")
    print_result("discover_sample_products — GET /api/v1/products", result)

    products = result["body"]
    if not isinstance(products, list):
        print("Unexpected response shape; expected a JSON array.")
        return

    active = [p for p in products if p.get("is_active", True)]
    print(f"Active products: {len(active)} / {len(products)}\n")

    voucher_sample = None
    topup_sample = None
    for p in active:
        if voucher_sample is None and gv_product_uses_quantity_flow(p):
            voucher_sample = p
        if topup_sample is None and gv_product_requires_player_id(p):
            topup_sample = p
        if voucher_sample and topup_sample:
            break

    def _fmt(p: dict) -> str:
        return (
            f"id={p.get('id')} name={p.get('name')!r} "
            f"category={p.get('category_name')!r} "
            f"type={p.get('type')!r} requires_game_uid={p.get('requires_game_uid')} "
            f"price={p.get('price')} stock={p.get('stock')}"
        )

    print("Suggested config values (copy into this file):")
    if voucher_sample:
        print(f"  VOUCHER_PRODUCT_ID = {voucher_sample.get('id')}")
        print(f"    {_fmt(voucher_sample)}")
    else:
        print("  VOUCHER_PRODUCT_ID = None  # no voucher-style product found")

    if topup_sample:
        print(f"  TOPUP_PRODUCT_ID = {topup_sample.get('id')}")
        print(f"    {_fmt(topup_sample)}")
    else:
        print("  TOPUP_PRODUCT_ID = None  # no top-up product found")


# ---------------------------------------------------------------------------
# GET /api/v1/products
# ---------------------------------------------------------------------------


async def test_products_200_success() -> None:
    result = await raw_request("GET", "/api/v1/products")
    print_result("GET /api/v1/products — 200 success (valid API key)", result)


async def test_products_401_unauthorized() -> None:
    result = await raw_request("GET", "/api/v1/products", api_key=INVALID_API_KEY)
    print_result("GET /api/v1/products — 401 unauthorized (invalid API key)", result)


# ---------------------------------------------------------------------------
# GET /api/v1/balance
# ---------------------------------------------------------------------------


async def test_balance_200_success() -> None:
    result = await raw_request("GET", "/api/v1/balance")
    print_result("GET /api/v1/balance — 200 success (valid API key)", result)


async def test_balance_401_unauthorized() -> None:
    result = await raw_request("GET", "/api/v1/balance", api_key=INVALID_API_KEY)
    print_result("GET /api/v1/balance — 401 unauthorized (invalid API key)", result)


# ---------------------------------------------------------------------------
# POST /api/v1/purchases
# ---------------------------------------------------------------------------


async def test_purchase_202_voucher() -> None:
    """WARNING: SPENDS REAL BALANCE."""
    product_id = _require_product_id(VOUCHER_PRODUCT_ID, "test_purchase_202_voucher")
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": product_id, "quantity": 1},
        idempotency_key=str(uuid.uuid4()),
    )
    print_result(
        "POST /api/v1/purchases — 202 voucher (quantity=1, no game_uid)", result
    )
    if result["status"] == 202 and isinstance(result["body"], dict):
        op_id = result["body"].get("operation_id")
        if op_id:
            print(f"  -> paste into config: OPERATION_ID_PROCESSING = {op_id!r}\n")


async def test_purchase_202_topup() -> None:
    """WARNING: SPENDS REAL BALANCE."""
    product_id = _require_product_id(TOPUP_PRODUCT_ID, "test_purchase_202_topup")
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={
            "product_id": product_id,
            "quantity": 1,
            "game_uid": TEST_GAME_UID,
        },
        idempotency_key=str(uuid.uuid4()),
    )
    print_result(
        f"POST /api/v1/purchases — 202 top-up (game_uid={TEST_GAME_UID!r})",
        result,
    )
    if result["status"] == 202 and isinstance(result["body"], dict):
        op_id = result["body"].get("operation_id")
        if op_id:
            print(f"  -> paste into config: OPERATION_ID_PROCESSING = {op_id!r}\n")


async def test_purchase_401_unauthorized() -> None:
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": FAKE_PRODUCT_ID, "quantity": 1},
        api_key=INVALID_API_KEY,
        idempotency_key=str(uuid.uuid4()),
    )
    print_result("POST /api/v1/purchases — 401 unauthorized (invalid API key)", result)


async def test_purchase_404_invalid_product() -> None:
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": FAKE_PRODUCT_ID, "quantity": 1},
        idempotency_key=str(uuid.uuid4()),
    )
    print_result("POST /api/v1/purchases — 404 invalid product_id", result)


async def test_purchase_400_invalid_quantity() -> None:
    product_id = _require_product_id(
        TOPUP_PRODUCT_ID or VOUCHER_PRODUCT_ID, "test_purchase_400_invalid_quantity"
    )
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": product_id, "quantity": 0},
        idempotency_key=str(uuid.uuid4()),
    )
    print_result("POST /api/v1/purchases — 400 invalid quantity (quantity=0)", result)


async def test_purchase_422_missing_game_uid() -> None:
    product_id = _require_product_id(
        TOPUP_PRODUCT_ID, "test_purchase_422_missing_game_uid"
    )
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": product_id, "quantity": 1},
        idempotency_key=str(uuid.uuid4()),
    )
    print_result(
        "POST /api/v1/purchases — 422 missing game_uid (top-up product)", result
    )


async def test_purchase_409_idempotency_replay() -> None:
    product_id = _require_product_id(
        VOUCHER_PRODUCT_ID or TOPUP_PRODUCT_ID, "test_purchase_409_idempotency_replay"
    )
    key = str(uuid.uuid4())
    first = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": product_id, "quantity": 1},
        idempotency_key=key,
    )
    print_result(
        "POST /api/v1/purchases — idempotency first call (may be 202 or error)", first
    )
    second = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": product_id, "quantity": 1},
        idempotency_key=key,
    )
    print_result("POST /api/v1/purchases — 409 idempotency replay (same key)", second)


async def test_purchase_402_insufficient_balance() -> None:
    """Environment-dependent: may return 402, 409, or another error if balance is sufficient."""
    product_id = _require_product_id(
        VOUCHER_PRODUCT_ID or TOPUP_PRODUCT_ID, "test_purchase_402_insufficient_balance"
    )
    result = await raw_request(
        "POST",
        "/api/v1/purchases",
        json_body={"product_id": product_id, "quantity": 10},
        idempotency_key=str(uuid.uuid4()),
    )
    print_result(
        "POST /api/v1/purchases — 402 insufficient balance (qty=10, may vary)", result
    )


# ---------------------------------------------------------------------------
# GET /api/v1/operations/{operation_id}
# ---------------------------------------------------------------------------


async def test_operation_200_processing() -> None:
    op_id = _require_operation_id(
        OPERATION_ID_PROCESSING, "test_operation_200_processing"
    )
    result = await raw_request("GET", f"/api/v1/operations/{op_id}")
    print_result(f"GET /api/v1/operations/{{id}} — 200 PROCESSING ({op_id})", result)


async def test_operation_200_pending() -> None:
    op_id = _require_operation_id(OPERATION_ID_PENDING, "test_operation_200_pending")
    result = await raw_request("GET", f"/api/v1/operations/{op_id}")
    print_result(f"GET /api/v1/operations/{{id}} — 200 PENDING ({op_id})", result)


async def test_operation_200_completed() -> None:
    op_id = _require_operation_id(
        OPERATION_ID_COMPLETED, "test_operation_200_completed"
    )
    result = await raw_request("GET", f"/api/v1/operations/{op_id}")
    print_result(f"GET /api/v1/operations/{{id}} — 200 COMPLETED ({op_id})", result)


async def test_operation_200_failed() -> None:
    op_id = _require_operation_id(OPERATION_ID_FAILED, "test_operation_200_failed")
    result = await raw_request("GET", f"/api/v1/operations/{op_id}")
    print_result(f"GET /api/v1/operations/{{id}} — 200 FAILED ({op_id})", result)


async def test_operation_404_not_found() -> None:
    result = await raw_request("GET", f"/api/v1/operations/{FAKE_OPERATION_ID}")
    print_result(
        "GET /api/v1/operations/{id} — 404 not found (fake operation_id)", result
    )


async def test_operation_401_unauthorized() -> None:
    op_id = OPERATION_ID_PROCESSING or FAKE_OPERATION_ID
    result = await raw_request(
        "GET",
        f"/api/v1/operations/{op_id}",
        api_key=INVALID_API_KEY,
    )
    print_result(
        "GET /api/v1/operations/{id} — 401 unauthorized (invalid API key)", result
    )


async def poll_operation_after_purchase(
    operation_id: str,
    *,
    interval_seconds: float = 3.0,
    max_attempts: int = 20,
) -> None:
    """Poll operation status until terminal state or max attempts."""
    print(f"\nPolling operation {operation_id!r} every {interval_seconds}s ...\n")
    for attempt in range(1, max_attempts + 1):
        result = await raw_request("GET", f"/api/v1/operations/{operation_id}")
        status = None
        if isinstance(result["body"], dict):
            status = (result["body"].get("status") or "").upper()
        print_result(f"poll attempt {attempt}/{max_attempts} — status={status}", result)
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            print(f"Terminal status reached: {status}\n")
            return
        await asyncio.sleep(interval_seconds)
    print("Max poll attempts reached without terminal status.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    load_dotenv()
    if not Config.GAMEVOUCHERS_API_KEY:
        print("ERROR: GAMEVOUCHERS_API_KEY is not set in .env")
        return

    print("GameVouchers API live tests — uncomment one call at a time\n")
    print(f"Base URL: {_base_url()}\n")

    # --- Safe / read-only ---
    # await discover_sample_products()
    # await test_products_200_success()          # expected: HTTP 200
    # await test_products_401_unauthorized()     # expected: HTTP 401
    # await test_balance_200_success()           # expected: HTTP 200
    # await test_balance_401_unauthorized()      # expected: HTTP 401

    # --- Purchase errors (no balance spend) ---
    # await test_purchase_401_unauthorized()     # expected: HTTP 401
    # await test_purchase_404_invalid_product()  # expected: HTTP 404
    # await test_purchase_400_invalid_quantity() # expected: HTTP 400 (set product ID first)
    # await test_purchase_422_missing_game_uid() # expected: HTTP 422 (set TOPUP_PRODUCT_ID first)
    # await test_purchase_409_idempotency_replay() # expected: HTTP 409 or 202 replay (may spend on first call!)
    # await test_purchase_402_insufficient_balance() # expected: HTTP 402 (environment-dependent, may spend!)

    # --- PAID: SPENDS REAL BALANCE — uncomment only when you accept balance spend ---
    # await test_purchase_202_voucher()          # expected: HTTP 202 (set VOUCHER_PRODUCT_ID first)
    # await test_purchase_202_topup()            # expected: HTTP 202 (set TOPUP_PRODUCT_ID first)

    # --- Operation status (paste operation IDs into config first) ---
    # await test_operation_200_processing()      # expected: HTTP 200, status PROCESSING
    # await test_operation_200_pending()         # expected: HTTP 200, status PENDING
    # await test_operation_200_completed()       # expected: HTTP 200, status COMPLETED (+ codes)
    # await test_operation_200_failed()          # expected: HTTP 200, status FAILED (+ error_message)
    # await test_operation_404_not_found()       # expected: HTTP 404
    # await test_operation_401_unauthorized()    # expected: HTTP 401

    # --- Optional: poll after a 202 purchase (paste operation_id from response) ---
    # await poll_operation_after_purchase("paste-operation-id-here")


if __name__ == "__main__":
    asyncio.run(main())
