import json
from unittest.mock import AsyncMock, patch

from django.template import Context, Template
from django.test import SimpleTestCase

from .consumers import ChatConsumer, DMConsumer
from .models import DirectMessage, Message
from .sanitization import sanitize_markdown_source, sanitize_rendered_markdown


class MarkdownSourceSanitizationTests(SimpleTestCase):
    def test_safe_markdown_source_is_preserved(self):
        markdown = (
            '# Heading\n\n'
            '**bold** and _emphasis_\n\n'
            '- one\n- two\n\n'
            '```python\nprint("safe")\n```\n\n'
            '[Django](https://www.djangoproject.com/)'
        )

        self.assertEqual(sanitize_markdown_source(markdown), markdown)

    def test_html_examples_inside_code_are_preserved_as_code(self):
        markdown = (
            '```html\n'
            '<script>alert(1)</script>\n'
            '<img src=x onerror=alert(1)>\n'
            '```\n\n'
            'Inline `<button onclick="example()">demo</button>`.'
        )

        self.assertEqual(sanitize_markdown_source(markdown), markdown)

    def test_raw_html_payloads_are_removed_from_markdown_source(self):
        payloads = [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<div onclick="alert(1)">click</div>',
            '<svg><script>alert(1)</script></svg>',
            '<svg onload="alert(1)"><a href="javascript:alert(1)">x</a></svg>',
        ]

        for payload in payloads:
            with self.subTest(payload=payload):
                cleaned = sanitize_markdown_source(payload).lower()
                self.assertNotIn('<script', cleaned)
                self.assertNotIn('<img', cleaned)
                self.assertNotIn('<svg', cleaned)
                self.assertNotIn('onerror=', cleaned)
                self.assertNotIn('onclick=', cleaned)
                self.assertNotIn('onload=', cleaned)

    def test_existing_stored_content_is_sanitized_by_template_filter(self):
        template = Template(
            '{% load markdown_extras %}'
            '<div data-raw="{{ body|sanitize_markdown }}"></div>'
        )
        rendered = template.render(Context({
            'body': '**safe** <img src=x onerror=alert(1)>',
        }))

        self.assertIn('**safe**', rendered)
        self.assertNotIn('<img', rendered.lower())
        self.assertNotIn('onerror', rendered.lower())

    def test_message_models_sanitize_new_content_before_persistence(self):
        payload = '**safe** <img src=x onerror=alert(1)>'

        with patch('django.db.models.Model.save', return_value=None):
            message = Message(body=payload)
            message.save()
            direct_message = DirectMessage(body=payload)
            direct_message.save()

        self.assertEqual(message.body, '**safe** ')
        self.assertEqual(direct_message.body, '**safe** ')


class RenderedMarkdownSanitizationTests(SimpleTestCase):
    def test_safe_markdown_html_is_preserved(self):
        rendered_markdown = (
            '<h1>Heading</h1>'
            '<p><strong>bold</strong> and <em>emphasis</em></p>'
            '<ul><li>one</li><li>two</li></ul>'
            '<pre><code class="language-python">print(&quot;safe&quot;)</code></pre>'
            '<p><a href="https://www.djangoproject.com/">Django</a></p>'
        )

        cleaned = sanitize_rendered_markdown(rendered_markdown)

        for expected in ('<h1>', '<strong>', '<em>', '<ul>', '<li>', '<pre>', '<code', '<a href='):
            self.assertIn(expected, cleaned)
        self.assertIn('https://www.djangoproject.com/', cleaned)

    def test_html_payload_displayed_as_code_remains_escaped(self):
        rendered_code = (
            '<pre><code class="language-html">'
            '&lt;script&gt;alert(1)&lt;/script&gt;'
            '</code></pre>'
        )

        cleaned = sanitize_rendered_markdown(rendered_code)

        self.assertIn('<pre><code class="language-html">', cleaned)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', cleaned)
        self.assertNotIn('<script>', cleaned)

    def test_dangerous_rendered_html_is_removed(self):
        payload = (
            '<script>alert(1)</script>'
            '<img src="x" onerror="alert(1)">'
            '<a href="javascript:alert(1)" onclick="alert(1)">bad link</a>'
            '<svg onload="alert(1)"><script>alert(1)</script></svg>'
        )

        cleaned = sanitize_rendered_markdown(payload).lower()

        for forbidden in (
            '<script', '<img', '<svg', 'javascript:',
            'onerror=', 'onclick=', 'onload=',
        ):
            self.assertNotIn(forbidden, cleaned)
        self.assertIn('bad link', cleaned)

    def test_safe_links_remain_and_dangerous_protocols_are_removed(self):
        html = (
            '<a href="https://example.com/path">https</a>'
            '<a href="mailto:student@example.com">email</a>'
            '<a href="/rooms/1/">relative</a>'
            '<a href="jav&#x61;script:alert(1)">encoded attack</a>'
            '<a href="data:text/html,payload">data attack</a>'
        )

        cleaned = sanitize_rendered_markdown(html).lower()

        self.assertIn('href="https://example.com/path"', cleaned)
        self.assertIn('href="mailto:student@example.com"', cleaned)
        self.assertIn('href="/rooms/1/"', cleaned)
        self.assertNotIn('javascript:', cleaned)
        self.assertNotIn('data:text/html', cleaned)


class WebSocketSanitizationTests(SimpleTestCase):
    async def test_room_websocket_sanitizes_message_body_before_sending(self):
        consumer = ChatConsumer()
        consumer.send = AsyncMock()

        await consumer.chat_message({
            'body': '**safe** <img src=x onerror=alert(1)>',
            'username': 'student',
            'avatar_url': '/media/avatar.svg',
            'user_id': 1,
            'timestamp': 'just now',
        })

        payload = json.loads(consumer.send.await_args.kwargs['text_data'])
        self.assertEqual(payload['body'], '**safe** ')

    async def test_dm_websocket_sanitizes_message_body_before_sending(self):
        consumer = DMConsumer()
        consumer.send = AsyncMock()

        await consumer.dm_message({
            'body': '[safe](https://example.com) <svg onload=alert(1)>',
            'sender_id': 1,
            'username': 'student',
            'avatar_url': '/media/avatar.svg',
            'timestamp': 'just now',
        })

        payload = json.loads(consumer.send.await_args.kwargs['text_data'])
        self.assertEqual(payload['body'], '[safe](https://example.com) ')
