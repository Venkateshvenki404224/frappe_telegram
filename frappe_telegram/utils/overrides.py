import frappe
from telegram.ext import Application, Bot
from frappe_telegram.handlers.logging import log_outgoing_message


"""
For each incoming Update, we will have frappe initialized.
We will override Application and Bot instance
- Application is overridden for initializing frappe for each incoming Update
- Bot is overridden for logging outgoing messages
"""


class FrappeTelegramBot(Bot):

    # The name of the active FrappeTelegramBot
    telegram_bot: str

    @classmethod
    def make(cls, telegram_bot: str, token: str):
        new_bot = cls(token)
        new_bot.telegram_bot = telegram_bot
        return new_bot

    def _message(self, *args, **kwargs):
        result = super()._message(*args, **kwargs)
        log_outgoing_message(self.telegram_bot, result)
        return result


class FrappeTelegramApplication(Application):

    # The Frappe Site
    site: str

    @classmethod
    def make(cls, site: str, telegram_bot: str, token: str):
        bot = FrappeTelegramBot.make(telegram_bot=telegram_bot, token=token)
        application = cls.builder().token(token).bot(bot).build()
        application.site = site
        print("Using Patched Frappe Telegram Application ✅")
        return application

    def process_update(self, update: object) -> None:
        try:
            frappe.init(site=self.site)
            frappe.flags.in_telegram_update = True
            frappe.connect()
            super().process_update(update=update)
        except BaseException:
            frappe.log_error(title="Telegram Process Update Error", message=frappe.get_traceback())
        finally:
            frappe.db.commit()
            frappe.destroy()
