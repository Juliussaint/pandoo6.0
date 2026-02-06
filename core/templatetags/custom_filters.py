from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

# ============================================
# MATH FILTERS
# ============================================

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_num(value, arg):
    """Add arg to value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Calculate percentage: (value / arg) * 100"""
    try:
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def abs_value(value):
    """Return absolute value"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

# ============================================
# CURRENCY FILTERS (RUPIAH)
# ============================================

@register.filter
def currency(value):
    """
    Format number as Rupiah currency: Rp 1.234.567
    Indonesian format: uses dots for thousands separator
    """
    try:
        # Convert to float and format
        num = float(value)
        # Format with comma as thousands separator first
        formatted = "{:,.0f}".format(num)
        # Replace comma with dot (Indonesian format)
        formatted = formatted.replace(',', '.')
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return "Rp 0"

@register.filter
def currency_no_symbol(value):
    """
    Format number without currency symbol: 1.234.567
    Indonesian format: uses dots for thousands separator
    """
    try:
        num = float(value)
        formatted = "{:,.0f}".format(num)
        formatted = formatted.replace(',', '.')
        return formatted
    except (ValueError, TypeError):
        return "0"

@register.filter
def currency_decimal(value):
    """
    Format number as Rupiah with decimals: Rp 1.234.567,50
    Indonesian format: dot for thousands, comma for decimals
    """
    try:
        num = float(value)
        # Format with 2 decimal places
        formatted = "{:,.2f}".format(num)
        # Replace comma with temp, dot with comma, temp with dot
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return "Rp 0,00"

# ============================================
# STRING FILTERS
# ============================================

@register.filter
def to_int(value):
    """Convert to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def to_float(value):
    """Convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# ============================================
# LIST/DICT FILTERS
# ============================================

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def json_encode(value):
    """Encode value as JSON"""
    return mark_safe(json.dumps(value))

# ============================================
# CONDITIONAL FILTERS
# ============================================

@register.filter
def default_if_none_or_zero(value, default):
    """Return default if value is None or 0"""
    if value is None or value == 0 or value == '0':
        return default
    return value