(function (root) {
  'use strict';

  const ALLOWED_TAGS = new Set([
    'P', 'BR', 'STRONG', 'B', 'EM', 'I', 'CODE', 'PRE', 'BLOCKQUOTE',
    'UL', 'OL', 'LI', 'A', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'HR', 'DEL', 'TABLE', 'THEAD', 'TBODY', 'TR', 'TH', 'TD', 'SPAN',
  ]);

  const ALLOWED_ATTRIBUTES = {
    A: new Set(['href', 'title', 'rel', 'target']),
    CODE: new Set(['class']),
    PRE: new Set(['class']),
    SPAN: new Set(['class']),
  };

  const SAFE_PROTOCOLS = new Set(['http:', 'https:', 'mailto:']);
  const SAFE_CLASS = /^(?:language-[a-z0-9_-]+|hljs(?:\s+[a-z0-9_-]+)*)$/i;

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function isSafeUrl(value) {
    if (typeof value !== 'string') return false;

    const candidate = value.trim();
    if (!candidate) return false;

    // Browsers ignore several whitespace/control characters while parsing a
    // scheme. Remove them before checking so "java\nscript:" is still blocked.
    const compact = candidate.replace(/[\u0000-\u0020\u007f-\u009f]/g, '');
    const explicitScheme = compact.match(/^([a-z][a-z0-9+.-]*):/i);
    if (explicitScheme && !SAFE_PROTOCOLS.has(explicitScheme[1].toLowerCase() + ':')) {
      return false;
    }

    try {
      const base = root.location && root.location.origin
        ? root.location.origin
        : 'https://example.invalid';
      return SAFE_PROTOCOLS.has(new URL(candidate, base).protocol.toLowerCase());
    } catch (error) {
      return false;
    }
  }

  function sanitizeRenderedHtml(html) {
    if (!root.document) {
      throw new Error('A browser document is required to sanitize rendered Markdown.');
    }

    const template = root.document.createElement('template');
    template.innerHTML = String(html == null ? '' : html);

    Array.from(template.content.querySelectorAll('*')).forEach((element) => {
      if (!ALLOWED_TAGS.has(element.tagName)) {
        element.replaceWith(root.document.createTextNode(element.textContent || ''));
        return;
      }

      const allowedForTag = ALLOWED_ATTRIBUTES[element.tagName] || new Set();
      Array.from(element.attributes).forEach((attribute) => {
        const name = attribute.name.toLowerCase();
        if (name.startsWith('on') || !allowedForTag.has(name)) {
          element.removeAttribute(attribute.name);
        }
      });

      if (element.tagName === 'A' && element.hasAttribute('href')) {
        if (!isSafeUrl(element.getAttribute('href'))) {
          element.removeAttribute('href');
          element.removeAttribute('target');
          element.removeAttribute('rel');
        } else if (element.getAttribute('target') === '_blank') {
          element.setAttribute('rel', 'nofollow noopener noreferrer');
        } else {
          element.removeAttribute('target');
        }
      }

      if (element.hasAttribute('class') && !SAFE_CLASS.test(element.getAttribute('class'))) {
        element.removeAttribute('class');
      }
    });

    const commentWalker = root.document.createTreeWalker(
      template.content,
      root.NodeFilter.SHOW_COMMENT,
    );
    const comments = [];
    while (commentWalker.nextNode()) comments.push(commentWalker.currentNode);
    comments.forEach((comment) => comment.remove());

    return template.innerHTML;
  }

  function render(source) {
    const markdown = String(source == null ? '' : source);
    if (!root.marked || typeof root.marked.parse !== 'function') {
      return escapeHtml(markdown).replace(/\r?\n/g, '<br>');
    }

    const rendered = root.marked.parse(markdown, { breaks: true, gfm: true });
    return sanitizeRenderedHtml(rendered);
  }

  function renderInto(element, source) {
    if (!element) return;
    element.innerHTML = render(source);
  }

  const api = {
    escapeHtml,
    isSafeUrl,
    sanitizeRenderedHtml,
    render,
    renderInto,
  };

  root.StudyHelpMarkdown = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
