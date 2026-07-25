import bleach
from django import template
from django.utils.html import escape

register = template.Library()

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'code', 'pre', 'blockquote',
    'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'del', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span',
]

ALLOWED_ATTRS = {
    'a': ['href', 'title', 'rel', 'target'],
    'code': ['class'],
    'pre': ['class'],
    'span': ['class'],
}


@register.filter(is_safe=True)
def sanitize_html(value):
    """Sanitize HTML — use after client-side markdown render or for raw storage."""
    return bleach.clean(
        str(value),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,
    )
