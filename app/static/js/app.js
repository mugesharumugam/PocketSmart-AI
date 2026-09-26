// Show a loading state while Gemini works, so people don't click twice.
document.querySelectorAll("form[data-loading-text]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button[type=submit]");
    if (!button || !form.checkValidity()) return;
    button.disabled = true;
    button.textContent = form.dataset.loadingText;
    form.setAttribute("aria-busy", "true");
  });
});
