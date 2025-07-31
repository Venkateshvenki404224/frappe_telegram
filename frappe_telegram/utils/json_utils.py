# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

"""
JSON utility functions for handling large integers and safe serialization.
Specifically designed for Telegram bot integration where user IDs, chat IDs, 
and bot IDs can exceed 64-bit integer limits.
"""

import frappe
import json
from frappe.utils import cstr


def convert_large_integers_to_strings(data):
    """Recursively convert large integers in nested data structures to strings.
    
    This prevents JSON serialization errors when integers exceed 64-bit range,
    which commonly happens with Telegram user IDs, chat IDs, and bot IDs.
    
    Args:
        data: Any data structure (dict, list, int, etc.)
        
    Returns:
        Same data structure with large integers converted to strings
    """
    if isinstance(data, dict):
        return {key: convert_large_integers_to_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_large_integers_to_strings(item) for item in data]
    elif isinstance(data, int):
        # Convert integers that might exceed 64-bit range to strings
        # Use a conservative limit to be safe across all systems
        if abs(data) > 2**31:  # More conservative than JavaScript safe integer limit
            return str(data)
        return data
    else:
        return data


def safe_serialize_response(data):
    """Safely serialize response data by converting large integers to strings.
    
    This is a wrapper around convert_large_integers_to_strings specifically
    for API responses and webhook data.
    
    Args:
        data: Response data to be serialized
        
    Returns:
        Safely serialized data
    """
    return convert_large_integers_to_strings(data)


def safe_json_dumps(data, **kwargs):
    """Safe JSON dumps that handles large integers.
    
    Args:
        data: Data to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string with large integers converted to strings
    """
    safe_data = safe_serialize_response(data)
    return json.dumps(safe_data, **kwargs)


def safe_json_loads(json_string):
    """Safe JSON loads that can handle string-encoded large integers.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed data
    """
    return json.loads(json_string)


def format_telegram_id(telegram_id):
    """Format Telegram ID for safe display and storage.
    
    Args:
        telegram_id: Telegram user ID, chat ID, or bot ID
        
    Returns:
        String representation of the ID
    """
    if isinstance(telegram_id, int):
        return str(telegram_id)
    elif isinstance(telegram_id, str):
        return telegram_id
    else:
        return cstr(telegram_id) 