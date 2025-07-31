"""
Help command handler for Telegram bot
"""

import frappe
from frappe import _

@frappe.whitelist()
def help_command(command, args, message_doc, chat_doc, user_doc):
    """
    Handle /help command
    
    Args:
        command: Command name ("/help")
        args: Command arguments
        message_doc: Telegram Message document name
        chat_doc: Telegram Chat document name
        user_doc: Telegram User document name
    """
    try:
        # Get chat document
        chat = frappe.get_doc("Telegram Chat", chat_doc)
        
        # Create help message
        help_message = _("""
📚 **Telegram Bot Help**

🤖 **Available Commands:**

**Basic Commands:**
/start - Start the bot and show welcome message
/help - Show this help message
/status - Check bot status and system health

**System Information:**
• Bot is running on Frappe Framework
• Messages are processed through a queue system
• Supports multiple environments (Development/Production)
• Automatic retry mechanism for failed messages

**Features:**
• Real-time message processing
• Command handling with custom responses
• Message status tracking (Queued, Processing, Sent, Failed)
• Webhook-based communication with Telegram

**Need Support?**
If you encounter any issues, please contact the system administrator.

For more information about specific features, type the command name.
        """).strip()
        
        # Send help message
        from frappe_telegram.api import send_response_message
        send_response_message(help_message, chat.chat_id)
        
        # Log the help command
        frappe.logger().info(f"User {user_doc} requested help in chat {chat_doc}")
        
    except Exception as e:
        frappe.log_error(f"Help command error: {str(e)}")
        # Send error message
        error_message = _("Sorry, there was an error processing your request. Please try again.")
        from frappe_telegram.api import send_response_message
        send_response_message(error_message, chat.chat_id) 