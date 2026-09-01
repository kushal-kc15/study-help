// Markdown rendering for server-rendered messages
document.addEventListener('DOMContentLoaded', function () {
  if (typeof StudyHelpMarkdown === 'undefined') return;
  document.querySelectorAll('[data-raw]').forEach(el => {
    StudyHelpMarkdown.renderInto(el, el.dataset.raw);
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

// Dropdown & Notification Modal
(function () {
  const dropdownMenu = document.querySelector(".dropdown-menu");
  const dropdownButton = document.querySelector(".dropdown-button");
  const notifToggle = document.getElementById("notif-toggle");
  const notifModal = document.getElementById("notif-modal");

  if (dropdownButton && dropdownMenu) {
    dropdownButton.addEventListener("click", (e) => {
      e.stopPropagation();
      if (notifModal) notifModal.classList.remove("show");
      dropdownMenu.classList.toggle("show");
    });
  }

  if (notifToggle && notifModal) {
    notifToggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (dropdownMenu) dropdownMenu.classList.remove("show");
      notifModal.classList.toggle("show");
    });
  }

  document.addEventListener("click", (e) => {
    if (dropdownMenu && !dropdownMenu.contains(e.target) && dropdownButton && !dropdownButton.contains(e.target)) {
      dropdownMenu.classList.remove("show");
    }
    if (notifModal && !notifModal.contains(e.target) && notifToggle && !notifToggle.contains(e.target)) {
      notifModal.classList.remove("show");
    }
  });
})();

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
