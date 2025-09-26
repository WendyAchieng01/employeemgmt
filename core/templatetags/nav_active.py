from django import template

register = template.Library()

@register.simple_tag
def active(request, pattern):
    """Return active class if current path starts with the given pattern."""
    if request.path.startswith(pattern):
        return "active bg-gradient-dark text-white"
    return ""
