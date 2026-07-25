// Markdown rendering for server-rendered messages
document.addEventListener('DOMContentLoaded', function () {
  if (typeof marked === 'undefined') return;
  marked.setOptions({ breaks: true, gfm: true });
  document.querySelectorAll('[data-raw]').forEach(el => {
    el.innerHTML = marked.parse(el.dataset.raw);
  });
});

// Dark Mode
(function () {
  const html = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const sunIcon = document.getElementById('theme-icon-sun');
  const moonIcon = document.getElementById('theme-icon-moon');

  function applyTheme(dark) {
    html.setAttribute('data-theme', dark ? 'dark' : 'light');
    if (sunIcon) sunIcon.style.display = dark ? 'block' : 'none';
    if (moonIcon) moonIcon.style.display = dark ? 'none' : 'block';
  }

  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved === 'dark' || (!saved && prefersDark));

  if (toggle) {
    toggle.addEventListener('click', function () {
      const isDark = html.getAttribute('data-theme') === 'dark';
      applyTheme(!isDark);
      localStorage.setItem('theme', isDark ? 'light' : 'dark');
    });
  }
})();

// Dropdown Menu
const dropdownMenu = document.querySelector(".dropdown-menu");
const dropdownButton = document.querySelector(".dropdown-button");

if (dropdownButton) {
  dropdownButton.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdownMenu.classList.toggle("show");
  });

  document.addEventListener("click", (e) => {
    if (!dropdownMenu.contains(e.target)) {
      dropdownMenu.classList.remove("show");
    }
  });
}

// Upload Image Preview
const photoInput = document.querySelector("#avatar");
const photoPreview = document.querySelector("#preview-avatar");
if (photoInput && photoPreview) {
  photoInput.onchange = () => {
    const [file] = photoInput.files;
    if (file) {
      photoPreview.src = URL.createObjectURL(file);
    }
  };
}

// Scroll to Bottom of Chat
const conversationThread = document.querySelector(".room__box");
if (conversationThread) {
  conversationThread.scrollTop = conversationThread.scrollHeight;
}
