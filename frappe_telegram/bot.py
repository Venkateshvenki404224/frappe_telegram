from typing import Union
from telegram.ext import Application


import frappe
from frappe_telegram.frappe_telegram.doctype import TelegramBot
from telegram.ext import MessageHandler


def start_polling(site: str, telegram_bot: Union[str, TelegramBot], poll_interval: int = 0):
    application = get_bot(telegram_bot=telegram_bot, site=site)

    application.run_polling(poll_interval=poll_interval)


def start_webhook(
        site: str,
        telegram_bot: Union[str, TelegramBot],
        listen_host: str = "127.0.0.1",
        webhook_port: int = 80,
        webhook_url: str = None):
    application = get_bot(telegram_bot=telegram_bot, site=site)
    application.run_webhook(
        listen=listen_host,
        port=webhook_port,
        webhook_url=webhook_url
    )


def get_bot(telegram_bot: Union[str, TelegramBot], site=None) -> Application:
    if not site:
        site = frappe.local.site

    from contextlib import ExitStack

    with frappe.init_site(site) if not frappe.db else ExitStack():
        if not frappe.db:
            frappe.connect()

        if isinstance(telegram_bot, str):
            telegram_bot = frappe.get_doc("Telegram Bot", telegram_bot)

        application = make_bot(telegram_bot=telegram_bot, site=site)

        handlers = frappe.get_hooks("telegram_bot_handler")
        if isinstance(handlers, dict):
            handlers = handlers[telegram_bot.name]
        for cmd in handlers:
            frappe.get_attr(cmd)(telegram_bot=telegram_bot, application=application)

        attach_update_processors(application=application)

    return application


def make_bot(telegram_bot: TelegramBot, site: str) -> Application:
    """
    Returns a custom TelegramApplication with FrappeTelegramDispatcher
    """
    from .utils.overrides import FrappeTelegramApplication

    application = FrappeTelegramApplication.make(
        site=site, 
        telegram_bot=telegram_bot.name, 
        token=telegram_bot.get_password("api_token")
    )
    application.initialize()

    return application


def attach_update_processors(application: Application):
    pre_process_group = -1000
    post_process_group = 1000

    for cmd in frappe.get_hooks("telegram_update_pre_processors"):
        application.add_handler(MessageHandler(None, frappe.get_attr(cmd)), group=pre_process_group)
        pre_process_group += 1

    for cmd in frappe.get_hooks("telegram_update_post_processors"):
        application.add_handler(MessageHandler(None, frappe.get_attr(cmd)), group=post_process_group)
        post_process_group += 1
