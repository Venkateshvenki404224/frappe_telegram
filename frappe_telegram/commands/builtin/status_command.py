"""
Status command handler for Telegram bot
"""

import frappe
from frappe import _

@frappe.whitelist()
def status_command(command, args, message_doc, chat_doc, user_doc):
    """
    Handle /status command
    
    Args:
        command: Command name ("/status")
        args: Command arguments
        message_doc: Telegram Message document name
        chat_doc: Telegram Chat document name
        user_doc: Telegram User document name
    """
    try:
        # Get chat document
        chat = frappe.get_doc("Telegram Chat", chat_doc)
        
        # Get system status
        status_info = get_system_status()
        
        # Create status message
        status_message = _("""
🤖 **Bot Status Report**

✅ **Bot Status:** {bot_status}
🌍 **Environment:** {environment}
📊 **Queue Health:** {queue_health}

📈 **Message Statistics (Last 24h):**
• Queued: {queued_count}
• Processing: {processing_count}
• Sent: {sent_count}
• Failed: {failed_count}

🔧 **System Information:**
• Active Bots: {active_bots}
• Webhook Status: {webhook_status}
• Queue Status: {queue_status}

🕒 **Last Updated:** {timestamp}
        """).format(**status_info)
        
        # Send status message
        from frappe_telegram.api import send_response_message
        send_response_message(status_message, chat.chat_id)
        
        # Log the status command
        frappe.logger().info(f"User {user_doc} requested status in chat {chat_doc}")
        
    except Exception as e:
        frappe.log_error(f"Status command error: {str(e)}")
        # Send error message
        error_message = _("Sorry, there was an error getting system status. Please try again.")
        from frappe_telegram.api import send_response_message
        send_response_message(error_message, chat.chat_id)

def get_system_status():
    """
    Get comprehensive system status
    
    Returns:
        Dict containing system status information
    """
    try:
        from frappe_telegram.utils.message_queue import get_queue_stats
        
        # Get queue statistics
        queue_stats = get_queue_stats()
        
        # Get active bots
        active_bots = frappe.db.sql("""
            SELECT name, environment, webhook_status
            FROM `tabTelegram Bot`
            WHERE is_active = 1
        """, as_dict=True)
        
        # Get message statistics for last 24 hours
        message_stats = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count
            FROM `tabTelegram Message`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY status
        """, as_dict=True)
        
        # Convert to dict for easy access
        stats_dict = {stat['status']: stat['count'] for stat in message_stats}
        
        # Determine bot status
        bot_status = "🟢 Online" if active_bots else "🔴 Offline"
        environment = active_bots[0]['environment'] if active_bots else "Unknown"
        webhook_status = active_bots[0]['webhook_status'] if active_bots else "Unknown"
        
        # Determine queue health
        queue_health = "🟢 Healthy"
        if queue_stats.get('queue_health', {}).get('stuck_messages', 0) > 0:
            queue_health = "🟡 Warning"
        if queue_stats.get('queue_health', {}).get('recent_failures', 0) > 10:
            queue_health = "🔴 Unhealthy"
        
        return {
            "bot_status": bot_status,
            "environment": environment,
            "queue_health": queue_health,
            "queued_count": stats_dict.get('Queued', 0),
            "processing_count": stats_dict.get('Processing', 0),
            "sent_count": stats_dict.get('Sent', 0),
            "failed_count": stats_dict.get('Failed', 0),
            "active_bots": len(active_bots),
            "webhook_status": webhook_status,
            "queue_status": "🟢 Running" if queue_stats.get('queue_health', {}).get('is_healthy', True) else "🔴 Issues",
            "timestamp": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting system status: {str(e)}")
        return {
            "bot_status": "🔴 Error",
            "environment": "Unknown",
            "queue_health": "🔴 Error",
            "queued_count": 0,
            "processing_count": 0,
            "sent_count": 0,
            "failed_count": 0,
            "active_bots": 0,
            "webhook_status": "Unknown",
            "queue_status": "🔴 Error",
            "timestamp": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        } 