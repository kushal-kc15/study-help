'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const safeMarkdown = require('../static/js/safe-markdown.js');


test('allows safe absolute and relative link destinations', () => {
  for (const url of [
    'https://example.com/path',
    'http://example.com/path',
    'mailto:student@example.com',
    '/rooms/1/',
    './notes',
    '#message-1',
  ]) {
    assert.equal(safeMarkdown.isSafeUrl(url), true, url);
  }
});


test('blocks scriptable and obfuscated link destinations', () => {
  for (const url of [
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    'java\nscript:alert(1)',
    'java\u0000script:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
  ]) {
    assert.equal(safeMarkdown.isSafeUrl(url), false, url);
  }
});


test('HTML fallback escaping neutralizes executable markup and attributes', () => {
  const escaped = safeMarkdown.escapeHtml(
    '<img src=x onerror="alert(1)"><svg onload="alert(1)"></svg>',
  );

  assert.equal(escaped.includes('<img'), false);
  assert.equal(escaped.includes('<svg'), false);
  assert.match(escaped, /&lt;img/);
  assert.match(escaped, /&lt;svg/);
});
