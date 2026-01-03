import aiohttp
from typing import Optional, Dict, List, Any
from Config import Config


class G2BulkAPI:
    BASE_URL = "https://api.g2bulk.com/v1"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.G2BULK_API_KEY
        if not self.api_key:
            raise ValueError("G2BULK_API_KEY is not set in Config")

    def _get_headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def get_me(self) -> Dict[str, Any]:
        """Get authenticated user details including balance"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/getMe", headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def get_games(self) -> List[Dict[str, Any]]:
        """Get all supported games"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/games", headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("games", [])
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def get_game_fields(self, game_code: str) -> Dict[str, Any]:
        """Get required input fields for a specific game"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/games/fields",
                headers=self._get_headers(),
                json={"game": game_code},
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def get_game_servers(self, game_code: str) -> Optional[Dict[str, str]]:
        """Get available server list for a specific game. Returns None if servers are not required."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/games/servers",
                headers=self._get_headers(),
                json={"game": game_code},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("servers")
                elif response.status == 403:
                    # Game does not require servers
                    return None
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def check_player_id(
        self, game_code: str, user_id: str, server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a player ID before placing an order"""
        payload = {"game": game_code, "user_id": user_id}
        if server_id:
            payload["server_id"] = server_id

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/games/checkPlayerId",
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def get_game_catalogue(self, game_code: str) -> Dict[str, Any]:
        """Get all available denominations/packages for a specific game"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/games/{game_code}/catalogue",
                headers=self._get_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def create_game_order(
        self,
        game_code: str,
        catalogue_name: str,
        player_id: str,
        server_id: Optional[str] = None,
        remark: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place a game top-up order"""
        payload = {"catalogue_name": catalogue_name, "player_id": player_id}
        if server_id:
            payload["server_id"] = server_id
        if remark:
            payload["remark"] = remark
        if callback_url:
            payload["callback_url"] = callback_url

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/games/{game_code}/order",
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def get_order_status(self, order_id: int, game_code: str) -> Dict[str, Any]:
        """Check the current status of a specific game order"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/games/order/status",
                headers=self._get_headers(),
                json={"order_id": order_id, "game": game_code},
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )

    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get complete game top-up order history"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/games/orders", headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("orders", [])
                else:
                    error_data = await response.json()
                    raise Exception(
                        f"API Error: {error_data.get('message', 'Unknown error')}"
                    )
