const API_ORIGIN =
  window.location.protocol === "http:" && window.location.port === "8000"
    ? window.location.origin
    : "http://127.0.0.1:8000";
const API_BASE = `${API_ORIGIN}/api`;
const IVA_RATE = 0;

const invoiceItems = [];
const apiState = {
  usuarios: [],
  clientes: [],
  tiposContrato: [],
  contratos: [],
  servicios: [],
  facturas: [],
  pagos: [],
  nextCode: 1001,
  lastInvoice: null,
  editingInvoiceId: null,
  editingOriginalDetailIds: [],
  historyFilter: "Todas"
};

const elements = {
  invoiceCode: document.querySelector("#invoiceCode"),
  selectedCustomer: document.querySelector("#selectedCustomer"),
  customerSelect: document.querySelector("#customerSelect"),
  contractSelect: document.querySelector("#contractSelect"),
  serviceSelect: document.querySelector("#serviceSelect"),
  quantityInput: document.querySelector("#quantityInput"),
  discountInput: document.querySelector("#discountInput"),
  addServiceButton: document.querySelector("#addServiceButton"),
  saveDraftButton: document.querySelector("#saveDraftButton"),
  issueInvoiceButton: document.querySelector("#issueInvoiceButton"),
  previewButton: document.querySelector("#previewButton"),
  printButton: document.querySelector("#printButton"),
  issueDateInput: document.querySelector("#issueDateInput"),
  dueDateInput: document.querySelector("#dueDateInput"),
  statusSelect: document.querySelector("#statusSelect"),
  observationInput: document.querySelector("#observationInput"),
  printPreviewSection: document.querySelector("#printPreviewSection"),
  invoiceDetailTable: document.querySelector("#invoiceDetailTable"),
  invoiceHistoryTable: document.querySelector("#invoiceHistoryTable"),
  subtotalValue: document.querySelector("#subtotalValue"),
  ivaValue: document.querySelector("#ivaValue"),
  discountValue: document.querySelector("#discountValue"),
  totalValue: document.querySelector("#totalValue"),
  totalCard: document.querySelector("#totalCard"),
  previewInvoiceCode: document.querySelector("#previewInvoiceCode"),
  previewStatus: document.querySelector("#previewStatus"),
  previewCustomer: document.querySelector("#previewCustomer"),
  previewCustomerEmail: document.querySelector("#previewCustomerEmail"),
  previewCustomerAddress: document.querySelector("#previewCustomerAddress"),
  previewIssueDate: document.querySelector("#previewIssueDate"),
  previewDueDate: document.querySelector("#previewDueDate"),
  previewContract: document.querySelector("#previewContract"),
  previewItemsTable: document.querySelector("#previewItemsTable"),
  previewObservation: document.querySelector("#previewObservation"),
  previewSubtotal: document.querySelector("#previewSubtotal"),
  previewIva: document.querySelector("#previewIva"),
  previewDiscount: document.querySelector("#previewDiscount"),
  previewTotal: document.querySelector("#previewTotal"),
  invoiceStatusFilter: document.querySelector("#invoiceStatusFilter")
};

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

  cell.textContent = content;
  return cell;
}

function createStatusCell(status) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");
  const statusClasses = {
    Pagada: "paid",
    Pendiente: "pending",
    Vencida: "overdue",
    Anulada: "neutral"
  };

  badge.className = `status ${statusClasses[status] || "neutral"}`;
  badge.textContent = status;
  cell.appendChild(badge);
  return cell;
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

function asList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  return Array.isArray(data?.results) ? data.results : [];
}

function formatoMoneda(valor) {
  return `C$ ${Number(valor || 0).toLocaleString("es-NI", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function formatInvoiceCode(code) {
  return `FAC-${String(Number(code) || 0).padStart(6, "0")}`;
}

function parseInvoiceCode(label) {
  const match = String(label || "").match(/\d+/);
  return match ? Number(match[0]) : apiState.nextCode;
}

function toDateInputValue(date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function toInputDateOnly(value) {
  if (!value) {
    return "";
  }

  const dateText = String(value);
  if (/^\d{4}-\d{2}-\d{2}/.test(dateText)) {
    return dateText.slice(0, 10);
  }

  return toDateInputValue(new Date(value));
}

function toApiDate(dateValue) {
  return toInputDateOnly(dateValue);
}

function toApiTime(dateValue) {
  const value = String(dateValue || "");
  const timeMatch = value.match(/T(\d{2}:\d{2})(?::(\d{2}))?/);

  if (!timeMatch) {
    return "00:00:00";
  }

  return `${timeMatch[1]}:${timeMatch[2] || "00"}`;
}

function toLocalDateTime(fecha, hora = "00:00:00") {
  if (!fecha) {
    return null;
  }

  return new Date(`${toInputDateOnly(fecha)}T${hora || "00:00:00"}`);
}

function formatDate(dateValue) {
  if (!dateValue) {
    return "Sin fecha";
  }

  return new Date(dateValue).toLocaleDateString("es-NI", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
}

function getNextInvoiceCode() {
  const codes = apiState.facturas
    .map((factura) => Number(factura.CodigoFact))
    .filter((codigo) => Number.isFinite(codigo));

  return (codes.length ? Math.max(...codes) : 1000) + 1;
}

function fillSelect(select, options, getValue, getLabel) {
  const fragment = document.createDocumentFragment();

  options.forEach((option) => {
    const item = document.createElement("option");
    item.value = getValue(option);
    item.textContent = getLabel(option);
    fragment.appendChild(item);
  });

  select.replaceChildren(fragment);
}

function getSelectedCustomer() {
  return apiState.clientes.find((cliente) => cliente.id === Number(elements.customerSelect.value));
}

function getActiveCustomers() {
  return apiState.clientes.filter((cliente) => Boolean(cliente.Estado));
}

function getSelectedTipoContrato() {
  return apiState.tiposContrato.find((tipo) => tipo.id === Number(elements.contractSelect.value));
}

function getSelectedService() {
  return apiState.servicios.find((servicio) => servicio.id === Number(elements.serviceSelect.value));
}

function updateContracts() {
  const customer = getSelectedCustomer();
  elements.selectedCustomer.textContent = customer
    ? `${customer.Nombre} ${customer.Apellido}`.trim()
    : "Sin cliente";
}

function updateCodeCard() {
  apiState.nextCode = getNextInvoiceCode();
  elements.invoiceCode.textContent = formatInvoiceCode(apiState.nextCode);
}

function updateDefaultDates() {
  const today = new Date();
  elements.issueDateInput.value = toDateInputValue(today);
  updateDueDateFromContract();
}

function isMonthlyContract(tipoContrato) {
  return String(tipoContrato?.Nombre || "").trim().toLowerCase() === "servicio mensual";
}

function calculateDueDate(issueDateValue, tipoContrato) {
  const issueDate = issueDateValue ? new Date(`${issueDateValue}T00:00:00`) : new Date();
  const dueDate = new Date(issueDate);

  if (isMonthlyContract(tipoContrato)) {
    dueDate.setDate(dueDate.getDate() + 30);
  }

  return toDateInputValue(dueDate);
}

function updateDueDateFromContract() {
  if (apiState.editingInvoiceId) {
    return;
  }

  elements.dueDateInput.value = calculateDueDate(
    elements.issueDateInput.value,
    getSelectedTipoContrato()
  );
}

function addService() {
  const service = getSelectedService();
  const cantidad = Number(elements.quantityInput.value || 1);

  if (!service || cantidad < 1) {
    alert("Selecciona un servicio y una cantidad valida.");
    return;
  }

  const subtotal = cantidad * Number(service.Precio || 0);
  const iva = subtotal * IVA_RATE;
  const total = subtotal + iva;

  invoiceItems.push({
    servicioId: service.id,
    codigo: `SERV-${String(service.id).padStart(3, "0")}`,
    nombre: service.Nombre_Servicio,
    cantidad,
    precio: Number(service.Precio || 0),
    subtotal,
    descuento: 0,
    iva,
    total
  });

  elements.quantityInput.value = 1;
  elements.discountInput.value = 0;
  renderInvoiceItems();
  renderPrintPreview();
}

function renderInvoiceItems() {
  const fragment = document.createDocumentFragment();

  invoiceItems.forEach((item, index) => {
    const row = document.createElement("tr");
    const actionCell = document.createElement("td");
    const actionWrap = document.createElement("span");
    const deleteButton = document.createElement("button");

    actionWrap.className = "table-actions";
    deleteButton.className = "icon-button";
    deleteButton.type = "button";
    deleteButton.setAttribute("aria-label", `Quitar ${item.nombre}`);
    deleteButton.innerHTML = '<i class="fa-solid fa-trash" aria-hidden="true"></i>';
    deleteButton.addEventListener("click", () => {
      invoiceItems.splice(index, 1);
      renderInvoiceItems();
      renderPrintPreview();
    });

    actionWrap.appendChild(deleteButton);
    actionCell.appendChild(actionWrap);

    row.append(
      createCell(item.codigo, { strong: true }),
      createCell(item.nombre),
      createCell(item.cantidad),
      createCell(formatoMoneda(item.precio)),
      createCell(formatoMoneda(item.iva)),
      createCell(formatoMoneda(item.total), { strong: true }),
      actionCell
    );

    fragment.appendChild(row);
  });

  if (!invoiceItems.length) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");

    emptyCell.colSpan = 7;
    emptyCell.className = "muted-cell";
    emptyCell.textContent = "Aun no hay servicios agregados a la factura.";
    emptyRow.appendChild(emptyCell);
    fragment.appendChild(emptyRow);
  }

  elements.invoiceDetailTable.replaceChildren(fragment);
  updateTotals();
}

function updateTotals() {
  const totals = invoiceItems.reduce(
    (accumulator, item) => {
      accumulator.subtotal += item.subtotal;
      accumulator.iva += item.iva;
      accumulator.descuento += item.descuento;
      accumulator.total += item.total;
      return accumulator;
    },
    { subtotal: 0, iva: 0, descuento: 0, total: 0 }
  );

  elements.subtotalValue.textContent = formatoMoneda(totals.subtotal);
  elements.ivaValue.textContent = formatoMoneda(totals.iva);
  elements.discountValue.textContent = formatoMoneda(totals.descuento);
  elements.totalValue.textContent = formatoMoneda(totals.total);
  elements.totalCard.textContent = formatoMoneda(totals.total);

  return totals;
}

function getFirstUserId() {
  return Number(apiState.usuarios[0]?.id || 1);
}

async function ensureContractForInvoice(customer, tipoContrato) {
  const existing = apiState.contratos.find((contrato) => {
    return (
      Number(contrato.ClienteId) === Number(customer.id) &&
      Number(contrato.TipoContratoId) === Number(tipoContrato.id) &&
      Boolean(contrato.EstadoContrato)
    );
  });

  if (existing) {
    return existing;
  }

  const fechaInicio = elements.issueDateInput.value;
  const fechaFin = elements.dueDateInput.value;
  const contrato = await fetchJson(`${API_BASE}/contratos/`, {
    method: "POST",
    body: JSON.stringify({
      ClienteId: customer.id,
      TipoContratoId: tipoContrato.id,
      Fecha_Inc: fechaInicio,
      Fecha_Fin: fechaFin,
      EstadoContrato: true,
      Descripcion: tipoContrato.Descripcion || tipoContrato.Nombre
    })
  });

  apiState.contratos.unshift(contrato);
  return contrato;
}

function getDetailPayload(facturaId, item) {
  return {
    FacturaId: facturaId,
    ServicioId: item.servicioId,
    PrecioVenta: Math.round(Number(item.precio || 0)),
    Cantidad: item.cantidad
  };
}

async function syncInvoiceDetails(facturaId) {
  const keptDetailIds = new Set();

  for (const item of invoiceItems) {
    const payload = getDetailPayload(facturaId, item);

    if (item.detalleId) {
      await fetchJson(`${API_BASE}/detalles-factura/${item.detalleId}/`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      keptDetailIds.add(Number(item.detalleId));
      continue;
    }

    await fetchJson(`${API_BASE}/detalles-factura/`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  const detailsToDelete = apiState.editingOriginalDetailIds.filter(
    (detailId) => !keptDetailIds.has(Number(detailId))
  );

  for (const detailId of detailsToDelete) {
    await fetchJson(`${API_BASE}/detalles-factura/${detailId}/`, {
      method: "DELETE"
    });
  }
}

async function saveInvoice(statusOverride) {
  const customer = getSelectedCustomer();
  const tipoContrato = getSelectedTipoContrato();

  if (!customer) {
    alert("Selecciona un cliente antes de guardar la factura.");
    return;
  }

  if (!customer.Estado) {
    alert("El cliente seleccionado esta inactivo y no puede facturarse.");
    return;
  }

  if (!tipoContrato) {
    alert("Selecciona un tipo de contrato antes de guardar la factura.");
    return;
  }

  if (!invoiceItems.length) {
    alert("Agrega al menos un servicio antes de guardar la factura.");
    return;
  }

  const code = parseInvoiceCode(elements.invoiceCode.textContent);

  setBusy(true);

  try {
    const contract = await ensureContractForInvoice(customer, tipoContrato);
    const isEditing = Boolean(apiState.editingInvoiceId);
    const invoicePayload = {
      UsuarioId: getFirstUserId(),
      ContratoId: contract.id,
      CodigoFact: code
    };

    if (!isEditing) {
      invoicePayload.Fecha_Emision = toApiDate(elements.issueDateInput.value);
      invoicePayload.Hora_Emision = toApiTime(elements.issueDateInput.value);
    }

    const factura = await fetchJson(
      isEditing ? `${API_BASE}/facturas/${apiState.editingInvoiceId}/` : `${API_BASE}/facturas/`,
      {
        method: isEditing ? "PATCH" : "POST",
        body: JSON.stringify(invoicePayload)
      }
    );

    await syncInvoiceDetails(factura.id);

    const facturaFinal = await fetchJson(`${API_BASE}/facturas/${factura.id}/`);
    apiState.lastInvoice = facturaFinal;

    if (isEditing) {
      apiState.facturas = apiState.facturas.map((item) =>
        Number(item.id) === Number(facturaFinal.id) ? facturaFinal : item
      );
    } else {
      apiState.facturas.unshift(facturaFinal);
    }

    const selectedStatus = statusOverride || elements.statusSelect.value;

    if (selectedStatus === "Pagada") {
      await markInvoiceAsPaid(facturaFinal);
    }

    applyInvoiceToPreview(facturaFinal, selectedStatus);
    clearInvoiceForm();
    renderInvoiceHistory();
    alert(
      `Factura ${formatInvoiceCode(facturaFinal.CodigoFact)} ${
        isEditing ? "actualizada" : "guardada"
      } en SQL Server.`
    );
  } catch (error) {
    alert(`No se pudo ${apiState.editingInvoiceId ? "actualizar" : "generar"} la factura: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  [
    elements.saveDraftButton,
    elements.issueInvoiceButton,
    elements.addServiceButton,
    elements.previewButton,
    elements.printButton
  ].forEach((button) => {
    button.disabled = isBusy;
  });
}

function setInvoiceMode(isEditing) {
  elements.issueDateInput.disabled = isEditing;
  elements.dueDateInput.disabled = true;

  if (isEditing) {
    elements.saveDraftButton.innerHTML =
      '<i class="fa-solid fa-xmark" aria-hidden="true"></i> Cancelar edición';
    elements.issueInvoiceButton.innerHTML =
      '<i class="fa-solid fa-floppy-disk" aria-hidden="true"></i> Actualizar factura';
    return;
  }

  elements.saveDraftButton.innerHTML =
    '<i class="fa-solid fa-floppy-disk" aria-hidden="true"></i> Guardar borrador';
  elements.issueInvoiceButton.innerHTML =
    '<i class="fa-solid fa-file-circle-plus" aria-hidden="true"></i> Agregar factura';
}

function clearInvoiceForm() {
  invoiceItems.splice(0, invoiceItems.length);
  apiState.editingInvoiceId = null;
  apiState.editingOriginalDetailIds = [];
  updateCodeCard();
  updateDefaultDates();
  elements.quantityInput.value = 1;
  elements.discountInput.value = 0;
  elements.statusSelect.value = "Pendiente";
  setInvoiceMode(false);
  renderInvoiceItems();
  renderPrintPreview();
}

function getInvoiceStatus(factura) {
  const estadoBackend = factura.estado_detalle?.estado;
  if (estadoBackend) {
    return estadoBackend;
  }

  if (isInvoicePaid(factura)) {
    return "Pagada";
  }

  const dueDate = toLocalDateTime(factura.Fecha_Vencimiento, factura.Hora_Vencimiento);
  if (dueDate && dueDate < new Date()) {
    return "Vencida";
  }

  return "Pendiente";
}

function getPaymentForInvoice(facturaId) {
  const payments = apiState.pagos.filter((pago) => Number(pago.FacturaId) === Number(facturaId));
  return payments.find((pago) => Boolean(pago.EstadoPago)) || payments[0] || null;
}

function isInvoicePaid(factura) {
  return apiState.pagos.some(
    (pago) => Number(pago.FacturaId) === Number(factura.id) && Boolean(pago.EstadoPago)
  );
}

function getNextReceiptNumber() {
  const numbers = apiState.pagos
    .map((pago) => Number(pago.NumeroRecibo))
    .filter((number) => Number.isFinite(number));
  return (numbers.length ? Math.max(...numbers) : 0) + 1;
}

function filterInvoicesForHistory(invoices) {
  if (apiState.historyFilter === "Todas") {
    return invoices;
  }

  return invoices.filter((factura) => getInvoiceStatus(factura) === apiState.historyFilter);
}

function getInvoiceCustomer(factura) {
  return factura.contrato_detalle?.cliente_detalle || null;
}

function renderInvoiceHistory() {
  const fragment = document.createDocumentFragment();
  const invoices = filterInvoicesForHistory(
    apiState.facturas.slice().sort((a, b) => Number(b.CodigoFact) - Number(a.CodigoFact))
  );

  invoices.forEach((factura) => {
    const row = document.createElement("tr");
    const customer = getInvoiceCustomer(factura);

    row.append(
      createCell(formatInvoiceCode(factura.CodigoFact), { strong: true }),
      createCell(customer ? `${customer.Nombre} ${customer.Apellido}`.trim() : "Sin cliente"),
      createCell(formatDate(factura.Fecha_Emision)),
      createCell(formatDate(factura.Fecha_Vencimiento)),
      createCell(formatoMoneda(factura.Monto_Total), { strong: true }),
      createStatusCell(getInvoiceStatus(factura)),
      createInvoiceActionCell(factura)
    );

    fragment.appendChild(row);
  });

  if (!invoices.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 7;
    cell.className = "muted-cell";
    cell.textContent =
      apiState.historyFilter === "Todas"
        ? "Aun no hay facturas registradas."
        : `No hay facturas con estado ${apiState.historyFilter.toLowerCase()}.`;
    row.appendChild(cell);
    fragment.appendChild(row);
  }

  elements.invoiceHistoryTable.replaceChildren(fragment);
}

async function markInvoiceAsPaid(factura) {
  const existing = getPaymentForInvoice(factura.id);
  const payload = {
    Fecha_Pago: new Date().toISOString(),
    Monto_Pagado: Number(factura.Monto_Total || 0),
    EstadoPago: true,
    MetodoPago: existing ? Boolean(existing.MetodoPago) : false,
    FacturaId: factura.id,
    NumeroRecibo: existing?.NumeroRecibo || getNextReceiptNumber()
  };

  const saved = await fetchJson(
    existing ? `${API_BASE}/pagos/${existing.id}/` : `${API_BASE}/pagos/`,
    {
      method: existing ? "PUT" : "POST",
      body: JSON.stringify(payload)
    }
  );

  if (existing) {
    apiState.pagos = apiState.pagos.map((pago) => (Number(pago.id) === Number(saved.id) ? saved : pago));
    return;
  }

  apiState.pagos.unshift(saved);
}

function detailToInvoiceItem(detail) {
  const service = detail.servicio_detalle || {};
  const cantidad = Number(detail.Cantidad || 1);
  const precio = Number(detail.PrecioVenta ?? service.Precio ?? 0);
  const subtotal = Number(detail.Subtotal ?? precio * cantidad);

  return {
    detalleId: detail.id,
    servicioId: Number(detail.ServicioId),
    codigo: `SERV-${String(detail.ServicioId).padStart(3, "0")}`,
    nombre: service.Nombre_Servicio || "Servicio",
    cantidad,
    precio,
    subtotal,
    descuento: 0,
    iva: 0,
    total: subtotal
  };
}

function loadInvoiceIntoForm(factura) {
  const customer = getInvoiceCustomer(factura);
  const contract = factura.contrato_detalle || {};
  const tipoContratoId = contract.TipoContratoId || contract.tipo_contrato_detalle?.id;
  const details = factura.detalles || [];

  apiState.lastInvoice = factura;
  apiState.editingInvoiceId = factura.id;
  apiState.editingOriginalDetailIds = details.map((detail) => Number(detail.id));

  elements.invoiceCode.textContent = formatInvoiceCode(factura.CodigoFact);
  elements.customerSelect.value = customer?.id || "";
  elements.contractSelect.value = tipoContratoId || "";
  elements.issueDateInput.value = toInputDateOnly(factura.Fecha_Emision);
  elements.dueDateInput.value = toInputDateOnly(factura.Fecha_Vencimiento);
  elements.statusSelect.value = getInvoiceStatus(factura);

  invoiceItems.splice(0, invoiceItems.length, ...details.map(detailToInvoiceItem));

  updateContracts();
  setInvoiceMode(true);
  renderInvoiceItems();
  renderPrintPreview();
  elements.customerSelect.scrollIntoView({ behavior: "smooth", block: "center" });
}

function createInvoiceActionCell(factura) {
  const cell = document.createElement("td");
  const actions = document.createElement("span");
  const previewButton = document.createElement("button");
  const editButton = document.createElement("button");

  actions.className = "table-actions";
  previewButton.className = "icon-button";
  previewButton.type = "button";
  previewButton.title = "Ver factura";
  previewButton.setAttribute("aria-label", `Ver ${formatInvoiceCode(factura.CodigoFact)}`);
  previewButton.innerHTML = '<i class="fa-solid fa-eye" aria-hidden="true"></i>';
  previewButton.addEventListener("click", async () => {
    try {
      const detail = await fetchJson(`${API_BASE}/facturas/${factura.id}/`);
      apiState.lastInvoice = detail;
      applyInvoiceToPreview(detail, getInvoiceStatus(detail));
      revealPrintPreview();
    } catch (error) {
      alert(`No se pudo cargar la factura: ${error.message}`);
    }
  });

  editButton.className = "icon-button";
  editButton.type = "button";
  editButton.title = "Editar factura";
  editButton.setAttribute("aria-label", `Editar ${formatInvoiceCode(factura.CodigoFact)}`);
  editButton.innerHTML = '<i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>';
  editButton.addEventListener("click", async () => {
    try {
      const detail = await fetchJson(`${API_BASE}/facturas/${factura.id}/`);
      loadInvoiceIntoForm(detail);
    } catch (error) {
      alert(`No se pudo preparar la factura para edición: ${error.message}`);
    }
  });

  actions.append(previewButton, editButton);
  cell.appendChild(actions);
  return cell;
}

function getSelectedContractLabel() {
  const selectedOption = elements.contractSelect.selectedOptions[0];
  return selectedOption ? selectedOption.textContent : "Sin tipo";
}

function renderPreviewItems() {
  const fragment = document.createDocumentFragment();

  invoiceItems.forEach((item) => {
    const row = document.createElement("tr");

    row.append(
      createCell(item.codigo, { strong: true }),
      createCell(item.nombre),
      createCell(item.cantidad),
      createCell(formatoMoneda(item.precio)),
      createCell(formatoMoneda(item.iva)),
      createCell(formatoMoneda(item.total), { strong: true })
    );

    fragment.appendChild(row);
  });

  if (!invoiceItems.length) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");

    emptyCell.colSpan = 6;
    emptyCell.textContent = "Sin servicios agregados.";
    emptyRow.appendChild(emptyCell);
    fragment.appendChild(emptyRow);
  }

  elements.previewItemsTable.replaceChildren(fragment);
}

function renderPrintPreview() {
  const customer = getSelectedCustomer();
  const totals = updateTotals();

  elements.previewInvoiceCode.textContent = elements.invoiceCode.textContent;
  elements.previewStatus.textContent = elements.statusSelect.value;
  elements.previewCustomer.textContent = customer
    ? `${customer.Nombre} ${customer.Apellido}`.trim()
    : "Cliente no seleccionado";
  elements.previewCustomerEmail.textContent = customer ? customer.Correo : "Sin correo";
  elements.previewCustomerAddress.textContent = customer ? customer.Direccion : "Sin dirección";
  elements.previewIssueDate.textContent = formatDate(elements.issueDateInput.value);
  elements.previewDueDate.textContent = formatDate(elements.dueDateInput.value);
  elements.previewContract.textContent = getSelectedContractLabel();
  elements.previewObservation.textContent = elements.observationInput.value || "Sin observación";
  elements.previewSubtotal.textContent = formatoMoneda(totals.subtotal);
  elements.previewIva.textContent = formatoMoneda(totals.iva);
  elements.previewDiscount.textContent = formatoMoneda(totals.descuento);
  elements.previewTotal.textContent = formatoMoneda(totals.total);

  renderPreviewItems();
}

function applyInvoiceToPreview(factura, status = "Pendiente") {
  const customer = getInvoiceCustomer(factura) || {};
  const contract = factura.contrato_detalle || {};
  const details = factura.detalles || [];
  const subtotal = details.reduce((total, detail) => total + Number(detail.Subtotal || 0), 0);

  elements.previewInvoiceCode.textContent = formatInvoiceCode(factura.CodigoFact);
  elements.previewStatus.textContent = status;
  elements.previewCustomer.textContent = `${customer.Nombre || ""} ${customer.Apellido || ""}`.trim() || "Sin cliente";
  elements.previewCustomerEmail.textContent = customer.Correo || "Sin correo";
  elements.previewCustomerAddress.textContent = customer.Direccion || "Sin dirección";
  elements.previewIssueDate.textContent = formatDate(factura.Fecha_Emision);
  elements.previewDueDate.textContent = formatDate(factura.Fecha_Vencimiento);
  elements.previewContract.textContent = `CONT-${String(contract.id || "").padStart(3, "0")}`;
  elements.previewObservation.textContent = elements.observationInput.value || "Factura generada desde SoftFactur.";
  elements.previewSubtotal.textContent = formatoMoneda(subtotal);
  elements.previewIva.textContent = formatoMoneda(0);
  elements.previewDiscount.textContent = formatoMoneda(0);
  elements.previewTotal.textContent = formatoMoneda(factura.Monto_Total);

  const fragment = document.createDocumentFragment();
  details.forEach((detail) => {
    const service = detail.servicio_detalle || {};
    const row = document.createElement("tr");
    row.append(
      createCell(`SERV-${String(detail.ServicioId).padStart(3, "0")}`, { strong: true }),
      createCell(service.Nombre_Servicio || "Servicio"),
      createCell(detail.Cantidad),
      createCell(formatoMoneda(detail.PrecioVenta)),
      createCell(formatoMoneda(0)),
      createCell(formatoMoneda(detail.Subtotal), { strong: true })
    );
    fragment.appendChild(row);
  });
  elements.previewItemsTable.replaceChildren(fragment);
  elements.printPreviewSection.classList.remove("is-hidden");
}

function revealPrintPreview() {
  elements.printPreviewSection.classList.remove("is-hidden");
  elements.printPreviewSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showPrintPreview() {
  renderPrintPreview();
  revealPrintPreview();
}

async function loadApiData() {
  const endpoints = [
    ["usuarios", `${API_BASE}/usuarios/`],
    ["clientes", `${API_BASE}/clientes/?ordering=Nombre`],
    ["tiposContrato", `${API_BASE}/tipos-contrato/?ordering=Nombre`],
    ["contratos", `${API_BASE}/contratos/?activo=true&ordering=id`],
    ["servicios", `${API_BASE}/servicios/?ordering=Nombre_Servicio`],
    ["facturas", `${API_BASE}/facturas/?ordering=-CodigoFact`],
    ["pagos", `${API_BASE}/pagos/?ordering=-Fecha_Pago`]
  ];
  const results = await Promise.allSettled(endpoints.map(([, url]) => fetchJson(url)));
  const errors = [];

  results.forEach((result, index) => {
    const key = endpoints[index][0];

    if (result.status === "fulfilled") {
      apiState[key] = asList(result.value);
      return;
    }

    apiState[key] = [];
    errors.push(`${key}: ${result.reason.message}`);
  });

  if (errors.length) {
    console.warn("Algunos datos de facturas no se pudieron cargar.", errors);
  }
}

function initUi() {
  updateDefaultDates();
  updateCodeCard();
  elements.dueDateInput.disabled = true;

  fillSelect(
    elements.customerSelect,
    getActiveCustomers(),
    (cliente) => cliente.id,
    (cliente) => `${cliente.Nombre} ${cliente.Apellido}`.trim()
  );

  fillSelect(
    elements.contractSelect,
    apiState.tiposContrato,
    (tipo) => tipo.id,
    (tipo) => tipo.Nombre
  );
  updateDueDateFromContract();

  fillSelect(
    elements.serviceSelect,
    apiState.servicios,
    (servicio) => servicio.id,
    (servicio) => `SERV-${String(servicio.id).padStart(3, "0")} - ${servicio.Nombre_Servicio}`
  );

  updateContracts();
  renderInvoiceItems();
  renderInvoiceHistory();
  renderPrintPreview();

  elements.discountInput.disabled = true;
  elements.discountInput.title = "El descuento no esta disponible en el modelo actual de detalle de factura.";

  if (elements.invoiceStatusFilter) {
    elements.invoiceStatusFilter.value = apiState.historyFilter;
  }
}

async function initInvoicePage() {
  try {
    await loadApiData();
    initUi();

    elements.customerSelect.addEventListener("change", () => {
      updateContracts();
      renderPrintPreview();
    });
    elements.contractSelect.addEventListener("change", () => {
      updateDueDateFromContract();
      renderPrintPreview();
    });
    elements.issueDateInput.addEventListener("change", () => {
      updateDueDateFromContract();
      renderPrintPreview();
    });
    elements.invoiceStatusFilter?.addEventListener("change", () => {
      apiState.historyFilter = elements.invoiceStatusFilter.value;
      renderInvoiceHistory();
    });
    elements.addServiceButton.addEventListener("click", addService);
    elements.saveDraftButton.addEventListener("click", () => {
      if (apiState.editingInvoiceId) {
        clearInvoiceForm();
        return;
      }

      saveInvoice("Pendiente");
    });
    elements.issueInvoiceButton.addEventListener("click", () => saveInvoice());
    elements.previewButton.addEventListener("click", showPrintPreview);
    elements.printButton.addEventListener("click", () => {
      if (apiState.lastInvoice) {
        applyInvoiceToPreview(apiState.lastInvoice, elements.previewStatus.textContent);
      } else {
        renderPrintPreview();
      }
      window.print();
    });
  } catch (error) {
    alert(`No se pudo conectar el módulo de facturas: ${error.message}`);
  }
}

if (elements.invoiceDetailTable) {
  initInvoicePage();
}
