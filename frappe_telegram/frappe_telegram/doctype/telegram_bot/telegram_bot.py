import frappe
from frappe.model.document import Document
from frappe_telegram.frappe_telegram.doctype.telegram_bot import DEFAULT_TELEGRAM_BOT_KEY
import requests
from frappe_telegram.utils.json_utils import safe_serialize_response
from frappe import _


class TelegramBot(Document):
    def autoname(self):
        self.name = self.title.replace(" ", "-")

    def validate(self):
        self.validate_api_token()
        self.set_nginx_path()

    def on_update(self):
        # Set username automatically when bot token changes
        if self.has_value_changed("bot_token"):
            self.set_username()

    def set_username(self):
        """Fetch and set bot username from Telegram API"""
        if not self.bot_token:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    new_username = bot_info.get('result', {}).get('username')
                    if new_username and new_username != self.username:
                        self.username = new_username
                        # Save without triggering on_update again
                        frappe.db.set_value(self.doctype, self.name, 'username', new_username)
                        frappe.msgprint(_(f"Bot username updated to: {new_username}"))
                    elif new_username:
                        frappe.msgprint(_("Bot username is already up to date"))
                    else:
                        frappe.throw(_("Could not retrieve username from Telegram API"))
                else:
                    frappe.throw(_("Failed to get bot information from Telegram API"))
            else:
                frappe.throw(_("Failed to connect to Telegram API"))
                
        except requests.RequestException as e:
            frappe.throw(_(f"Connection error: {str(e)}"))
        except Exception as e:
            frappe.throw(_(f"Error setting username: {str(e)}"))

    def after_insert(self):
        default_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)   
        if not default_bot:
            self.mark_as_default()

    def after_delete(self):
        default_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)

        if default_bot == self.name:
            new_default_bot = frappe.get_value("Telegram Bot", {})
            frappe.db.set_default(DEFAULT_TELEGRAM_BOT_KEY, new_default_bot)

            if new_default_bot:
                frappe.msgprint(
                    frappe._(f"Set {new_default_bot} as the default bot for notifications.")
                )

    def set_nginx_path(self):
        if self.webhook_nginx_path:
            return

        if not self.webhook_url:
            return

        self.webhook_nginx_path = "/" + self.webhook_url.rstrip("/").split("/")[-1]

    @frappe.whitelist()
    def mark_as_default(self):
        frappe.db.set_default(DEFAULT_TELEGRAM_BOT_KEY, self.name)
        frappe.msgprint(frappe._(f"Set {self.get('title')} as the default bot for notifications."))

    def validate_api_token(self):
        if not self.is_new() and not self.has_value_changed("api_token"):
            return

        # Basic token format validation (should be like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
        token_parts = self.bot_token.split(':')
        if len(token_parts) != 2:
            frappe.throw(_("Invalid bot token format. Token should be in format 'bot_id:auth_token'"))
        
        bot_id, auth_token = token_parts
        # Validate bot_id format without converting to integer to avoid overflow
        if not bot_id.isdigit() or len(bot_id) < 3 or len(auth_token) < 35:
            frappe.throw(_("Invalid bot token format"))

    @frappe.whitelist()
    def test_bot_connection(self):
        """Test bot connectivity with Telegram API"""
        if not self.bot_token:
            frappe.throw(_("Bot token is required"))
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            print(response.text)
            
            if response.status_code == 200:
                bot_info = response.json()
                print(bot_info)
                if bot_info.get('ok'):
                    # Convert large integers to strings to prevent serialization errors
                    safe_bot_info = safe_serialize_response(bot_info.get('result', {}))
                    return {
                        'success': True,
                        'message': _("Bot connection successful"),
                        'bot_info': safe_bot_info
                    }
            
            return safe_serialize_response({
                'success': False,
                'message': _("Failed to connect to Telegram API"),
                'error': response.text
            })
        
        except requests.RequestException as e:
            return safe_serialize_response({
                'success': False,
                'message': _("Connection error"),
                'error': str(e)
            })

    @frappe.whitelist()
    def refresh_username(self):
        """Manually refresh bot username from Telegram API"""
        if not self.bot_token:
            frappe.throw(_("Bot token is required to refresh username"))
        
        try:
            self.set_username()
            return {
                'success': True,
                'message': _("Username refreshed successfully")
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
