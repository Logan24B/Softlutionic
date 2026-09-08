const API_ORIGIN =
  window.location.protocol === "http:" || window.location.protocol === "https:"
    ? window.location.origin
    : "http://127.0.0.1:8000";
const API_BASE = `${API_ORIGIN}/api`;

const moraState = {
  moras: [],
  filter: "todas"
};

const moraElements = {
  pendingCard: document.querySelector("#pendingMorasCard"),
  paidCard: document.querySelector("#paidMorasCard"),
  pendingAmountCard: document.querySelector("#pendingAmountCard"),
  table: document.querySelector("#morasTable"),
  searchInput: document.querySelector("#moraSearchInput"),
  statusFilter: document.querySelector("#moraStatusFilter"),
  refreshButton: document.querySelector("#refreshMorasButton")
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", loadMorasPage);
} else {
  loadMorasPage();
}

async function loadMorasPage() {
  try {
    setBusy(true);
    const moras = await fetchJson(`${API_BASE}/moras/?ordering=-Fecha_Inicio,-Hora_Inicio`);
    moraState.moras = asList(moras);
    renderMorasPage();
    bindEventsOnce();
  } catch (error) {
    console.error("No se pudo cargar la entidad Mora.", error);
    renderTableMessage(error.message);
  } finally {
    setBusy(false);
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
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

function asList(data) {
  if (Array.isArray(data)) {
    return data;
  }
  return Array.isArray(data?.results) ? data.results : [];
}

function bindEventsOnce() {
  if (moraElements.refreshButton.dataset.bound === "true") {
    return;
  }

  moraElements.searchInput.addEventListener("input", renderMorasPage);
  moraElements.statusFilter.addEventListener("change", () => {
    moraState.filter = moraElements.statusFilter.value;
    renderMorasPage();
  });
  moraElements.refreshButton.addEventListener("click", loadMorasPage);
  moraElements.refreshButton.dataset.bound = "true";
}

function renderMorasPage() {
  const filtered = getFilteredMoras();
  const pending = moraState.moras.filter((mora) => !mora.EstadoMora);
  const paid = moraState.moras.filter((mora) => mora.EstadoMora);
  const pendingAmount = pending.reduce((total, mora) => total + Number(mora.Monto_Mora || 0), 0);

  moraElements.pendingCard.textContent = pending.length;
  moraElements.paidCard.textContent = paid.length;
  moraElements.pendingAmountCard.textContent = formatMoney(pendingAmount);

  renderMorasTable(filtered);
}

function getFilteredMoras() {
  const search = moraElements.searchInput.value.trim().toLowerCase();
  const statusFilter = moraState.filter;

  return moraState.moras.filter((mora) => {
    const factura = mora.factura_detalle || {};
    const searchable = [
      formatInvoiceCode(factura.CodigoFact),
      getInvoiceCustomer(factura),
      mora.DescripcionMora
    ]
      .join(" ")
      .toLowerCase();
    const matchesSearch = !search || searchable.includes(search);
    const matchesStatus =
      statusFilter === "todas" ||
      (statusFilter === "pendientes" && !mora.EstadoMora) ||
      (statusFilter === "pagadas" && mora.EstadoMora);

    return matchesSearch && matchesStatus;
  });
}

function renderMorasTable(moras) {
  const fragment = document.createDocumentFragment();

  moras.forEach((mora, index) => {
    const factura = mora.factura_detalle || {};
    const row = document.createElement("tr");

    row.append(
      createCell(index + 1, true),
      createCell(formatInvoiceCode(factura.CodigoFact), true),
      createCell(getInvoiceCustomer(factura)),
      createCell(formatDateTime(mora.Fecha_Inicio, mora.Hora_Inicio)),
      createCell(formatDateTime(mora.Fecha_Final, mora.Hora_Final)),
      createCell(countMoraDays(mora)),
      createCell(formatMoney(mora.Monto_Mora), true),
      createStatusCell(mora.EstadoMora ? "Pagada" : "Pendiente"),
      createActionCell(mora)
    );

    fragment.appendChild(row);
  });

  if (!moras.length) {
    renderTableMessage("No hay moras que coincidan con los filtros.");
    return;
  }

  moraElements.table.replaceChildren(fragment);
}

function createActionCell(mora) {
  const cell = document.createElement("td");
  const actions = document.createElement("span");
  const actionLink = document.createElement("a");

  actions.className = "table-actions";
  actionLink.className = "icon-button";
  actionLink.href = `pagos.html?factura=${mora.FacturaId}`;
  actionLink.title = mora.EstadoMora ? "Ver pago asociado" : "Registrar pago";
  actionLink.setAttribute("aria-label", actionLink.title);
  actionLink.innerHTML = mora.EstadoMora
    ? '<i class="fa-solid fa-receipt" aria-hidden="true"></i>'
    : '<i class="fa-solid fa-credit-card" aria-hidden="true"></i>';

  actions.appendChild(actionLink);
  cell.appendChild(actions);
  return cell;
}

function getInvoiceCustomer(factura) {
  const customer = factura?.cliente_detalle || factura?.contrato_detalle?.cliente_detalle;
  return customer ? `${customer.Nombre} ${customer.Apellido || ""}`.trim() : "Sin cliente";
}

function createCell(content, strong = false) {
  const cell = document.createElement("td");
  if (strong) {
    const strongElement = document.createElement("strong");
    strongElement.textContent = content || "";
    cell.appendChild(strongElement);
    return cell;
  }

  cell.textContent = content || "";
  return cell;
}

function createStatusCell(status) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = `status ${status === "Pagada" ? "paid" : "pending"}`;
  badge.textContent = status;
  cell.appendChild(badge);
  return cell;
}

function renderTableMessage(message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 9;
  cell.className = "muted-cell";
  cell.textContent = message;
  row.appendChild(cell);
  moraElements.table.replaceChildren(row);
}

function countMoraDays(mora) {
  const start = new Date(`${mora.Fecha_Inicio}T00:00:00`);
  const end = new Date(`${mora.Fecha_Final}T00:00:00`);
  const diff = Math.round((end - start) / 86400000);
  return Math.max(1, diff);
}

function formatInvoiceCode(code) {
  return `FAC-${String(Number(code) || 0).padStart(6, "0")}`;
}

function formatDateTime(dateValue, timeValue) {
  if (!dateValue) {
    return "Sin fecha";
  }

  return new Date(`${dateValue}T${timeValue || "00:00:00"}`).toLocaleString("es-NI", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatMoney(value) {
  return `C$ ${Number(value || 0).toLocaleString("es-NI", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function formatApiError(data, status) {
  if (!data) {
    return `La API respondio con estado ${status}.`;
  }

  return Object.entries(data)
    .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join(" | ");
}

function setBusy(isBusy) {
  moraElements.refreshButton.disabled = isBusy;
}
