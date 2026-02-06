from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the arg
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """
    Subtract arg from value
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """
    Calculate percentage of value from arg
    Usage: {{ value|percentage:total }}
    """
    try:
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def currency(value):
    """
    Format number as Rupiah currency: Rp 1.234.567
    """
    try:
        num = float(value)
        formatted = "{:,.0f}".format(num)
        formatted = formatted.replace(',', '.')
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return "Rp 0"