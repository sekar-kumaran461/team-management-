import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """Return the basename of a file path"""
    if value:
        return os.path.basename(value)
    return value

@register.filter
def add(value, arg):
    """Add the arg to the value."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except TypeError:
            return ''

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter"""
    if value:
        return value.split(delimiter)
    return []
