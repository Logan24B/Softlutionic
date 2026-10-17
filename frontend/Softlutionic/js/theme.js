(() => {
  const key = "softfactur-theme";
  const root = document.documentElement;
  const showToggle = document.currentScript.hasAttribute("data-theme-toggle");
  let theme = "light";
  try {
    theme = localStorage.getItem(key) === "dark" ? "dark" : "light";
  } catch (_) { /* El tema funciona aunque el almacenamiento esté bloqueado. */ }
  root.dataset.theme = theme;

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "theme-toggle";
    const icon = document.createElement("span");
    icon.setAttribute("aria-hidden", "true");
    button.append(icon);
    const actions = document.querySelector(".topbar-actions");
    if (showToggle && actions) {
      actions.append(button);
    } else if (showToggle) {
      const toolbar = document.createElement("div");
      toolbar.className = "login-theme-toolbar";
      toolbar.append(button);
      document.body.prepend(toolbar);
    }

    function refresh() {
      const dark = root.dataset.theme === "dark";
      const label = dark ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
      button.setAttribute("aria-label", label);
      button.setAttribute("aria-pressed", String(dark));
      button.title = label;
      icon.textContent = dark ? "☀" : "☾";
      if (window.Chart) {
        const styles = getComputedStyle(root);
        Chart.defaults.color = styles.getPropertyValue("--muted").trim();
        Chart.defaults.borderColor = styles.getPropertyValue("--line").trim();
        Object.values(Chart.instances).forEach((chart) => chart.update("none"));
      }
    }
    button.addEventListener("click", () => {
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem(key, root.dataset.theme); } catch (_) { }
      refresh();
    });
    window.addEventListener("storage", (event) => {
      if (event.key === key || event.key === null) {
        root.dataset.theme = event.newValue === "dark" ? "dark" : "light";
        refresh();
      }
    });
    refresh();
  });
})();
