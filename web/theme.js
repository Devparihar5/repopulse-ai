(() => {
  const key = "repopulse-ai-theme";
  const root = document.documentElement;
  try {
    if (localStorage.getItem(key) === "light") root.dataset.theme = "light";
  } catch {
    // Storage can be unavailable in private browsing.
  }

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("theme-switch");
    const updateLabel = () => {
      button.textContent = root.dataset.theme === "light" ? "Dark theme" : "Light theme";
    };
    updateLabel();
    button.hidden = false;
    button.addEventListener("click", () => {
      root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
      updateLabel();
      try {
        localStorage.setItem(key, root.dataset.theme);
      } catch {
        // The selected theme still applies for this page.
      }
    });
  });
})();
