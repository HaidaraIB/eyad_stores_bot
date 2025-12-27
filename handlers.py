from telegram import Update
from start import start_command, admin_command
from common.common import create_folders
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_user_home_page_handler,
)
from common.error_handler import error_handler
from common.force_join import check_joined_handler

from user.user_calls import *
from user.user_settings import *

from admin.admin_calls import *
from admin.admin_settings import *
from admin.broadcast import *
from admin.ban import *
from admin.force_join_chats_settings import *
from admin.manage_users_settings import *
from admin.games_settings import *
from admin.items_settings import *
from admin.payment_methods_settings import *
from admin.orders_settings import *

from models import init_db

from MyApp import MyApp


def setup_and_run():
    create_folders()
    init_db()

    app = MyApp.build_app()

    # USER SETTINGS
    app.add_handler(user_settings_handler)
    app.add_handler(change_lang_handler)
    app.add_handler(user_profile_handler)

    # USER ORDERS
    app.add_handler(back_to_charging_balance_orders_handler)
    app.add_handler(back_to_purchase_orders_handler)
    app.add_handler(my_orders_handler)
    app.add_handler(show_charging_balance_orders_handler)
    app.add_handler(show_purchase_orders_handler)
    app.add_handler(view_charging_balance_order_handler)
    app.add_handler(view_purchase_order_handler)
    app.add_handler(purchase_order_handler)
    app.add_handler(charge_balance_handler)

    # ADMIN SETTINGS
    app.add_handler(show_admins_handler)
    app.add_handler(add_admin_handler)
    app.add_handler(remove_admin_handler)
    app.add_handler(edit_admin_permissions_handler)
    app.add_handler(admin_settings_handler)

    # GAMES SETTINGS
    app.add_handler(add_game_handler)
    app.add_handler(remove_game_handler)
    app.add_handler(edit_game_handler)
    app.add_handler(games_settings_handler)

    # ITEMS SETTINGS
    app.add_handler(add_item_handler)
    app.add_handler(remove_item_handler)
    app.add_handler(edit_item_handler)
    app.add_handler(items_settings_handler)

    # PAYMENT METHODS SETTINGS
    app.add_handler(add_payment_method_handler)
    app.add_handler(edit_payment_method_handler)
    app.add_handler(remove_payment_method_handler)
    app.add_handler(payment_methods_settings_handler)

    # PAYMENT MEHTODS ADDRESSES SETTINGS
    app.add_handler(add_payment_address_handler)
    app.add_handler(remove_payment_address_handler)
    app.add_handler(manage_payment_addresses_handler)

    # ORDERS SETTINGS
    app.add_handler(orders_settings_handler)
    app.add_handler(show_charging_balance_orders_admin_handler)
    app.add_handler(show_purchase_orders_admin_handler)
    app.add_handler(view_charging_balance_order_admin_handler)
    app.add_handler(view_purchase_order_admin_handler)
    app.add_handler(update_order_status_handler)
    app.add_handler(set_order_status_handler)
    app.add_handler(back_to_order_view_handler)
    app.add_handler(add_order_notes_handler)
    app.add_handler(back_to_admin_charging_balance_orders_handler)
    app.add_handler(back_to_admin_purchase_orders_handler)
    app.add_handler(request_charging_order_handler)
    app.add_handler(request_purchase_order_handler)

    # MANAGE USERS SETTINGS
    app.add_handler(manage_users_settings_handler)
    app.add_handler(export_users_handler)

    # FORCE JOIN CHATS
    app.add_handler(add_force_join_chat_handler)
    app.add_handler(remove_force_join_chat_handler)
    app.add_handler(show_force_join_chats_handler)
    app.add_handler(force_join_chats_settings_handler)

    app.add_handler(broadcast_message_handler)

    app.add_handler(check_joined_handler)

    app.add_handler(ban_unban_user_handler)

    app.add_handler(admin_command)
    app.add_handler(start_command)
    app.add_handler(find_id_handler)
    app.add_handler(hide_ids_keyboard_handler)
    app.add_handler(back_to_user_home_page_handler)
    app.add_handler(back_to_admin_home_page_handler)

    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)
