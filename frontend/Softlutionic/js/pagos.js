const API_ORIGIN =
  window.location.protocol === "http:" || window.location.protocol === "https:"
    ? window.location.origin
    : "http://127.0.0.1:8000";
const API_BASE = `${API_ORIGIN}/api`;

const paymentState = {
  facturas: [],
  pagos: [],
  moras: [],
  editingPaymentId: null
};

const paymentElements = {
  paymentsTotal: document.querySelector("#paymentsTotal"),
  pendingTotal: document.querySelector("#pendingTotal"),
  pendingTable: document.querySelector("#pendingInvoicesTable"),
  paymentsTable: document.querySelector("#paymentsTable"),
  invoiceSelect: document.querySelector("#paymentInvoiceSelect"),
  receiptInput: document.querySelector("#receiptInput"),
  dateInput: document.querySelector("#paymentDateInput"),
  amountInput: document.querySelector("#paymentAmountInput"),
  methodSelect: document.querySelector("#paymentMethodSelect"),
  statusSelect: document.querySelector("#paymentStatusSelect"),
  clearButton: document.querySelector("#clearPaymentButton"),
  saveButton: document.querySelector("#savePaymentButton"),
  selectedCustomer: document.querySelector("#selectedPaymentCustomer"),
  selectedInvoice: document.querySelector("#selectedPaymentInvoice"),
  selectedAmount: document.querySelector("#selectedPaymentAmount"),
  selectedStatus: document.querySelector("#selectedPaymentStatus")
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", loadPaymentsPage);
} else {
  loadPaymentsPage();
}

async function loadPaymentsPage() {
  try {
    const [facturasResult, pagosResult, morasResult] = await Promise.allSettled([
      fetchJson(`${API_BASE}/facturas/?ordering=-Fecha_Emision,-Hora_Emision`),
      fetchJson(`${API_BASE}/pagos/?ordering=-Fecha_Pago`),
      fetchJson(`${API_BASE}/moras/?ordering=-Fecha_Inicio,-Hora_Inicio`)
    ]);

    if (facturasResult.status === "rejected" || pagosResult.status === "rejected") {
      throw facturasResult.reason || pagosResult.reason;
    }

    if (morasResult.status === "rejected") {
      console.warn("No se pudo cargar moras para sugerir el monto total.", morasResult.reason);
    }

    paymentState.facturas = asList(facturasResult.value);
    paymentState.pagos = asList(pagosResult.value);
    paymentState.moras = morasResult.status === "fulfilled" ? asList(morasResult.value) : [];
    renderPaymentsPage();
    initPaymentForm();
  } catch (error) {
    console.error("No se pudo cargar pagos desde la API.", error);
    renderTableMessage(paymentElements.pendingTable, 6, error.message);
    renderTableMessage(paymentElements.paymentsTable, 8, error.message);
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

function initPaymentForm() {
  if (!hasPaymentForm()) {
    return;
  }

  fillInvoiceSelect();

  const invoiceFromUrl = new URLSearchParams(window.location.search).get("factura");
  if (invoiceFromUrl && getInvoiceById(invoiceFromUrl)) {
    paymentElements.invoiceSelect.value = invoiceFromUrl;
  }

  if (!paymentElements.dateInput.value) {
    paymentElements.dateInput.value = toDateTimeLocal(new Date());
  }

  if (!paymentElements.receiptInput.value) {
    paymentElements.receiptInput.value = getNextReceiptNumber();
  }

  updateSelectedInvoiceSummary();
  bindPaymentEventsOnce();
}

function bindPaymentEventsOnce() {
  if (paymentElements.saveButton.dataset.bound === "true") {
    return;
  }

  paymentElements.invoiceSelect.addEventListener("change", () => {
    const factura = getSelectedInvoice();
    const existing = factura ? getPaymentForInvoice(factura.id) : null;

    if (!paymentState.editingPaymentId) {
      paymentElements.amountInput.value = factura ? getSuggestedPaymentAmount(factura).toFixed(2) : "";
      paymentElements.receiptInput.value = existing?.NumeroRecibo || getNextReceiptNumber();
      paymentElements.statusSelect.value = existing ? String(Boolean(existing.EstadoPago)) : "false";
      paymentElements.methodSelect.value = existing ? String(Boolean(existing.MetodoPago)) : "false";
    }

    updateSelectedInvoiceSummary();
  });

  paymentElements.clearButton.addEventListener("click", clearPaymentForm);
  paymentElements.saveButton.addEventListener("click", savePayment);
  paymentElements.saveButton.dataset.bound = "true";
}

function fillInvoiceSelect() {
  const fragment = document.createDocumentFragment();

  paymentState.facturas.forEach((factura) => {
    const option = document.createElement("option");
    option.value = factura.id;
    option.textContent = `${formatInvoiceCode(factura.CodigoFact)} - ${getInvoiceCustomer(factura)} - ${formatMoney(
      factura.Monto_Total
    )}`;
    fragment.appendChild(option);
  });

  paymentElements.invoiceSelect.replaceChildren(fragment);
}

function renderPaymentsPage() {
  const pendingInvoices = getPendingInvoices();

  paymentElements.paymentsTotal.textContent = paymentState.pagos.length;
  paymentElements.pendingTotal.textContent = pendingInvoices.length;
  renderPendingInvoices(pendingInvoices);
  renderPayments();

  if (hasPaymentForm()) {
    updateSelectedInvoiceSummary();
  }
}

function hasPaymentForm() {
  return Boolean(
    paymentElements.invoiceSelect &&
      paymentElements.receiptInput &&
      paymentElements.dateInput &&
      paymentElements.amountInput &&
      paymentElements.methodSelect &&
      paymentElements.statusSelect &&
      paymentElements.clearButton &&
      paymentElements.saveButton
  );
}

function getConfirmedPayment(facturaId) {
  return paymentState.pagos.find((pago) => {
    return Number(pago.FacturaId) === Number(facturaId) && Boolean(pago.EstadoPago);
  });
}

function getPaymentForInvoice(facturaId) {
  return paymentState.pagos.find((pago) => Number(pago.FacturaId) === Number(facturaId));
}

function getMoraForInvoice(facturaId) {
  return paymentState.moras.find((mora) => Number(mora.FacturaId) === Number(facturaId) && !mora.EstadoMora);
}

function getSuggestedPaymentAmount(factura) {
  const mora = getMoraForInvoice(factura.id);
  return Number(factura.Monto_Total || 0) + Number(mora?.Monto_Mora || 0);
}

function getPendingInvoices() {
  return paymentState.facturas.filter((factura) => !getConfirmedPayment(factura.id));
}

function renderPendingInvoices(invoices) {
  const fragment = document.createDocumentFragment();

  invoices.forEach((factura) => {
    const row = document.createElement("tr");
    const actionCell = document.createElement("td");
    const actions = document.createElement("span");
    const manageButton = document.createElement("button");
    const paidButton = document.createElement("button");

    actions.className = "table-actions";

    manageButton.className = "icon-button";
    manageButton.type = "button";
    manageButton.title = "Gestionar pago";
    manageButton.setAttribute("aria-label", `Gestionar pago de ${formatInvoiceCode(factura.CodigoFact)}`);
    manageButton.innerHTML = '<i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>';
    manageButton.addEventListener("click", () => loadInvoiceForPayment(factura));

    paidButton.className = "icon-button";
    paidButton.type = "button";
    paidButton.title = "Marcar pagada";
    paidButton.setAttribute("aria-label", `Marcar pagada ${formatInvoiceCode(factura.CodigoFact)}`);
    paidButton.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i>';
    paidButton.addEventListener("click", () => markInvoiceAsPaid(factura, paidButton));

    actions.append(manageButton, paidButton);
    actionCell.appendChild(actions);

    row.append(
      createCell(formatInvoiceCode(factura.CodigoFact), true),
      createCell(getInvoiceCustomer(factura)),
      createCell(formatDate(factura.Fecha_Vencimiento)),
      createCell(formatMoney(factura.Monto_Total), true),
      createStatusCell("Pendiente"),
      actionCell
    );
    fragment.appendChild(row);
  });

  if (!invoices.length) {
    renderTableMessage(paymentElements.pendingTable, 6, "No hay facturas pendientes de pago.");
    return;
  }

  paymentElements.pendingTable.replaceChildren(fragment);
}

function renderPayments() {
  const fragment = document.createDocumentFragment();

  paymentState.pagos.forEach((pago) => {
    const factura = pago.factura_detalle || getInvoiceById(pago.FacturaId) || {};
    const row = document.createElement("tr");
    row.append(
      createCell(`REC-${String(pago.NumeroRecibo).padStart(6, "0")}`, true),
      createCell(formatInvoiceCode(factura.CodigoFact)),
      createCell(getInvoiceCustomer(factura)),
      createCell(formatDate(pago.Fecha_Pago)),
      createCell(formatMoney(pago.Monto_Pagado), true),
      createCell(pago.metodo_descripcion || getMethodLabel(pago.MetodoPago)),
      createStatusCell(pago.EstadoPago ? "Pagada" : "Pendiente"),
      createPaymentActionCell(pago)
    );
    fragment.appendChild(row);
  });

  if (!paymentState.pagos.length) {
    renderTableMessage(paymentElements.paymentsTable, 8, "No hay pagos registrados.");
    return;
  }

  paymentElements.paymentsTable.replaceChildren(fragment);
}

function createPaymentActionCell(pago) {
  const cell = document.createElement("td");
  const actions = document.createElement("span");
  const editButton = document.createElement("button");
  const statusButton = document.createElement("button");

  actions.className = "table-actions";

  editButton.className = "icon-button";
  editButton.type = "button";
  editButton.title = "Editar pago";
  editButton.setAttribute("aria-label", `Editar recibo ${pago.NumeroRecibo}`);
  editButton.innerHTML = '<i class="fa-solid fa-pen-to-square" aria-hidden="true"></i>';
  editButton.addEventListener("click", () => loadPaymentIntoForm(pago));

  statusButton.className = "icon-button";
  statusButton.type = "button";
  statusButton.title = pago.EstadoPago ? "Cambiar a pendiente" : "Cambiar a pagado";
  statusButton.setAttribute("aria-label", statusButton.title);
  statusButton.innerHTML = pago.EstadoPago
    ? '<i class="fa-solid fa-rotate-left" aria-hidden="true"></i>'
    : '<i class="fa-solid fa-check" aria-hidden="true"></i>';
  statusButton.addEventListener("click", () => togglePaymentStatus(pago, statusButton));

  actions.append(editButton, statusButton);
  cell.appendChild(actions);
  return cell;
}

function loadInvoiceForPayment(factura) {
  const existing = getPaymentForInvoice(factura.id);

  if (existing) {
    loadPaymentIntoForm(existing);
    return;
  }

  paymentState.editingPaymentId = null;
  paymentElements.invoiceSelect.value = factura.id;
  paymentElements.receiptInput.value = getNextReceiptNumber();
  paymentElements.dateInput.value = toDateTimeLocal(new Date());
  paymentElements.amountInput.value = getSuggestedPaymentAmount(factura).toFixed(2);
  paymentElements.methodSelect.value = "false";
  paymentElements.statusSelect.value = "false";
  setPaymentMode(false);
  updateSelectedInvoiceSummary();
  paymentElements.invoiceSelect.scrollIntoView({ behavior: "smooth", block: "center" });
}

function loadPaymentIntoForm(pago) {
  paymentState.editingPaymentId = pago.id;
  paymentElements.invoiceSelect.value = pago.FacturaId;
  paymentElements.receiptInput.value = pago.NumeroRecibo;
  paymentElements.dateInput.value = toDateTimeLocal(pago.Fecha_Pago);
  paymentElements.amountInput.value = Number(pago.Monto_Pagado || 0).toFixed(2);
  paymentElements.methodSelect.value = String(Boolean(pago.MetodoPago));
  paymentElements.statusSelect.value = String(Boolean(pago.EstadoPago));
  setPaymentMode(true);
  updateSelectedInvoiceSummary();
  paymentElements.invoiceSelect.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function savePayment() {
  const factura = getSelectedInvoice();

  if (!factura) {
    alert("Selecciona una factura antes de guardar el pago.");
    return;
  }

  if (!paymentElements.receiptInput.value || Number(paymentElements.receiptInput.value) < 1) {
    alert("Ingresa un número de recibo válido.");
    return;
  }

  if (!paymentElements.dateInput.value) {
    alert("Selecciona la fecha y hora del pago.");
    return;
  }

  if (Number(paymentElements.amountInput.value) < 0) {
    alert("El monto pagado no puede ser negativo.");
    return;
  }

  const payload = getPaymentPayload(factura.id);
  const isEditing = Boolean(paymentState.editingPaymentId);

  setBusy(true);

  try {
    const saved = await fetchJson(
      isEditing ? `${API_BASE}/pagos/${paymentState.editingPaymentId}/` : `${API_BASE}/pagos/`,
      {
        method: isEditing ? "PUT" : "POST",
        body: JSON.stringify(payload)
      }
    );

    upsertPayment(saved);
    clearPaymentForm();
    await loadPaymentsPage();
    alert(`Pago ${isEditing ? "actualizado" : "registrado"} correctamente.`);
  } catch (error) {
    alert(`No se pudo guardar el pago: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

async function markInvoiceAsPaid(factura, button) {
  button.disabled = true;

  try {
    const existing = getPaymentForInvoice(factura.id);
    const payload = {
      Fecha_Pago: new Date().toISOString(),
      Monto_Pagado: Number(factura.Monto_Total || 0),
      EstadoPago: true,
      MetodoPago: existing ? Boolean(existing.MetodoPago) : false,
      FacturaId: factura.id,
      NumeroRecibo: existing?.NumeroRecibo || getNextReceiptNumber()
    };

    if (existing) {
      await fetchJson(`${API_BASE}/pagos/${existing.id}/`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
    } else {
      await fetchJson(`${API_BASE}/pagos/`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    await loadPaymentsPage();
    alert(`Pago confirmado para ${formatInvoiceCode(factura.CodigoFact)}.`);
  } catch (error) {
    alert(`No se pudo actualizar el pago: ${error.message}`);
    button.disabled = false;
  }
}

async function togglePaymentStatus(pago, button) {
  button.disabled = true;

  try {
    const payload = {
      Fecha_Pago: pago.Fecha_Pago,
      Monto_Pagado: pago.Monto_Pagado,
      EstadoPago: !pago.EstadoPago,
      MetodoPago: pago.MetodoPago,
      FacturaId: pago.FacturaId,
      NumeroRecibo: pago.NumeroRecibo
    };

    await fetchJson(`${API_BASE}/pagos/${pago.id}/`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });

    await loadPaymentsPage();
  } catch (error) {
    alert(`No se pudo cambiar el estado del pago: ${error.message}`);
    button.disabled = false;
  }
}

function getPaymentPayload(facturaId) {
  return {
    Fecha_Pago: toApiDateTime(paymentElements.dateInput.value),
    Monto_Pagado: Number(paymentElements.amountInput.value || 0),
    EstadoPago: paymentElements.statusSelect.value === "true",
    MetodoPago: paymentElements.methodSelect.value === "true",
    FacturaId: facturaId,
    NumeroRecibo: Number(paymentElements.receiptInput.value)
  };
}

function upsertPayment(payment) {
  const index = paymentState.pagos.findIndex((item) => Number(item.id) === Number(payment.id));

  if (index >= 0) {
    paymentState.pagos.splice(index, 1, payment);
    return;
  }

  paymentState.pagos.unshift(payment);
}

function clearPaymentForm() {
  paymentState.editingPaymentId = null;
  paymentElements.receiptInput.value = getNextReceiptNumber();
  paymentElements.dateInput.value = toDateTimeLocal(new Date());
  paymentElements.amountInput.value = getSelectedInvoice()
    ? getSuggestedPaymentAmount(getSelectedInvoice()).toFixed(2)
    : "";
  paymentElements.methodSelect.value = "false";
  paymentElements.statusSelect.value = "false";
  setPaymentMode(false);
  updateSelectedInvoiceSummary();
}

function setPaymentMode(isEditing) {
  paymentElements.saveButton.innerHTML = isEditing
    ? '<i class="fa-solid fa-floppy-disk" aria-hidden="true"></i> Actualizar pago'
    : '<i class="fa-solid fa-floppy-disk" aria-hidden="true"></i> Guardar pago';
}

function setBusy(isBusy) {
  [paymentElements.clearButton, paymentElements.saveButton].forEach((button) => {
    button.disabled = isBusy;
  });
}

function updateSelectedInvoiceSummary() {
  const factura = getSelectedInvoice();
  const pago = factura ? getPaymentForInvoice(factura.id) : null;

  paymentElements.selectedCustomer.textContent = factura ? getInvoiceCustomer(factura) : "Sin cliente";
  paymentElements.selectedInvoice.textContent = factura ? formatInvoiceCode(factura.CodigoFact) : "Sin factura";
  paymentElements.selectedAmount.textContent = factura ? formatMoney(factura.Monto_Total) : formatMoney(0);
  paymentElements.selectedStatus.textContent = pago?.EstadoPago ? "Pagada" : "Pendiente";
}

function getSelectedInvoice() {
  return getInvoiceById(paymentElements.invoiceSelect.value);
}

function getInvoiceById(id) {
  return paymentState.facturas.find((factura) => Number(factura.id) === Number(id));
}

function getNextReceiptNumber() {
  const numbers = paymentState.pagos
    .map((pago) => Number(pago.NumeroRecibo))
    .filter((number) => Number.isFinite(number));
  return (numbers.length ? Math.max(...numbers) : 0) + 1;
}

function getInvoiceCustomer(factura) {
  const customer = factura?.contrato_detalle?.cliente_detalle;
  return customer ? `${customer.Nombre} ${customer.Apellido}`.trim() : "Sin cliente";
}

function createCell(content, strong = false) {
  const cell = document.createElement("td");
  if (strong) {
    const strongElement = document.createElement("strong");
    strongElement.textContent = content || "";
    cell.appendChild(strongElement);
  } else {
    cell.textContent = content || "";
  }
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

function renderTableMessage(table, colSpan, message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = colSpan;
  cell.className = "muted-cell";
  cell.textContent = message;
  row.appendChild(cell);
  table.replaceChildren(row);
}

function formatApiError(data, status) {
  if (!data) {
    return `La API respondio con estado ${status}.`;
  }
  return Object.entries(data)
    .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join(" | ");
}

function formatInvoiceCode(code) {
  return `FAC-${String(Number(code) || 0).padStart(6, "0")}`;
}

function formatDate(value) {
  if (!value) {
    return "Sin fecha";
  }
  return new Date(value).toLocaleString("es-NI", {
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

function getMethodLabel(value) {
  return value ? "Transferencia" : "Efectivo";
}

function toDateTimeLocal(value) {
  const date = value instanceof Date ? value : new Date(value);
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

function toApiDateTime(value) {
  return `${value}:00-06:00`;
}
