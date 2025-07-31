"""
Message Queue System for Telegram Bot Integration
Handles message processing with status tracking and retry logic
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_url
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MessageQueueManager:
    """Manages message queue operations with efficient database handling"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 300  # 5 minutes
    
    def enqueue_message(self, message_data: Dict[str, Any], bot_name: str) -> str:
        """
        Add message to queue for processing
        
        Args:
            message_data: Message content and metadata
            bot_name: Name of the bot to send from
            
        Returns:
            str: Message ID
        """
        try:
            # Create message record with queued status
            message_doc = frappe.get_doc({
                "doctype": "Telegram Message",
                "content": message_data.get("text", ""),
                "from_bot": bot_name,
                "status": "Queued",
                "queued_at": now_datetime(),
                "retry_count": 0,
                "message_type": message_data.get("type", "text"),
                "chat_id": message_data.get("chat_id"),
                "parse_mode": message_data.get("parse_mode"),
                "reply_to_message_id": message_data.get("reply_to_message_id"),
                "disable_web_page_preview": message_data.get("disable_web_page_preview", False),
                "disable_notification": message_data.get("disable_notification", False),
                "protect_content": message_data.get("protect_content", False)
            })
            
            message_doc.insert()
            
            # Enqueue background job for processing
            frappe.enqueue(
                "frappe_telegram.utils.message_queue.process_message",
                message_id=message_doc.name,
                queue="telegram_messages",
                timeout=300
            )
            
            logger.info(f"Message {message_doc.name} queued for processing")
            return message_doc.name
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {str(e)}")
            frappe.log_error(f"Message Queue Error: {str(e)}")
            raise
    
    def process_message(self, message_id: str) -> bool:
        """
        Process a queued message
        
        Args:
            message_id: ID of the message to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message_doc = frappe.get_doc("Telegram Message", message_id)
            
            if message_doc.status != "Queued":
                logger.warning(f"Message {message_id} is not in queued status: {message_doc.status}")
                return False
            
            # Update status to processing
            frappe.db.set_value("Telegram Message", message_id, "status", "Processing")
            frappe.db.set_value("Telegram Message", message_id, "processing_at", now_datetime())
            
            # Get bot configuration
            bot_doc = frappe.get_doc("Telegram Bot", message_doc.from_bot)
            
            # Send message via Telegram API
            success = self._send_telegram_message(message_doc, bot_doc)
            
            if success:
                # Update status to sent
                frappe.db.set_value("Telegram Message", message_id, "status", "Sent")
                frappe.db.set_value("Telegram Message", message_id, "sent_at", now_datetime())
                logger.info(f"Message {message_id} sent successfully")
                return True
            else:
                # Handle failure
                self._handle_message_failure(message_doc)
                return False
                
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {str(e)}")
            frappe.log_error(f"Message Processing Error: {str(e)}")
            self._handle_message_failure(frappe.get_doc("Telegram Message", message_id))
            return False
    
    def _send_telegram_message(self, message_doc, bot_doc) -> bool:
        """
        Send message via Telegram API
        
        Args:
            message_doc: Telegram Message document
            bot_doc: Telegram Bot document
            
        Returns:
            bool: True if successful
        """
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{bot_doc.get_password('bot_token')}/sendMessage"
            
            payload = {
                "chat_id": message_doc.chat_id,
                "text": message_doc.content,
                "parse_mode": message_doc.parse_mode or "HTML"
            }
            
            # Add optional parameters
            if message_doc.reply_to_message_id:
                payload["reply_to_message_id"] = message_doc.reply_to_message_id
            
            if message_doc.disable_web_page_preview:
                payload["disable_web_page_preview"] = True
            
            if message_doc.disable_notification:
                payload["disable_notification"] = True
            
            if message_doc.protect_content:
                payload["protect_content"] = True
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    # Store Telegram message ID
                    telegram_message_id = result["result"]["message_id"]
                    frappe.db.set_value("Telegram Message", message_doc.name, "message_id", telegram_message_id)
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description')}")
                    return False
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    def _handle_message_failure(self, message_doc):
        """
        Handle failed message processing
        
        Args:
            message_doc: Telegram Message document
        """
        current_retry_count = message_doc.retry_count or 0
        
        if current_retry_count < self.max_retries:
            # Schedule retry
            next_retry_time = now_datetime() + timedelta(seconds=self.retry_delay * (current_retry_count + 1))
            
            frappe.db.set_value("Telegram Message", message_doc.name, "status", "Failed")
            frappe.db.set_value("Telegram Message", message_doc.name, "failed_at", now_datetime())
            frappe.db.set_value("Telegram Message", message_doc.name, "retry_count", current_retry_count + 1)
            frappe.db.set_value("Telegram Message", message_doc.name, "next_retry_at", next_retry_time)
            
            # Schedule retry job
            frappe.enqueue(
                "frappe_telegram.utils.message_queue.process_message",
                message_id=message_doc.name,
                queue="telegram_messages",
                timeout=300,
                at=next_retry_time
            )
            
            logger.info(f"Message {message_doc.name} scheduled for retry {current_retry_count + 1}/{self.max_retries}")
        else:
            # Max retries exceeded
            frappe.db.set_value("Telegram Message", message_doc.name, "status", "Failed")
            frappe.db.set_value("Telegram Message", message_doc.name, "failed_at", now_datetime())
            frappe.db.set_value("Telegram Message", message_doc.name, "retry_count", current_retry_count)
            
            logger.error(f"Message {message_doc.name} failed after {self.max_retries} retries")
            
            # Notify administrators
            self._notify_failure(message_doc)
    
    def _notify_failure(self, message_doc):
        """
        Notify administrators of message failure
        
        Args:
            message_doc: Telegram Message document
        """
        try:
            # Send notification to system managers
            frappe.sendmail(
                recipients=[user.name for user in frappe.get_all("User", filters={"role_profile_name": "System Manager"})],
                subject=f"Telegram Message Failed: {message_doc.name}",
                message=f"""
                A Telegram message has failed after maximum retries.
                
                Message ID: {message_doc.name}
                Bot: {message_doc.from_bot}
                Content: {message_doc.content[:100]}...
                Failed At: {message_doc.failed_at}
                Retry Count: {message_doc.retry_count}
                
                Please check the message and bot configuration.
                """
            )
        except Exception as e:
            logger.error(f"Failed to send failure notification: {str(e)}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics for monitoring
        
        Returns:
            Dict containing queue statistics
        """
        try:
            # Use efficient SQL queries for statistics
            stats = frappe.db.sql("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    MIN(creation) as oldest,
                    MAX(creation) as newest
                FROM `tabTelegram Message`
                WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY status
            """, as_dict=True)
            
            # Get active bots
            active_bots = frappe.db.sql("""
                SELECT name, environment, is_active
                FROM `tabTelegram Bot`
                WHERE is_active = 1
            """, as_dict=True)
            
            return {
                "message_stats": stats,
                "active_bots": active_bots,
                "queue_health": self._check_queue_health()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {"error": str(e)}
    
    def _check_queue_health(self) -> Dict[str, Any]:
        """
        Check queue health metrics
        
        Returns:
            Dict containing health metrics
        """
        try:
            # Check for stuck messages (processing for too long)
            stuck_messages = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabTelegram Message`
                WHERE status = 'Processing'
                AND processing_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE)
            """)[0][0]
            
            # Check for failed messages in last hour
            recent_failures = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabTelegram Message`
                WHERE status = 'Failed'
                AND failed_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)[0][0]
            
            return {
                "stuck_messages": stuck_messages,
                "recent_failures": recent_failures,
                "is_healthy": stuck_messages == 0 and recent_failures < 10
            }
            
        except Exception as e:
            logger.error(f"Error checking queue health: {str(e)}")
            return {"error": str(e)}

# Global instance
message_queue = MessageQueueManager()

# Background job functions
@frappe.whitelist()
def process_message(message_id: str) -> bool:
    """Background job function to process a message"""
    return message_queue.process_message(message_id)

@frappe.whitelist()
def get_queue_stats() -> Dict[str, Any]:
    """Get queue statistics"""
    return message_queue.get_queue_stats() 