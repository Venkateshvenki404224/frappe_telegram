"""
Telegram Webhook API Endpoint
Handles incoming webhook requests from Telegram
"""

import frappe
from frappe import _
import json
import logging
from typing import Dict, Any
from frappe_telegram.utils.json_utils import safe_serialize_response

logger = logging.getLogger(__name__)

@frappe.whitelist(allow_guest=True)
def receive_webhook():
    """
    Receive webhook from Telegram
    This endpoint is called by Telegram when a message is received
    """
    try:
        # Get the raw request data
        request_data = frappe.request.get_json()
        
        if not request_data:
            frappe.throw(_("No data received"))
        
        # Log the incoming webhook for debugging
        logger.info(f"Received webhook: {json.dumps(request_data, default=str)}")
        
        # Validate webhook data structure
        if "update_id" not in request_data:
            frappe.throw(_("Invalid webhook data: missing update_id"))
        
        # Process the update
        process_telegram_update(request_data)
        
        # Return success response to Telegram
        return {"ok": True, "result": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        frappe.log_error(f"Telegram Webhook Error: {str(e)}")
        return {"ok": False, "error": str(e)}

def process_telegram_update(update_data: Dict[str, Any]):
    """
    Process a Telegram update
    
    Args:
        update_data: The update data from Telegram
    """
    try:
        # Extract message data
        message = update_data.get("message")
        callback_query = update_data.get("callback_query")
        
        if message:
            process_telegram_message(message)
        elif callback_query:
            process_callback_query(callback_query)
        else:
            logger.warning(f"Unknown update type: {update_data}")
            
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}")
        frappe.log_error(f"Update Processing Error: {str(e)}")

def process_telegram_message(message_data: Dict[str, Any]):
    """
    Process a Telegram message
    
    Args:
        message_data: The message data from Telegram
    """
    try:
        # Extract message details
        message_id = message_data.get("message_id")
        chat_data = message_data.get("chat", {})
        from_user_data = message_data.get("from", {})
        text = message_data.get("text", "")
        date = message_data.get("date")
        
        # Get or create chat record
        chat_doc = get_or_create_chat(chat_data)
        
        # Get or create user record
        user_doc = get_or_create_user(from_user_data)
        
        # Create message record
        message_doc = frappe.get_doc({
            "doctype": "Telegram Message",
            "message_id": str(message_id),
            "chat": chat_doc.name,
            "from_user": user_doc.name if user_doc else None,
            "content": text,
            "status": "Received",
            "message_type": "text",
            "chat_id": str(chat_data.get("id")),
            "received_at": frappe.utils.now_datetime()
        })
        
        message_doc.insert()
        
        # Process commands if message starts with "/"
        if text.startswith("/"):
            process_command(text, message_doc, chat_doc, user_doc)
        
        logger.info(f"Processed message {message_id} from chat {chat_data.get('id')}")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        frappe.log_error(f"Message Processing Error: {str(e)}")

def process_callback_query(callback_data: Dict[str, Any]):
    """
    Process a Telegram callback query
    
    Args:
        callback_data: The callback query data from Telegram
    """
    try:
        # Extract callback details
        callback_id = callback_data.get("id")
        data = callback_data.get("data")
        message = callback_data.get("message", {})
        from_user_data = callback_data.get("from", {})
        
        # Get or create user record
        user_doc = get_or_create_user(from_user_data)
        
        # Process callback data
        if data:
            process_callback_data(data, callback_id, message, user_doc)
        
        logger.info(f"Processed callback query {callback_id}")
        
    except Exception as e:
        logger.error(f"Error processing callback query: {str(e)}")
        frappe.log_error(f"Callback Processing Error: {str(e)}")

def get_or_create_chat(chat_data: Dict[str, Any]):
    """
    Get or create a Telegram Chat record
    
    Args:
        chat_data: Chat data from Telegram
        
    Returns:
        Telegram Chat document
    """
    try:
        chat_id = str(chat_data.get("id"))
        chat_type = chat_data.get("type", "private")
        title = chat_data.get("title", "")
        username = chat_data.get("username", "")
        first_name = chat_data.get("first_name", "")
        last_name = chat_data.get("last_name", "")
        
        # Check if chat already exists
        existing_chat = frappe.db.exists("Telegram Chat", {"chat_id": chat_id})
        
        if existing_chat:
            chat_doc = frappe.get_doc("Telegram Chat", existing_chat)
            # Update chat information
            chat_doc.update({
                "chat_type": chat_type,
                "title": title,
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            })
            chat_doc.save()
        else:
            # Create new chat record
            chat_doc = frappe.get_doc({
                "doctype": "Telegram Chat",
                "chat_id": chat_id,
                "chat_type": chat_type,
                "title": title,
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            })
            chat_doc.insert()
        
        return chat_doc
        
    except Exception as e:
        logger.error(f"Error creating/updating chat: {str(e)}")
        raise

def get_or_create_user(user_data: Dict[str, Any]):
    """
    Get or create a Telegram User record
    
    Args:
        user_data: User data from Telegram
        
    Returns:
        Telegram User document or None
    """
    try:
        if not user_data:
            return None
            
        user_id = str(user_data.get("id"))
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        username = user_data.get("username", "")
        language_code = user_data.get("language_code", "")
        
        # Check if user already exists
        existing_user = frappe.db.exists("Telegram User", {"telegram_user_id": user_id})
        
        if existing_user:
            user_doc = frappe.get_doc("Telegram User", existing_user)
            # Update user information
            user_doc.update({
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "language_code": language_code
            })
            user_doc.save()
        else:
            # Create new user record
            user_doc = frappe.get_doc({
                "doctype": "Telegram User",
                "telegram_user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "language_code": language_code
            })
            user_doc.insert()
        
        return user_doc
        
    except Exception as e:
        logger.error(f"Error creating/updating user: {str(e)}")
        return None

def process_command(command: str, message_doc, chat_doc, user_doc):
    """
    Process a Telegram command
    
    Args:
        command: The command text (e.g., "/start")
        message_doc: Telegram Message document
        chat_doc: Telegram Chat document
        user_doc: Telegram User document
    """
    try:
        # Extract command and arguments
        parts = command.split(" ", 1)
        command_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Get command handlers from hooks
        command_handlers = frappe.get_hooks("telegram_command_handlers", {})
        
        # Find handler for this command
        handler_method = command_handlers.get(command_name)
        
        if handler_method:
            # Call the handler method
            frappe.call(
                handler_method,
                command=command_name,
                args=args,
                message_doc=message_doc.name,
                chat_doc=chat_doc.name,
                user_doc=user_doc.name if user_doc else None
            )
        else:
            # Default command handling
            handle_default_command(command_name, args, message_doc, chat_doc, user_doc)
            
    except Exception as e:
        logger.error(f"Error processing command {command}: {str(e)}")
        frappe.log_error(f"Command Processing Error: {str(e)}")

def handle_default_command(command: str, args: str, message_doc, chat_doc, user_doc):
    """
    Handle default commands
    
    Args:
        command: Command name
        args: Command arguments
        message_doc: Telegram Message document
        chat_doc: Telegram Chat document
        user_doc: Telegram User document
    """
    try:
        if command == "/start":
            # Send welcome message
            welcome_message = _("Welcome! I'm your Telegram bot assistant. How can I help you today?")
            send_response_message(welcome_message, chat_doc.chat_id)
            
        elif command == "/help":
            # Send help message
            help_message = _("""
Available commands:
/start - Start the bot
/help - Show this help message
/status - Check bot status
            """).strip()
            send_response_message(help_message, chat_doc.chat_id)
            
        elif command == "/status":
            # Send status message
            status_message = _("Bot is running and ready to help!")
            send_response_message(status_message, chat_doc.chat_id)
            
        else:
            # Unknown command
            unknown_message = _("Unknown command. Type /help for available commands.")
            send_response_message(unknown_message, chat_doc.chat_id)
            
    except Exception as e:
        logger.error(f"Error in default command handler: {str(e)}")

def process_callback_data(data: str, callback_id: str, message: Dict[str, Any], user_doc):
    """
    Process callback query data
    
    Args:
        data: Callback data
        callback_id: Callback query ID
        message: Original message
        user_doc: Telegram User document
    """
    try:
        # Get callback handlers from hooks
        callback_handlers = frappe.get_hooks("telegram_callback_handlers", {})
        
        # Find handler for this callback
        handler_method = callback_handlers.get(data)
        
        if handler_method:
            # Call the handler method
            frappe.call(
                handler_method,
                data=data,
                callback_id=callback_id,
                message=message,
                user_doc=user_doc.name if user_doc else None
            )
        else:
            # Default callback handling
            handle_default_callback(data, callback_id, message, user_doc)
            
    except Exception as e:
        logger.error(f"Error processing callback data {data}: {str(e)}")
        frappe.log_error(f"Callback Processing Error: {str(e)}")

def handle_default_callback(data: str, callback_id: str, message: Dict[str, Any], user_doc):
    """
    Handle default callback queries
    
    Args:
        data: Callback data
        callback_id: Callback query ID
        message: Original message
        user_doc: Telegram User document
    """
    try:
        # Default callback response
        response_message = _("Callback received: {0}").format(data)
        send_response_message(response_message, message.get("chat", {}).get("id"))
        
    except Exception as e:
        logger.error(f"Error in default callback handler: {str(e)}")

def send_response_message(text: str, chat_id: str, bot_name: str = None):
    """
    Send a response message to a chat
    
    Args:
        text: Message text
        chat_id: Target chat ID
        bot_name: Bot name to use (optional)
    """
    try:
        from frappe_telegram.client import send_message
        
        # Get active bot for this environment
        if not bot_name:
            active_bots = frappe.db.sql("""
                SELECT name FROM `tabTelegram Bot` 
                WHERE is_active = 1 
                ORDER BY environment = 'Production' DESC, creation DESC
                LIMIT 1
            """)
            
            if active_bots:
                bot_name = active_bots[0][0]
            else:
                logger.error("No active bot found for sending response")
                return
        
        # Send message using queue system
        send_message(
            message_text=text,
            chat_id=chat_id,
            from_bot=bot_name,
            use_queue=True
        )
        
    except Exception as e:
        logger.error(f"Error sending response message: {str(e)}")
        frappe.log_error(f"Response Message Error: {str(e)}")

@frappe.whitelist()
def get_webhook_status():
    """
    Get webhook status for all bots
    
    Returns:
        Dict containing webhook status for each bot
    """
    try:
        bots = frappe.get_all("Telegram Bot", fields=["name", "title", "environment", "webhook_status"])
        return {"bots": bots}
    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}")
        return {"error": str(e)} 