const userState = {
  currentUser: null,
  users: []
};

const userElements = {
  form: document.querySelector("#userForm"),
  formTitle: document.querySelector("#userFormTitle"),
  formHint: document.querySelector("#userFormHint"),
  userIdInput: document.querySelector("#userIdInput"),
  firstNameInput: document.querySelector("#firstNameInput"),
  secondNameInput: document.querySelector("#secondNameInput"),
  emailInput: document.querySelector("#userEmailInput"),
  usernameInput: document.querySelector("#usernameInput"),
  passwordInput: document.querySelector("#passwordInput"),
  confirmPasswordInput: document.querySelector("#confirmPasswordInput"),
  roleInput: document.querySelector("#roleInput"),
  activeInput: document.querySelector("#activeInput"),
  dateInput: document.querySelector("#userDateInput"),
  clearButton: document.querySelector("#clearUserButton"),
  saveButton: document.querySelector("#saveUserButton"),
  searchInput: document.querySelector("#userSearchInput"),
  roleFilter: document.querySelector("#userRoleFilter"),
  statusFilter: document.querySelector("#userStatusFilter"),
  table: document.querySelector("#usersTable"),
  totalCard: document.querySelector("#usersTotalCard"),
  adminsCard: document.querySelector("#adminUsersCard"),
  activeCard: document.querySelector("#activeUsersCard"),
  previewName: document.querySelector("#previewUserName"),
  previewEmail: document.querySelector("#previewUserEmail"),
  previewRole: document.querySelector("#previewUserRole"),
  previewStatus: document.querySelector("#previewUserStatus")
};

function usersApiOrigin() {
  if (window.location.protocol === "http:" && window.location.port === "8000") {
    return window.location.origin;
  }

  const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
  const host = localHosts.has(window.location.hostname)
    ? window.location.hostname
    : "127.0.0.1";

  return `http://${host}:8000`;
}

const USERS_API_BASE = `${usersApiOrigin()}/api`;

if (userElements.form) {
  document.addEventListener("DOMContentLoaded", initUsersPage);
}

async function initUsersPage() {
  renderTableMessage("Cargando usuarios desde la base de datos...");

  try {
    userState.currentUser = await getCurrentSessionUser();
    await loadUsers();
    bindEvents();
    applyPermissionState();
    resetForm();
    renderUsers();
  } catch (error) {
    renderTableMessage(error.message);
  }
}

function bindEvents() {
  userElements.form.addEventListener("submit", saveUser);
  userElements.clearButton.addEventListener("click", resetForm);
  userElements.searchInput.addEventListener("input", renderUsers);
  userElements.roleFilter.addEventListener("change", renderUsers);
  userElements.statusFilter.addEventListener("change", renderUsers);

  [
    userElements.firstNameInput,
    userElements.secondNameInput,
    userElements.emailInput,
    userElements.roleInput,
    userElements.activeInput
  ].forEach((field) => {
    field.addEventListener("input", updatePreview);
    field.addEventListener("change", updatePreview);
  });
}

async function loadUsers() {
  const data = await usersFetch("/usuarios/?ordering=PrimerNombre");
  userState.users = asList(data);
}

async function getCurrentSessionUser() {
  if (window.SoftFacturAuth?.requireSession) {
    return window.SoftFacturAuth.requireSession();
  }

  const data = await usersFetch("/auth/session/");
  return data.user;
}

async function usersFetch(path, options = {}) {
  if (window.SoftFacturAuth?.fetch) {
    return window.SoftFacturAuth.fetch(path, options);
  }

  const method = String(options.method || "GET").toUpperCase();
  const needsCsrf = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);

  const response = await fetch(`${USERS_API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(needsCsrf ? usersCsrfHeader() : {}),
      ...(options.headers || {})
    }
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || `La API respondió con estado ${response.status}.`);
  }

  return data;
}

function usersCsrfHeader() {
  const token = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1] || "";
  return token ? { "X-CSRFToken": token } : {};
}

function asList(data) {
  if (Array.isArray(data)) {
    return data;
  }
  return Array.isArray(data?.results) ? data.results : [];
}

function isAdmin() {
  return Boolean(userState.currentUser?.Rol);
}

function applyPermissionState() {
  const admin = isAdmin();
  userElements.form.classList.toggle("readonly-form", !admin);
  userElements.formHint.textContent = admin
    ? "Solo los administradores pueden crear o modificar usuarios."
    : "Tu sesión puede consultar usuarios, pero solo un administrador puede crearlos o modificarlos.";

  userElements.form.querySelectorAll("input, select, button").forEach((element) => {
    if (element.id !== "userDateInput") {
      element.disabled = !admin;
    }
  });
  userElements.clearButton.disabled = !admin;
}

function getFullName(user) {
  return `${user.PrimerNombre || ""} ${user.SegundoNombre || ""}`.trim();
}

function getRoleLabel(user) {
  return user.Rol ? "Administrador" : "Empleado";
}

function formatServerDate(value) {
  if (!value) {
    return "Asignada por el servidor";
  }

  return new Date(value).toLocaleString("es-NI", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
}

function getFilteredUsers() {
  const search = userElements.searchInput.value.trim().toLowerCase();
  const role = userElements.roleFilter.value;
  const status = userElements.statusFilter.value;

  return userState.users.filter((user) => {
    const searchable = [
      getFullName(user),
      user.Email,
      user.Usuario,
      getRoleLabel(user)
    ].join(" ").toLowerCase();

    const matchesSearch = !search || searchable.includes(search);
    const matchesRole =
      role === "all" ||
      (role === "admin" && user.Rol) ||
      (role === "employee" && !user.Rol);
    const matchesStatus =
      status === "all" ||
      (status === "active" && user.is_active) ||
      (status === "inactive" && !user.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });
}

function renderUsers() {
  const fragment = document.createDocumentFragment();
  const filteredUsers = getFilteredUsers();

  filteredUsers.forEach((user, index) => {
    const row = document.createElement("tr");
    row.append(
      createCell(index + 1, { strong: true }),
      createCell(getFullName(user), { strong: true }),
      createCell(user.Email),
      createCell(user.Usuario),
      createRoleCell(user),
      createStatusCell(user.is_active),
      createCell(formatServerDate(user.FechaRegistro)),
      createActionCell(user)
    );
    fragment.appendChild(row);
  });

  if (!filteredUsers.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 8;
    cell.className = "muted-cell";
    cell.textContent = "No hay usuarios que coincidan con la búsqueda.";
    row.appendChild(cell);
    fragment.appendChild(row);
  }

  userElements.table.replaceChildren(fragment);
  updateSummaryCards();
}

function updateSummaryCards() {
  userElements.totalCard.textContent = userState.users.length;
  userElements.adminsCard.textContent = userState.users.filter((user) => user.Rol).length;
  userElements.activeCard.textContent = userState.users.filter((user) => user.is_active).length;
}

function createCell(content, options = {}) {
  const cell = document.createElement("td");

  if (options.className) {
    cell.className = options.className;
  }

  if (options.strong) {
    const strong = document.createElement("strong");
    strong.textContent = content || "";
    cell.appendChild(strong);
    return cell;
  }

  cell.textContent = content || "";
  return cell;
}

function createRoleCell(user) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = `status ${user.Rol ? "paid" : "neutral"}`;
  badge.textContent = getRoleLabel(user);
  cell.appendChild(badge);
  return cell;
}

function createStatusCell(isActive) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = `status ${isActive ? "paid" : "neutral"}`;
  badge.textContent = isActive ? "Activo" : "Inactivo";
  cell.appendChild(badge);
  return cell;
}

function createActionCell(user) {
  const cell = document.createElement("td");
  const actions = document.createElement("span");
  const editButton = document.createElement("button");
  const statusButton = document.createElement("button");
  const statusAction = user.is_active ? "Inactivar" : "Activar";

  actions.className = "table-actions";

  editButton.className = "icon-button";
  editButton.type = "button";
  editButton.title = "Editar usuario";
  editButton.disabled = !isAdmin();
  editButton.setAttribute("aria-label", `Editar ${getFullName(user) || user.Email}`);
  editButton.innerHTML = '<i class="fa-solid fa-pen" aria-hidden="true"></i>';
  editButton.addEventListener("click", () => editUser(user.id));

  statusButton.className = "icon-button";
  statusButton.type = "button";
  statusButton.title = `${statusAction} usuario`;
  statusButton.disabled = !isAdmin() || Number(user.id) === Number(userState.currentUser?.id);
  statusButton.setAttribute("aria-label", `${statusAction} ${getFullName(user) || user.Email}`);
  statusButton.innerHTML = user.is_active
    ? '<i class="fa-solid fa-user-slash" aria-hidden="true"></i>'
    : '<i class="fa-solid fa-user-check" aria-hidden="true"></i>';
  statusButton.addEventListener("click", () => toggleUserStatus(user.id));

  actions.append(editButton, statusButton);
  cell.appendChild(actions);
  return cell;
}

async function saveUser(event) {
  event.preventDefault();

  if (!isAdmin()) {
    alert("Solo un administrador puede guardar usuarios.");
    return;
  }

  const userId = userElements.userIdInput.value;
  const isEditing = Boolean(userId);

  if (!validatePasswords(isEditing)) {
    return;
  }

  const payload = getPayloadFromForm(isEditing);

  setFormBusy(true);

  try {
    const savedUser = await usersFetch(
      isEditing ? `/usuarios/${userId}/` : "/usuarios/",
      {
        method: isEditing ? "PATCH" : "POST",
        body: JSON.stringify(payload)
      }
    );

    const index = userState.users.findIndex((user) => user.id === savedUser.id);
    if (index >= 0) {
      userState.users[index] = savedUser;
    } else {
      userState.users.push(savedUser);
    }

    userState.users.sort((a, b) => getFullName(a).localeCompare(getFullName(b)));
    resetForm();
    renderUsers();
    alert(isEditing ? "Usuario actualizado correctamente." : "Usuario registrado correctamente.");
  } catch (error) {
    alert(`No se pudo guardar el usuario: ${error.message}`);
  } finally {
    setFormBusy(false);
  }
}

function validatePasswords(isEditing) {
  const password = userElements.passwordInput.value;
  const confirmPassword = userElements.confirmPasswordInput.value;

  if (!isEditing && !password) {
    alert("Ingresa una contraseña para crear el usuario.");
    userElements.passwordInput.focus();
    return false;
  }

  if (password !== confirmPassword) {
    alert("Las contraseñas no coinciden. Vuelve a escribirlas.");
    userElements.confirmPasswordInput.focus();
    return false;
  }

  return true;
}

function getPayloadFromForm(isEditing) {
  const email = userElements.emailInput.value.trim();
  const payload = {
    PrimerNombre: userElements.firstNameInput.value.trim(),
    SegundoNombre: userElements.secondNameInput.value.trim(),
    Email: email,
    Usuario: userElements.usernameInput.value.trim() || email,
    Rol: userElements.roleInput.value === "true",
    is_active: userElements.activeInput.value === "true"
  };
  const password = userElements.passwordInput.value;

  if (password) {
    payload.Contrasena = password;
  }

  if (!isEditing && !password) {
    payload.Contrasena = "";
  }

  return payload;
}

function editUser(userId) {
  const user = userState.users.find((item) => item.id === Number(userId));

  if (!user || !isAdmin()) {
    return;
  }

  userElements.userIdInput.value = user.id;
  userElements.firstNameInput.value = user.PrimerNombre || "";
  userElements.secondNameInput.value = user.SegundoNombre || "";
  userElements.emailInput.value = user.Email || "";
  userElements.usernameInput.value = user.Usuario || "";
  userElements.passwordInput.value = "";
  userElements.confirmPasswordInput.value = "";
  userElements.passwordInput.placeholder = "Dejar vacío para conservarla";
  userElements.confirmPasswordInput.placeholder = "Repite solo si cambias contraseña";
  userElements.roleInput.value = String(Boolean(user.Rol));
  userElements.activeInput.value = String(Boolean(user.is_active));
  userElements.dateInput.value = formatServerDate(user.FechaRegistro);
  userElements.formTitle.textContent = "Editando usuario";
  updatePreview();
  userElements.firstNameInput.focus();
}

async function toggleUserStatus(userId) {
  const user = userState.users.find((item) => item.id === Number(userId));

  if (!user || !isAdmin()) {
    return;
  }

  if (Number(user.id) === Number(userState.currentUser?.id)) {
    alert("No puedes inactivar tu propia cuenta mientras la estás usando.");
    return;
  }

  try {
    const updatedUser = await usersFetch(`/usuarios/${userId}/`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !user.is_active })
    });

    const index = userState.users.findIndex((item) => item.id === updatedUser.id);
    if (index >= 0) {
      userState.users[index] = updatedUser;
    }

    renderUsers();
    if (Number(userElements.userIdInput.value) === userId) {
      userElements.activeInput.value = String(Boolean(updatedUser.is_active));
      updatePreview();
    }
  } catch (error) {
    alert(`No se pudo cambiar el estado del usuario: ${error.message}`);
  }
}

function resetForm() {
  userElements.form.reset();
  userElements.userIdInput.value = "";
  userElements.roleInput.value = "false";
  userElements.activeInput.value = "true";
  userElements.dateInput.value = "Asignada por el servidor";
  userElements.passwordInput.placeholder = "Requerida al crear";
  userElements.confirmPasswordInput.placeholder = "Escríbela nuevamente";
  userElements.formTitle.textContent = "Nuevo usuario";
  updatePreview();
}

function updatePreview() {
  const name = `${userElements.firstNameInput.value} ${userElements.secondNameInput.value}`.trim();
  userElements.previewName.textContent = name || "Sin seleccionar";
  userElements.previewEmail.textContent = userElements.emailInput.value || "Sin correo";
  userElements.previewRole.textContent =
    userElements.roleInput.value === "true" ? "Administrador" : "Empleado";
  userElements.previewStatus.textContent =
    userElements.activeInput.value === "true" ? "Activo" : "Inactivo";
}

function setFormBusy(isBusy) {
  userElements.form.querySelectorAll("button, input, select").forEach((element) => {
    if (element.id !== "userDateInput") {
      element.disabled = isBusy;
    }
  });
  userElements.clearButton.disabled = isBusy;
}

function renderTableMessage(message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 8;
  cell.className = "muted-cell";
  cell.textContent = message;
  row.appendChild(cell);
  userElements.table.replaceChildren(row);
}
