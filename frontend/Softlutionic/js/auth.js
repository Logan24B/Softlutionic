function softFacturApiOrigin() {
  if (window.location.protocol === "http:" || window.location.protocol === "https:") {
    return window.location.origin;
  }

  const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
  const host = localHosts.has(window.location.hostname)
    ? window.location.hostname
    : "127.0.0.1";

  return `http://${host}:8000`;
}

const SOFTFACTUR_API_ORIGIN = softFacturApiOrigin();
const SOFTFACTUR_API_BASE = `${SOFTFACTUR_API_ORIGIN}/api`;
let softFacturSessionTimeoutMs = 15 * 60 * 1000;
let softFacturLastActivityAt = Date.now();
let softFacturInactivityTimer = null;
let softFacturIsLoggingOut = false;
let softFacturInactivityWatcherStarted = false;

async function softFacturFetch(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const needsCsrf = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);

  const response = await fetch(`${SOFTFACTUR_API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(needsCsrf ? csrfHeader() : {}),
      ...(options.headers || {})
    }
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || `La API respondió con estado ${response.status}.`);
  }

  return data;
}

function loginPath() {
  return window.location.pathname.includes("/pages/") ? "../login.html" : "login.html";
}

function csrfToken() {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1] || "";
}

function csrfHeader() {
  const token = csrfToken();
  return token ? { "X-CSRFToken": token } : {};
}

function renderSession(user) {
  const userBoxes = document.querySelectorAll(".user-box");
  const name = `${user.PrimerNombre || ""} ${user.SegundoNombre || ""}`.trim();

  userBoxes.forEach((box) => {
    box.innerHTML = "";

    const label = document.createElement("small");
    label.textContent = user.rol_descripcion || "Sesión activa";

    const username = document.createElement("strong");
    username.textContent = name || user.Usuario || user.Email || "Usuario";

    const button = document.createElement("button");
    button.className = "logout-button";
    button.type = "button";
    button.innerHTML = '<i class="fa-solid fa-right-from-bracket" aria-hidden="true"></i><span>Cerrar sesión</span>';
    button.addEventListener("click", logout);

    box.append(label, username, button);
  });
}

function rememberActivity() {
  softFacturLastActivityAt = Date.now();
  scheduleInactivityLogout();
}

function scheduleInactivityLogout() {
  window.clearTimeout(softFacturInactivityTimer);

  const elapsedMs = Date.now() - softFacturLastActivityAt;
  const remainingMs = softFacturSessionTimeoutMs - elapsedMs;

  if (remainingMs <= 0) {
    logout();
    return;
  }

  softFacturInactivityTimer = window.setTimeout(logout, remainingMs);
}

function startInactivityWatcher(timeoutSeconds) {
  if (Number.isFinite(timeoutSeconds) && timeoutSeconds > 0) {
    softFacturSessionTimeoutMs = timeoutSeconds * 1000;
  }

  if (softFacturInactivityWatcherStarted) {
    rememberActivity();
    return;
  }
  softFacturInactivityWatcherStarted = true;

  ["click", "keydown", "mousemove", "scroll", "touchstart"].forEach((eventName) => {
    window.addEventListener(eventName, rememberActivity, { passive: true });
  });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      scheduleInactivityLogout();
    }
  });

  rememberActivity();
}

function adminTargetPath() {
  return window.location.pathname.includes("/pages/") ? "usuarios.html" : "pages/usuarios.html";
}

function dashboardPath() {
  return window.location.pathname.includes("/pages/") ? "../index.html" : "index.html";
}

function defaultUserPath() {
  return window.location.pathname.includes("/pages/") ? "facturas.html" : "pages/facturas.html";
}

function isDashboardPage() {
  const pathname = window.location.pathname.toLowerCase();
  return pathname.endsWith("/index.html") || pathname.endsWith("/softlutionic/");
}

function toggleRestrictedLinks(selector, visible) {
  document.querySelectorAll(selector).forEach((link) => {
    link.hidden = !visible;
    link.style.display = visible ? "" : "none";
    link.setAttribute("aria-hidden", String(!visible));
    link.tabIndex = visible ? 0 : -1;
  });
}

function applyAdminVisibility(user) {
  const isAdmin = Boolean(user?.Rol);

  toggleRestrictedLinks('a[href$="usuarios.html"]', isAdmin);
  toggleRestrictedLinks('a[href$="reportes.html"]', isAdmin);
  toggleRestrictedLinks('nav.menu a[href$="index.html"], nav.menu a[href$="../index.html"]', isAdmin);

  document.querySelectorAll(".brand").forEach((brand) => {
    brand.href = isAdmin ? dashboardPath() : defaultUserPath();
    brand.setAttribute(
      "aria-label",
      isAdmin ? "Ir al dashboard" : "Ir a facturas"
    );
  });

  const pathname = window.location.pathname.toLowerCase();
  const onUsersPage = pathname.endsWith("/usuarios.html");

  if (!isAdmin && (onUsersPage || pathname.endsWith('/reportes.html') || isDashboardPage())) {
    window.location.href = defaultUserPath();
  }
}

async function requireSession() {
  try {
    const data = await softFacturFetch("/auth/session/");
    renderSession(data.user);
    applyAdminVisibility(data.user);
    startInactivityWatcher(data.session_timeout_seconds);
    return data.user;
  } catch (error) {
    window.location.href = loginPath();
    return null;
  }
}

async function logout() {
  if (softFacturIsLoggingOut) {
    return;
  }
  softFacturIsLoggingOut = true;
  window.clearTimeout(softFacturInactivityTimer);

  try {
    await softFacturFetch("/auth/logout/", { method: "POST" });
  } finally {
    window.location.href = loginPath();
  }
}

window.SoftFacturAuth = {
  requireSession,
  logout,
  fetch: softFacturFetch,
  csrfHeader,
  applyAdminVisibility
};

requireSession();
