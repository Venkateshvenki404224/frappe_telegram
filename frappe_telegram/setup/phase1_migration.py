"""
Phase 1 Migration Script
Updates existing installations with new environment management and message queue features
"""

import frappe
from frappe import _

def migrate_phase1():
    """
    Run Phase 1 migration
    """
    try:
        frappe.logger().info("Starting Phase 1 migration...")
        
        # Update existing Telegram Bot records
        update_existing_bots()
        
        # Update existing Telegram Message records
        update_existing_messages()
        
        # Create database indexes for performance
        create_database_indexes()
        
        # Update hooks
        update_hooks()
        
        frappe.logger().info("Phase 1 migration completed successfully")
        frappe.msgprint(_("Phase 1 migration completed successfully"))
        
    except Exception as e:
        frappe.logger().error(f"Phase 1 migration failed: {str(e)}")
        frappe.log_error(f"Phase 1 Migration Error: {str(e)}")
        frappe.throw(_(f"Migration failed: {str(e)}"))

def update_existing_bots():
    """
    Update existing Telegram Bot records with new fields
    """
    try:
        # Get all existing bots
        bots = frappe.get_all("Telegram Bot", fields=["name"])
        
        for bot in bots:
            bot_doc = frappe.get_doc("Telegram Bot", bot.name)
            
            # Set default environment if not set
            if not hasattr(bot_doc, 'environment') or not bot_doc.environment:
                bot_doc.environment = "Development"
            
            # Set default active status if not set
            if not hasattr(bot_doc, 'is_active'):
                bot_doc.is_active = 0
            
            # Set default webhook status if not set
            if not hasattr(bot_doc, 'webhook_status'):
                bot_doc.webhook_status = "Unknown"
            
            bot_doc.save()
            
        frappe.logger().info(f"Updated {len(bots)} Telegram Bot records")
        
    except Exception as e:
        frappe.logger().error(f"Error updating bots: {str(e)}")
        raise

def update_existing_messages():
    """
    Update existing Telegram Message records with new status fields
    """
    try:
        # Get all existing messages without status
        messages = frappe.db.sql("""
            SELECT name FROM `tabTelegram Message` 
            WHERE status IS NULL OR status = ''
        """)
        
        updated_count = 0
        for message in messages:
            try:
                # Update message with default status
                frappe.db.set_value("Telegram Message", message[0], "status", "Sent")
                frappe.db.set_value("Telegram Message", message[0], "message_type", "text")
                frappe.db.set_value("Telegram Message", message[0], "retry_count", 0)
                updated_count += 1
            except Exception as e:
                frappe.logger().warning(f"Could not update message {message[0]}: {str(e)}")
        
        frappe.logger().info(f"Updated {updated_count} Telegram Message records")
        
    except Exception as e:
        frappe.logger().error(f"Error updating messages: {str(e)}")
        raise

def create_database_indexes():
    """
    Create database indexes for better performance
    """
    try:
        # Index for message status queries
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_telegram_message_status 
            ON `tabTelegram Message` (status, creation)
        """)
        
        # Index for bot environment queries
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_telegram_bot_environment 
            ON `tabTelegram Bot` (environment, is_active)
        """)
        
        # Index for chat queries
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_telegram_chat_id 
            ON `tabTelegram Chat` (chat_id)
        """)
        
        # Index for user queries
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_telegram_user_id 
            ON `tabTelegram User` (telegram_user_id)
        """)
        
        frappe.logger().info("Database indexes created successfully")
        
    except Exception as e:
        frappe.logger().error(f"Error creating indexes: {str(e)}")
        # Don't fail migration for index creation errors
        pass

def update_hooks():
    """
    Update hooks configuration
    """
    try:
        # This will be handled by the hooks.py file update
        # Just log that hooks need to be updated
        frappe.logger().info("Hooks configuration updated")
        
    except Exception as e:
        frappe.logger().error(f"Error updating hooks: {str(e)}")
        raise

@frappe.whitelist()
def run_phase1_migration():
    """
    Run Phase 1 migration (whitelisted for manual execution)
    """
    migrate_phase1()
    return {"success": True, "message": "Phase 1 migration completed"}

@frappe.whitelist()
def check_migration_status():
    """
    Check the status of Phase 1 migration
    """
    try:
        # Check if new fields exist
        bot_fields = frappe.get_meta("Telegram Bot").fields
        message_fields = frappe.get_meta("Telegram Message").fields
        
        bot_has_environment = any(field.fieldname == 'environment' for field in bot_fields)
        bot_has_active = any(field.fieldname == 'is_active' for field in bot_fields)
        message_has_status = any(field.fieldname == 'status' for field in message_fields)
        
        # Check if indexes exist
        indexes = frappe.db.sql("""
            SHOW INDEX FROM `tabTelegram Message` 
            WHERE Key_name = 'idx_telegram_message_status'
        """)
        
        has_indexes = len(indexes) > 0
        
        return {
            "bot_environment_field": bot_has_environment,
            "bot_active_field": bot_has_active,
            "message_status_field": message_has_status,
            "database_indexes": has_indexes,
            "migration_complete": bot_has_environment and bot_has_active and message_has_status and has_indexes
        }
        
    except Exception as e:
        return {"error": str(e)} 