function apiOrigin() {
  if (window.location.protocol === "http:" && window.location.port === "8000") {
    return window.location.origin;
  }

  const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
  const host = localHosts.has(window.location.hostname)
    ? window.location.hostname
    : "127.0.0.1";

  return `http://${host}:8000`;
}

const API_ORIGIN = apiOrigin();
const API_BASE = `${API_ORIGIN}/api`;

const forms = {
  login: document.querySelector("#loginForm"),
  recover: document.querySelector("#recoverForm"),
  reset: document.querySelector("#resetForm")
};
const message = document.querySelector("#authMessage");
const params = new URLSearchParams(window.location.search);
const resetUid = params.get("uid");
const resetToken = params.get("token");

function showView(view) {
  Object.entries(forms).forEach(([key, form]) => {
    form.classList.toggle("active", key === view);
  });
  clearMessage();
}

function setMessage(text, type = "success") {
  message.textContent = text;
  message.className = `auth-message visible ${type}`;
}

function clearMessage() {
  message.textContent = "";
  message.className = "auth-message";
}

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || "No se pudo completar la solicitud.");
  }

  return data;
}

async function redirectIfAuthenticated() {
  if (resetUid && resetToken) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/auth/session/`, {
      credentials: "include",
      headers: { Accept: "application/json" }
    });

    if (response.ok) {
      window.location.href = "index.html";
    }
  } catch (error) {
    return;
  }
}

document.querySelectorAll("[data-auth-view]").forEach((button) => {
  button.addEventListener("click", () => showView(button.dataset.authView));
});

document.querySelectorAll("[data-toggle-password]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.querySelector(`#${button.dataset.togglePassword}`);
    const icon = button.querySelector("i");
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    icon.className = isPassword ? "fa-solid fa-eye-slash" : "fa-solid fa-eye";
  });
});

forms.login.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();

  try {
    await postJson("/auth/login/", {
      usuario: document.querySelector("#loginUser").value.trim(),
      contrasena: document.querySelector("#loginPassword").value
    });
    window.location.href = "index.html";
  } catch (error) {
    setMessage(error.message, "error");
  }
});

forms.recover.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();

  try {
    const data = await postJson("/auth/password-reset/", {
      email: document.querySelector("#recoverEmail").value.trim()
    });
    setMessage(data.detail);
  } catch (error) {
    setMessage(error.message, "error");
  }
});

forms.reset.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();

  const password = document.querySelector("#resetPassword").value;
  const confirm = document.querySelector("#resetPasswordConfirm").value;

  if (password !== confirm) {
    setMessage("Las contrasenas no coinciden.", "error");
    return;
  }

  try {
    const data = await postJson("/auth/password-reset/confirm/", {
      uid: resetUid,
      token: resetToken,
      nueva_contrasena: password
    });
    setMessage(data.detail);
    forms.reset.reset();
    window.history.replaceState({}, document.title, "login.html");
    setTimeout(() => showView("login"), 1200);
  } catch (error) {
    setMessage(error.message, "error");
  }
});

if (resetUid && resetToken) {
  showView("reset");
}

redirectIfAuthenticated();
