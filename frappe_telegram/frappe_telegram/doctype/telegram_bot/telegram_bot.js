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