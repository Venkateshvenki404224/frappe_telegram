"""
Start command handler for Telegram bot
"""

import frappe
from frappe import _

@frappe.whitelist()
def start_command(command, args, message_doc, chat_doc, user_doc):
    """
    Handle /start command
    
    Args:
        command: Command name ("/start")
        args: Command arguments
        message_doc: Telegram Message document name
        chat_doc: Telegram Chat document name
        user_doc: Telegram User document name
    """
    try:
        # Get chat document
        chat = frappe.get_doc("Telegram Chat", chat_doc)
        
        # Create welcome message
        welcome_message = _("""
🎉 Welcome to the Telegram Bot!

I'm here to help you with various tasks. Here are some things I can do:

📋 **Available Commands:**
/start - Show this welcome message
/help - Show help and available commands
/status - Check bot status and health

💡 **Features:**
• Send and receive messages
• Process commands automatically
• Queue-based message handling
• Multi-environment support

Need help? Just type /help for more information!
        """).strip()
        
        # Send welcome message
        from frappe_telegram.api import send_response_message
        send_response_message(welcome_message, chat.chat_id)
        
        # Log the start command
        frappe.logger().info(f"User {user_doc} started the bot in chat {chat_doc}")
        
    except Exception as e:
        frappe.log_error(f"Start command error: {str(e)}")
        # Send error message
        error_message = _("Sorry, there was an error processing your request. Please try again.")
        from frappe_telegram.api import send_response_message
        send_response_message(error_message, chat.chat_id) 