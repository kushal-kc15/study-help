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
