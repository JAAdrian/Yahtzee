from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dictionary access by variable key in templates: dict|get_item:key."""
    if dictionary is None:
        return None
    return dictionary.get(key)
