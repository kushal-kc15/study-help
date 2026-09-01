from django import template

from base.sanitization import sanitize_markdown_source, sanitize_rendered_markdown

register = template.Library()


@register.filter(is_safe=True)
def sanitize_html(value):
    """Sanitize HTML produced by a Markdown renderer."""
    return sanitize_rendered_markdown(value)


@register.filter
def sanitize_markdown(value):
    """Strip raw HTML from Markdown while leaving Markdown syntax intact."""
    return sanitize_markdown_source(value)
