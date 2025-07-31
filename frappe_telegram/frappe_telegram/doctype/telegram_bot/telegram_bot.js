// Copyright (c) 2021, Leam Technology Systems and contributors
// For license information, please see license.txt

frappe.ui.form.on('Telegram Bot', {
	refresh: function(frm) {
		frm.add_custom_button(__('Test Connection'), function() {
            test_bot_connection(frm);
        }, __('Bot Actions'));
        
        frm.add_custom_button(__('Mark as Default'), function() {
            mark_as_default(frm);
        }, __('Bot Actions'));
        
        frm.add_custom_button(__('Refresh Username'), function() {
            refresh_username(frm);
        }, __('Bot Actions'));

        // Environment management buttons
        if (frm.doc.environment) {
            if (frm.doc.is_active) {
                frm.add_custom_button(__('Deactivate Bot'), function() {
                    deactivate_bot(frm);
                }, __('Environment Management'));
            } else {
                frm.add_custom_button(__('Activate Bot'), function() {
                    activate_bot(frm);
                }, __('Environment Management'));
            }
        }

        // Webhook management
        setup_webhook_management(frm);
	}
});

// Bot connection test
function test_bot_connection(frm) {
    if (!frm.doc.bot_token) {
        frappe.msgprint(__('Please enter a bot token first'));
        return;
    }

    frappe.call({
        method: 'test_bot_connection',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                const bot_info = r.message.bot_info;
                // Handle large integer bot ID safely
                const bot_id = typeof bot_info.id === 'number' ? bot_info.id.toString() : bot_info.id;
                
                frappe.msgprint({
                    title: __('Connection Successful'),
                    message: `Bot Name: ${bot_info.first_name || 'N/A'}<br>
                             Username: @${bot_info.username || 'N/A'}<br>
                             Bot ID: ${bot_id}<br>
                             Can Join Groups: ${bot_info.can_join_groups || false}<br>
                             Can Read All Group Messages: ${bot_info.can_read_all_group_messages || false}`,
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Connection Failed'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

// Mark as default
function mark_as_default(frm) {
    frappe.call({
        method: 'mark_as_default',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message,
                    indicator: 'green'
                });
            }
        }
    });
}

// Refresh username
function refresh_username(frm) {
    if (!frm.doc.bot_token) {
        frappe.msgprint(__('Please enter a bot token first'));
        return;
    }

    frappe.call({
        method: 'refresh_username',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
                // Refresh the form to show updated username
                frm.refresh();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

// Environment management functions
function activate_bot(frm) {
    frappe.call({
        method: 'activate_bot',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
                frm.refresh();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function deactivate_bot(frm) {
    frappe.call({
        method: 'deactivate_bot',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
                frm.refresh();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

// Webhook management
function setup_webhook_management(frm) {
    // Get webhook info on form load
    if (frm.doc.bot_token) {
        get_webhook_info(frm);
    }

    // Create webhook action buttons
    const webhookActionsHtml = `
        <div class="webhook-actions">
            <button class="btn btn-sm btn-primary" onclick="register_webhook('${frm.doc.name}')">
                ${__('Register Webhook')}
            </button>
            <button class="btn btn-sm btn-warning" onclick="unregister_webhook('${frm.doc.name}')">
                ${__('Unregister Webhook')}
            </button>
            <button class="btn btn-sm btn-info" onclick="get_webhook_info('${frm.doc.name}')">
                ${__('Refresh Status')}
            </button>
        </div>
    `;

    // Set the webhook actions HTML
    if (frm.get_field('webhook_actions')) {
        frm.set_value('webhook_actions', webhookActionsHtml);
    }
}

function register_webhook(bot_name) {
    frappe.call({
        method: 'frappe_telegram.frappe_telegram.doctype.telegram_bot.telegram_bot.register_webhook',
        args: { name: bot_name },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
                // Refresh webhook status
                get_webhook_info(bot_name);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function unregister_webhook(bot_name) {
    frappe.call({
        method: 'frappe_telegram.frappe_telegram.doctype.telegram_bot.telegram_bot.unregister_webhook',
        args: { name: bot_name },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
                // Refresh webhook status
                get_webhook_info(bot_name);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

function get_webhook_info(bot_name) {
    frappe.call({
        method: 'frappe_telegram.frappe_telegram.doctype.telegram_bot.telegram_bot.get_webhook_info',
        args: { name: bot_name },
        callback: function(r) {
            if (r.message && r.message.success) {
                const webhook_info = r.message.webhook_info;
                const status = r.message.status;
                
                // Update webhook status field
                const frm = frappe.get_form('Telegram Bot', bot_name);
                if (frm && frm.get_field('webhook_status')) {
                    frm.set_value('webhook_status', status);
                }
                
                // Show detailed webhook info
                if (webhook_info.url) {
                    frappe.msgprint({
                        title: __('Webhook Status'),
                        message: `Status: ${status}<br>
                                 URL: ${webhook_info.url}<br>
                                 Has Custom Certificate: ${webhook_info.has_custom_certificate || false}<br>
                                 Pending Update Count: ${webhook_info.pending_update_count || 0}`,
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Webhook Status'),
                        message: `Status: ${status}<br>No webhook is currently set.`,
                        indicator: 'orange'
                    });
                }
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message ? r.message.message : __('Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}