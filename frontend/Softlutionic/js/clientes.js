const clientState = {
  clientes: [],
  departamentos: []
};

const API_ORIGIN =
  window.location.protocol === "http:" && window.location.port === "8000"
    ? window.location.origin
    : "http://127.0.0.1:8000";

const clientElements = {
  form: document.querySelector("#clientForm"),
  formTitle: document.querySelector("#formTitle"),
  clientIdInput: document.querySelector("#clientIdInput"),
  namesInput: document.querySelector("#namesInput"),
  lastNamesInput: document.querySelector("#lastNamesInput"),
  phoneInput: document.querySelector("#phoneInput"),
  emailInput: document.querySelector("#emailInput"),
  departmentInput: document.querySelector("#departmentInput"),
  documentNumberInput: document.querySelector("#documentNumberInput"),
  dateInput: document.querySelector("#dateInput"),
  timeInput: document.querySelector("#timeInput"),
  statusInput: document.querySelector("#statusInput"),
  addressInput: document.querySelector("#addressInput"),
  clearClientButton: document.querySelector("#clearClientButton"),
  clientsTable: document.querySelector("#clientsTable"),
  clientSearchInput: document.querySelector("#clientSearchInput"),
  clientStatusFilter: document.querySelector("#clientStatusFilter"),
  totalClientsCard: document.querySelector("#totalClientsCard"),
  activeClientsCard: document.querySelector("#activeClientsCard"),
  newClientsCard: document.querySelector("#newClientsCard"),
  previewClientName: document.querySelector("#previewClientName"),
  previewClientEmail: document.querySelector("#previewClientEmail"),
  previewClientPhone: document.querySelector("#previewClientPhone"),
  previewClientStatus: document.querySelector("#previewClientStatus")
};

if (clientElements.form) {
  document.addEventListener("DOMContentLoaded", initClientsPage);
}

async function initClientsPage() {
  try {
    renderTableMessage("Cargando clientes desde la base de datos...");
    await loadInitialData();
    fillDepartmentSelect();
    resetForm();
    renderClients();
    bindEvents();
  } catch (error) {
    renderTableMessage(error.message);
  }
}

function bindEvents() {
  clientElements.form.addEventListener("submit", saveClient);
  clientElements.clearClientButton.addEventListener("click", resetForm);
  clientElements.clientSearchInput.addEventListener("input", renderClients);
  clientElements.clientStatusFilter.addEventListener("change", renderClients);

  [
    clientElements.namesInput,
    clientElements.lastNamesInput,
    clientElements.phoneInput,
    clientElements.emailInput,
    clientElements.statusInput
  ].forEach((field) => {
    field.addEventListener("input", updatePreviewFromForm);
    field.addEventListener("change", updatePreviewFromForm);
  });
}

async function loadInitialData() {
  const [departamentos, clientes] = await Promise.all([
    fetchJson("/api/departamentos/?ordering=Nombre"),
    fetchJson("/api/clientes/?ordering=Nombre")
  ]);

  clientState.departamentos = asList(departamentos);
  clientState.clientes = asList(clientes);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(apiUrl(url), {
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(window.SoftFacturAuth?.csrfHeader?.() || {})
    },
    ...options
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(formatApiError(data, response.status));
  }

  return data;
}

function apiUrl(url) {
  return url.startsWith("/api") ? `${API_ORIGIN}${url}` : url;
}

function asList(data) {
  if (Array.isArray(data)) {
    return data;
  }
  return Array.isArray(data?.results) ? data.results : [];
}

function fillDepartmentSelect() {
  const fragment = document.createDocumentFragment();

  clientState.departamentos.forEach((departamento) => {
    const option = document.createElement("option");
    option.value = departamento.id;
    option.textContent = departamento.Nombre;
    fragment.appendChild(option);
  });

  clientElements.departmentInput.replaceChildren(fragment);
}

function getTodayValue() {
  return new Date().toISOString().slice(0, 10);
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

function formatServerTime(value) {
  if (!value) {
    return "Asignada por el servidor";
  }

  return String(value).slice(0, 5);
}

function getDepartmentName(id) {
  const departamento = clientState.departamentos.find((item) => item.id === Number(id));
  return departamento ? departamento.Nombre : "Sin departamento";
}

function getClientFullName(cliente) {
  return `${cliente.Nombre} ${cliente.Apellido || ""}`.trim();
}

function getClientById(clientId) {
  return clientState.clientes.find((cliente) => cliente.id === Number(clientId));
}

function createCell(content, options = {}) {
  const cell = document.createElement("td");

  if (options.className) {
    cell.className = options.className;
  }

  if (options.strong) {
    const strong = document.createElement("strong");
    strong.textContent = content;
    cell.appendChild(strong);
    return cell;
  }

  cell.textContent = content || "";
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

function createActionCell(cliente) {
  const cell = document.createElement("td");
  const actions = document.createElement("span");
  const editButton = document.createElement("button");
  const statusButton = document.createElement("button");
  const statusAction = cliente.Estado ? "Inactivar" : "Activar";

  actions.className = "table-actions";

  editButton.className = "icon-button";
  editButton.type = "button";
  editButton.title = "Editar cliente";
  editButton.setAttribute("aria-label", `Editar ${getClientFullName(cliente)}`);
  editButton.innerHTML = '<i class="fa-solid fa-pen" aria-hidden="true"></i>';
  editButton.addEventListener("click", () => editClient(cliente.id));

  statusButton.className = "icon-button";
  statusButton.type = "button";
  statusButton.title = `${statusAction} cliente`;
  statusButton.setAttribute("aria-label", `${statusAction} ${getClientFullName(cliente)}`);
  statusButton.innerHTML = cliente.Estado
    ? '<i class="fa-solid fa-user-slash" aria-hidden="true"></i>'
    : '<i class="fa-solid fa-user-check" aria-hidden="true"></i>';
  statusButton.addEventListener("click", () => toggleClientStatus(cliente.id));

  actions.append(editButton, statusButton);
  cell.appendChild(actions);
  return cell;
}

function getFilteredClients() {
  const search = clientElements.clientSearchInput.value.trim().toLowerCase();
  const statusFilter = clientElements.clientStatusFilter.value;

  return clientState.clientes.filter((cliente) => {
    const searchable = [
      getClientFullName(cliente),
      cliente.Telefono,
      cliente.Correo,
      cliente.Direccion,
      cliente.Cedula,
      getDepartmentName(cliente.DepartamentoId)
    ].join(" ").toLowerCase();

    const matchesSearch = !search || searchable.includes(search);
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && cliente.Estado) ||
      (statusFilter === "inactive" && !cliente.Estado);

    return matchesSearch && matchesStatus;
  });
}

function renderClients() {
  const fragment = document.createDocumentFragment();
  const filteredClients = getFilteredClients();

  filteredClients.forEach((cliente, index) => {
    const row = document.createElement("tr");
    row.append(
      createCell(index + 1, { strong: true }),
      createCell(getClientFullName(cliente), { strong: true }),
      createCell(cliente.Telefono),
      createCell(cliente.Correo),
      createCell(getDepartmentName(cliente.DepartamentoId)),
      createCell(cliente.Cedula || "Sin cedula"),
      createStatusCell(Boolean(cliente.Estado)),
      createActionCell(cliente)
    );
    fragment.appendChild(row);
  });

  if (!filteredClients.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 8;
    cell.className = "muted-cell";
    cell.textContent = "No hay clientes que coincidan con la búsqueda.";
    row.appendChild(cell);
    fragment.appendChild(row);
  }

  clientElements.clientsTable.replaceChildren(fragment);
  updateSummaryCards();
}

function updateSummaryCards() {
  const activeClients = clientState.clientes.filter((cliente) => cliente.Estado);
  const currentMonth = getTodayValue().slice(0, 7);
  const newClients = clientState.clientes.filter((cliente) => {
    return String(cliente.FechaRegistro || "").slice(0, 7) === currentMonth;
  });

  clientElements.totalClientsCard.textContent = clientState.clientes.length;
  clientElements.activeClientsCard.textContent = activeClients.length;
  clientElements.newClientsCard.textContent = newClients.length;
}

function updatePreviewFromForm() {
  const fullName = `${clientElements.namesInput.value} ${clientElements.lastNamesInput.value}`.trim();

  clientElements.previewClientName.textContent = fullName || "Sin seleccionar";
  clientElements.previewClientEmail.textContent = clientElements.emailInput.value || "Sin correo";
  clientElements.previewClientPhone.textContent = clientElements.phoneInput.value || "Sin teléfono";
  clientElements.previewClientStatus.textContent =
    clientElements.statusInput.value === "true" ? "Activo" : "Inactivo";
}

function resetForm() {
  clientElements.form.reset();
  clientElements.clientIdInput.value = "";
  clientElements.dateInput.value = "Asignada por el servidor";
  clientElements.timeInput.value = "Asignada por el servidor";
  clientElements.statusInput.value = "true";
  clientElements.formTitle.textContent = "Nuevo cliente";
  updatePreviewFromForm();
}

function getPayloadFromForm() {
  return {
    Nombre: clientElements.namesInput.value.trim(),
    Apellido: clientElements.lastNamesInput.value.trim(),
    Telefono: normalizeNicaraguaPhone(clientElements.phoneInput.value),
    Correo: clientElements.emailInput.value.trim(),
    DepartamentoId: Number(clientElements.departmentInput.value),
    Cedula: clientElements.documentNumberInput.value.trim(),
    Direccion: clientElements.addressInput.value.trim(),
    Estado: clientElements.statusInput.value === "true"
  };
}

function normalizeNicaraguaPhone(value) {
  const digits = String(value || "").replace(/\D/g, "");

  if (digits.length === 8) {
    return `+505 ${digits.slice(0, 4)} ${digits.slice(4)}`;
  }

  if (digits.length === 11 && digits.startsWith("505")) {
    return `+505 ${digits.slice(3, 7)} ${digits.slice(7)}`;
  }

  return String(value || "").trim();
}

async function saveClient(event) {
  event.preventDefault();
  const clientId = clientElements.clientIdInput.value;
  const payload = getPayloadFromForm();
  const isEditing = Boolean(clientId);

  setFormBusy(true);

  try {
    const savedClient = await fetchJson(isEditing ? `/api/clientes/${clientId}/` : "/api/clientes/", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify(payload)
    });

    if (isEditing) {
      const index = clientState.clientes.findIndex((cliente) => cliente.id === savedClient.id);
      if (index >= 0) {
        clientState.clientes[index] = savedClient;
      }
    } else {
      clientState.clientes.push(savedClient);
    }

    renderClients();
    resetForm();
    alert(isEditing ? "Cliente actualizado correctamente." : "Cliente registrado correctamente.");
  } catch (error) {
    alert(`No se pudo guardar el cliente: ${error.message}`);
  } finally {
    setFormBusy(false);
  }
}

function editClient(clientId) {
  const cliente = getClientById(clientId);

  if (!cliente) {
    return;
  }

  clientElements.clientIdInput.value = cliente.id;
  clientElements.namesInput.value = cliente.Nombre;
  clientElements.lastNamesInput.value = cliente.Apellido || "";
  clientElements.phoneInput.value = cliente.Telefono;
  clientElements.emailInput.value = cliente.Correo;
  clientElements.departmentInput.value = cliente.DepartamentoId;
  clientElements.documentNumberInput.value = cliente.Cedula || "";
  clientElements.dateInput.value = formatServerDate(cliente.FechaRegistro);
  clientElements.timeInput.value = formatServerTime(cliente.HoraRegistro);
  clientElements.statusInput.value = String(Boolean(cliente.Estado));
  clientElements.addressInput.value = cliente.Direccion;
  clientElements.formTitle.textContent = "Editando cliente";
  updatePreviewFromForm();
  clientElements.namesInput.focus();
}

async function toggleClientStatus(clientId) {
  const cliente = getClientById(clientId);

  if (!cliente) {
    return;
  }

  try {
    const updatedClient = await fetchJson(`/api/clientes/${clientId}/`, {
      method: "PATCH",
      body: JSON.stringify({ Estado: !cliente.Estado })
    });

    const index = clientState.clientes.findIndex((item) => item.id === updatedClient.id);
    if (index >= 0) {
      clientState.clientes[index] = updatedClient;
    }

    renderClients();

    if (Number(clientElements.clientIdInput.value) === clientId) {
      clientElements.statusInput.value = String(Boolean(updatedClient.Estado));
      updatePreviewFromForm();
    }
  } catch (error) {
    alert(`No se pudo cambiar el estado del cliente: ${error.message}`);
  }
}

function setFormBusy(isBusy) {
  clientElements.form.querySelectorAll("button, input, select, textarea").forEach((element) => {
    if (element.id !== "dateInput" && element.id !== "timeInput") {
      element.disabled = isBusy;
    }
  });
  clientElements.clearClientButton.disabled = isBusy;
}

function renderTableMessage(message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 8;
  cell.className = "muted-cell";
  cell.textContent = message;
  row.appendChild(cell);
  clientElements.clientsTable.replaceChildren(row);
}

function formatApiError(data, status) {
  if (!data) {
    return `La API respondio con estado ${status}.`;
  }

  if (typeof data === "string") {
    return data;
  }

  return Object.entries(data)
    .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join(" | ");
}
