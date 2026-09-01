import re
import uuid

import bleach


MARKDOWN_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'code', 'pre', 'blockquote',
    'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'del', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span',
]

MARKDOWN_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel', 'target'],
    'code': ['class'],
    'pre': ['class'],
    'span': ['class'],
}

MARKDOWN_ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

_markdown_source_cleaner = bleach.Cleaner(
    tags=[],
    attributes={},
    protocols=MARKDOWN_ALLOWED_PROTOCOLS,
    strip=True,
    strip_comments=True,
)

_rendered_markdown_cleaner = bleach.Cleaner(
    tags=MARKDOWN_ALLOWED_TAGS,
    attributes=MARKDOWN_ALLOWED_ATTRIBUTES,
    protocols=MARKDOWN_ALLOWED_PROTOCOLS,
    strip=True,
    strip_comments=True,
)

_fenced_code = re.compile(
    r'^ {0,3}(?P<fence>`{3,}|~{3,})[^\r\n]*\r?\n.*?'
    r'^ {0,3}(?P=fence)[ \t]*\r?$',
    re.MULTILINE | re.DOTALL,
)
_indented_code = re.compile(r'(?m)(?:^(?: {4}|\t).*?(?:\r?\n|$))+')
_inline_code = re.compile(r'(?P<ticks>`+)[^\r\n]*?(?P=ticks)')


def _protect_code(markdown):
    protected = {}
    token_prefix = f'__STUDYHELP_CODE_{uuid.uuid4().hex}_'

    def replace(match):
        token = f'{token_prefix}{len(protected)}__'
        protected[token] = match.group(0)
        return token

    markdown = _fenced_code.sub(replace, markdown)
    markdown = _indented_code.sub(replace, markdown)
    markdown = _inline_code.sub(replace, markdown)
    return markdown, protected


def sanitize_markdown_source(value):
    """Remove raw HTML while preserving Markdown, including code content."""
    markdown, protected_code = _protect_code(str(value or ''))
    cleaned = _markdown_source_cleaner.clean(markdown)
    for token, code in protected_code.items():
        cleaned = cleaned.replace(token, code)
    return cleaned


def sanitize_rendered_markdown(value):
    """Allow only the HTML that legitimate Markdown rendering can produce."""
    return _rendered_markdown_cleaner.clean(str(value or ''))
