from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from common.keyboards import build_request_buttons
import os
import models
import uuid
from datetime import datetime
from custom_filters import HasPermission
from models import Permission


def check_hidden_permission_requests_keyboard(
    context: ContextTypes.DEFAULT_TYPE, admin_id: int
):
    if not HasPermission.check(admin_id, Permission.VIEW_IDS):
        reply_markup = ReplyKeyboardRemove()
    elif (
        not context.user_data.get("request_keyboard_hidden", None)
        or not context.user_data["request_keyboard_hidden"]
    ):
        context.user_data["request_keyboard_hidden"] = False
        request_buttons = build_request_buttons()
        reply_markup = ReplyKeyboardMarkup(request_buttons, resize_keyboard=True)
        request_buttons = build_request_buttons()
        reply_markup = ReplyKeyboardMarkup(request_buttons, resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardRemove()
    return reply_markup


def uuid_generator():
    return uuid.uuid4().hex


def create_folders():
    os.makedirs("data", exist_ok=True)


def format_datetime(d: datetime):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def format_float(f: float):
    return f"{float(f):,.2f}".rstrip("0").rstrip(".")


def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_exchange_rate():
    """Get USD to Sudan currency exchange rate from database"""
    from models.DB import session_scope
    with session_scope() as session:
        settings = session.query(models.GeneralSettings).first()
        if settings:
            return settings.usd_to_sudan_rate
        else:
            # Create default settings if not exists
            settings = models.GeneralSettings()
            session.add(settings)
            session.commit()
            return 1.0