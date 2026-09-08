const serviceState = {
  services: []
};

const API_ORIGIN =
  window.location.protocol === "http:" || window.location.protocol === "https:"
    ? window.location.origin
    : "http://127.0.0.1:8000";

const serviceElements = {
  form: document.querySelector("#serviceForm"),
  formTitle: document.querySelector("#serviceFormTitle"),
  idInput: document.querySelector("#serviceIdInput"),
  nameInput: document.querySelector("#serviceNameInput"),
  priceInput: document.querySelector("#servicePriceInput"),
  durationInput: document.querySelector("#serviceDurationInput"),
  descriptionInput: document.querySelector("#serviceDescriptionInput"),
  clearButton: document.querySelector("#clearServiceButton"),
  searchInput: document.querySelector("#serviceSearchInput"),
  table: document.querySelector("#servicesTable"),
  total: document.querySelector("#servicesTotal"),
  average: document.querySelector("#servicesAverage"),
  max: document.querySelector("#servicesMax"),
  previewName: document.querySelector("#previewServiceName"),
  previewPrice: document.querySelector("#previewServicePrice"),
  previewDuration: document.querySelector("#previewServiceDuration")
};

if (serviceElements.form) {
  document.addEventListener("DOMContentLoaded", initServicesPage);
}

async function initServicesPage() {
  renderTableMessage("Cargando servicios desde la base de datos...");

  try {
    await loadServices();
    bindEvents();
    resetForm();
  } catch (error) {
    renderTableMessage(error.message);
  }
}

function bindEvents() {
  serviceElements.form.addEventListener("submit", saveService);
  serviceElements.clearButton.addEventListener("click", resetForm);
  serviceElements.searchInput.addEventListener("input", renderServices);

  [
    serviceElements.nameInput,
    serviceElements.priceInput,
    serviceElements.durationInput
  ].forEach((field) => {
    field.addEventListener("input", updatePreview);
    field.addEventListener("change", updatePreview);
  });
}

async function loadServices() {
  const data = await fetchJson("/api/servicios/?ordering=Nombre_Servicio");
  serviceState.services = asList(data);
  renderServices();
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

function getFilteredServices() {
  const search = serviceElements.searchInput.value.trim().toLowerCase();

  return serviceState.services.filter((service) => {
    const searchable = [
      service.Nombre_Servicio,
      service.Descripcion,
      service.Duracion,
      `SERV-${String(service.id).padStart(3, "0")}`
    ].join(" ").toLowerCase();

    return !search || searchable.includes(search);
  });
}

function renderServices() {
  const fragment = document.createDocumentFragment();
  const filteredServices = getFilteredServices();

  updateSummaryCards();

  filteredServices.forEach((service) => {
    const row = document.createElement("tr");
    row.append(
      createCell(`SERV-${String(service.id).padStart(3, "0")}`, { className: "service-code" }),
      createCell(service.Nombre_Servicio, { strong: true }),
      createCell(service.Descripcion, { className: "service-description-cell" }),
      createCell(service.Duracion),
      createCell(formatMoney(service.Precio), { strong: true, className: "service-price-cell" }),
      createActionCell(service)
    );
    fragment.appendChild(row);
  });

  if (!filteredServices.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.className = "muted-cell";
    cell.textContent = "No hay servicios que coincidan con la búsqueda.";
    row.appendChild(cell);
    fragment.appendChild(row);
  }

  serviceElements.table.replaceChildren(fragment);
}

function updateSummaryCards() {
  const count = serviceState.services.length;
  const total = serviceState.services.reduce((sum, service) => sum + Number(service.Precio || 0), 0);
  const max = serviceState.services.reduce((currentMax, service) => {
    return Math.max(currentMax, Number(service.Precio || 0));
  }, 0);

  serviceElements.total.textContent = count;
  serviceElements.average.textContent = formatMoney(count ? total / count : 0);
  serviceElements.max.textContent = formatMoney(max);
}

function createActionCell(service) {
  const cell = document.createElement("td");
  const actions = document.createElement("span");
  const editButton = document.createElement("button");
  const deleteButton = document.createElement("button");

  actions.className = "table-actions";

  editButton.className = "icon-button";
  editButton.type = "button";
  editButton.title = "Editar servicio";
  editButton.setAttribute("aria-label", `Editar ${service.Nombre_Servicio}`);
  editButton.innerHTML = '<i class="fa-solid fa-pen" aria-hidden="true"></i>';
  editButton.addEventListener("click", () => editService(service.id));

  deleteButton.className = "icon-button";
  deleteButton.type = "button";
  deleteButton.title = "Eliminar servicio";
  deleteButton.setAttribute("aria-label", `Eliminar ${service.Nombre_Servicio}`);
  deleteButton.innerHTML = '<i class="fa-solid fa-trash" aria-hidden="true"></i>';
  deleteButton.addEventListener("click", () => deleteService(service.id));

  actions.append(editButton, deleteButton);
  cell.appendChild(actions);
  return cell;
}

async function saveService(event) {
  event.preventDefault();
  const serviceId = serviceElements.idInput.value;
  const isEditing = Boolean(serviceId);
  const payload = getPayloadFromForm();

  setFormBusy(true);

  try {
    const savedService = await fetchJson(isEditing ? `/api/servicios/${serviceId}/` : "/api/servicios/", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify(payload)
    });

    if (isEditing) {
      const index = serviceState.services.findIndex((service) => service.id === savedService.id);
      if (index >= 0) {
        serviceState.services[index] = savedService;
      }
    } else {
      serviceState.services.push(savedService);
    }

    serviceState.services.sort((a, b) => a.Nombre_Servicio.localeCompare(b.Nombre_Servicio));
    renderServices();
    resetForm();
    alert(isEditing ? "Servicio actualizado correctamente." : "Servicio registrado correctamente.");
  } catch (error) {
    alert(`No se pudo guardar el servicio: ${error.message}`);
  } finally {
    setFormBusy(false);
  }
}

function getPayloadFromForm() {
  return {
    Nombre_Servicio: serviceElements.nameInput.value.trim(),
    Descripcion: serviceElements.descriptionInput.value.trim(),
    Precio: Number(serviceElements.priceInput.value || 0),
    Duracion: serviceElements.durationInput.value.trim()
  };
}

function editService(serviceId) {
  const service = serviceState.services.find((item) => item.id === Number(serviceId));

  if (!service) {
    return;
  }

  serviceElements.idInput.value = service.id;
  serviceElements.nameInput.value = service.Nombre_Servicio;
  serviceElements.priceInput.value = service.Precio;
  serviceElements.durationInput.value = service.Duracion;
  serviceElements.descriptionInput.value = service.Descripcion;
  serviceElements.formTitle.textContent = `Editando servicio #${service.id}`;
  updatePreview();
  serviceElements.nameInput.focus();
}

async function deleteService(serviceId) {
  const service = serviceState.services.find((item) => item.id === Number(serviceId));

  if (!service) {
    return;
  }

  const confirmed = window.confirm(`Deseas eliminar el servicio "${service.Nombre_Servicio}"?`);
  if (!confirmed) {
    return;
  }

  try {
    await fetchJson(`/api/servicios/${serviceId}/`, { method: "DELETE" });
    serviceState.services = serviceState.services.filter((item) => item.id !== Number(serviceId));
    renderServices();
    resetForm();
    alert("Servicio eliminado correctamente.");
  } catch (error) {
    alert(`No se pudo eliminar el servicio. Si ya fue usado en facturas, SQL Server protege el registro. Detalle: ${error.message}`);
  }
}

function resetForm() {
  serviceElements.form.reset();
  serviceElements.idInput.value = "";
  serviceElements.formTitle.textContent = "Nuevo servicio";
  updatePreview();
}

function updatePreview() {
  serviceElements.previewName.textContent = serviceElements.nameInput.value || "Sin seleccionar";
  serviceElements.previewPrice.textContent = formatMoney(serviceElements.priceInput.value || 0);
  serviceElements.previewDuration.textContent = serviceElements.durationInput.value || "Sin duración";
}

function setFormBusy(isBusy) {
  serviceElements.form.querySelectorAll("button, input, textarea").forEach((element) => {
    element.disabled = isBusy;
  });
  serviceElements.clearButton.disabled = isBusy;
}

function renderTableMessage(message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 6;
  cell.className = "muted-cell";
  cell.textContent = message;
  row.appendChild(cell);
  serviceElements.table.replaceChildren(row);
}

function createCell(content, options = {}) {
  const cell = document.createElement("td");

  if (options.className) {
    cell.className = options.className;
  }

  if (options.strong) {
    const strongElement = document.createElement("strong");
    strongElement.textContent = content || "";
    cell.appendChild(strongElement);
    return cell;
  }

  cell.textContent = content || "";
  return cell;
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

function formatMoney(value) {
  return `C$ ${Number(value || 0).toLocaleString("es-NI", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}
