from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given separator"""
    return value.split(arg)

@register.filter
def slugify_to_username(value, arg):
    """Return both usernames from a slug"""
    return [value, arg]

@register.filter
def user_filter(usernames, current_user):
    """Return the username that is not the current user"""
    for username in usernames:
        if username != current_user:
            return username
    return usernames[0]  # Fallback