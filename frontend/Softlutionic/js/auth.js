function softFacturApiOrigin() {
  if (window.location.protocol === "http:" && window.location.port === "8000") {
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
    throw new Error(data?.detail || `La API respondio con estado ${response.status}.`);
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

function adminTargetPath() {
  return window.location.pathname.includes("/pages/") ? "usuarios.html" : "pages/usuarios.html";
}

function dashboardPath() {
  return window.location.pathname.includes("/pages/") ? "../index.html" : "index.html";
}

function applyAdminVisibility(user) {
  const isAdmin = Boolean(user?.Rol);
  const adminLinks = document.querySelectorAll('a[href$="usuarios.html"]');

  adminLinks.forEach((link) => {
    link.hidden = !isAdmin;
    link.style.display = isAdmin ? "" : "none";
    link.setAttribute("aria-hidden", String(!isAdmin));
    link.tabIndex = isAdmin ? 0 : -1;
  });

  const onUsersPage = window.location.pathname.toLowerCase().endsWith("/usuarios.html");
  if (!isAdmin && onUsersPage) {
    window.location.href = dashboardPath();
  }
}

async function requireSession() {
  try {
    const data = await softFacturFetch("/auth/session/");
    renderSession(data.user);
    applyAdminVisibility(data.user);
    return data.user;
  } catch (error) {
    window.location.href = loginPath();
    return null;
  }
}

async function logout() {
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
