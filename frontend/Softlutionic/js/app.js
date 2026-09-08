const VERSION_POLL_INTERVAL_MS = 8000;
const MONEY_FORMATTER = new Intl.NumberFormat("es-NI", {
  style: "currency",
  currency: "NIO",
  minimumFractionDigits: 2
});
const NUMBER_FORMATTER = new Intl.NumberFormat("es-NI");
const CHART_COLORS = ["#6d5dfc", "#14b8a6", "#ec4899", "#f59e0b", "#16a34a", "#dc2626", "#2563eb"];

const charts = {};
let pollTimer = null;
let isLoading = false;
let lastDashboardRevision = null;

function getApiBase() {
  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000/api";
  }

  return `${window.location.origin}/api`;
}

function buildQuery() {
  const form = document.querySelector("#dashboardFilters");
  const params = new URLSearchParams();
  if (!form) return "";

  const formData = new FormData(form);
  ["start", "end"].forEach((key) => {
    const value = String(formData.get(key) || "").trim();
    if (value) params.set(key, value);
  });

  const query = params.toString();
  return query ? `?${query}` : "";
}

async function apiGet(path) {
  if (window.SoftFacturAuth && typeof window.SoftFacturAuth.fetch === "function") {
    return window.SoftFacturAuth.fetch(path);
  }

  const response = await fetch(`${getApiBase()}${path}`, {
    credentials: "include",
    headers: { Accept: "application/json" }
  });

  if (!response.ok) {
    throw new Error(`La API respondió con estado ${response.status}.`);
  }

  return response.json();
}

function fetchDashboard(endpoint) {
  return apiGet(`${endpoint}${buildQuery()}`);
}

function fetchDashboardVersion() {
  return apiGet("/dashboard/version/");
}

function setMessage(message, type = "info") {
  const element = document.querySelector("#dashboardMessage");
  if (!element) return;

  element.textContent = message;
  element.dataset.type = type;
  element.hidden = !message;
}

function setRefreshStatus(message, mode = "idle") {
  const element = document.querySelector("#refreshStatus");
  if (!element) return;

  element.textContent = message;
  element.dataset.mode = mode;
}

function setMetric(name, value, options = {}) {
  const element = document.querySelector(`[data-metric="${name}"]`);
  if (!element) return;

  element.textContent = options.money
    ? MONEY_FORMATTER.format(Number(value || 0))
    : NUMBER_FORMATTER.format(Number(value || 0));
}

function emptyRows(tableBody, colspan, message) {
  tableBody.replaceChildren();
  const row = document.createElement("tr");
  const tableCell = document.createElement("td");
  tableCell.colSpan = colspan;
  tableCell.textContent = message;
  row.appendChild(tableCell);
  tableBody.appendChild(row);
}

function statusClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized.includes("pagada") || normalized.includes("confirmado") || normalized.includes("activo")) return "paid";
  if (normalized.includes("pendiente")) return "pending";
  if (normalized.includes("vencida") || normalized.includes("finalizado")) return "overdue";
  return "neutral";
}

function cell(text, strong = false) {
  const tableCell = document.createElement("td");
  if (strong) {
    const element = document.createElement("strong");
    element.textContent = text;
    tableCell.appendChild(element);
  } else {
    tableCell.textContent = text;
  }
  return tableCell;
}

function badge(text) {
  const tableCell = document.createElement("td");
  const span = document.createElement("span");
  span.className = `status ${statusClass(text)}`;
  span.textContent = text || "Sin estado";
  tableCell.appendChild(span);
  return tableCell;
}

function renderInvoiceTable(rows) {
  const tableBody = document.querySelector("#invoiceTable");
  if (!tableBody) return;
  if (!rows.length) {
    emptyRows(tableBody, 4, "No hay facturas para el rango seleccionado.");
    return;
  }

  const fragment = document.createDocumentFragment();
  rows.forEach((invoice) => {
    const row = document.createElement("tr");
    row.append(
      cell(invoice.CodigoFact, true),
      cell(invoice.Fecha_Emision),
      cell(MONEY_FORMATTER.format(Number(invoice.Monto_Total || 0)), true),
      badge(invoice.estado)
    );
    fragment.appendChild(row);
  });
  tableBody.replaceChildren(fragment);
}

function renderCommercialTable(rows) {
  const tableBody = document.querySelector("#commercialTable");
  if (!tableBody) return;
  if (!rows.length) {
    emptyRows(tableBody, 5, "No hay contratos registrados para mostrar.");
    return;
  }

  const fragment = document.createDocumentFragment();
  rows.forEach((item) => {
    const row = document.createElement("tr");
    row.append(
      cell(item.Nombre, true),
      cell(item.Apellido),
      cell(item.Telefono),
      badge(item.EstadoContrato),
      cell(item.TipoContrato)
    );
    fragment.appendChild(row);
  });
  tableBody.replaceChildren(fragment);
}

function chartData(items) {
  return {
    labels: items.map((item) => item.label),
    values: items.map((item) => Number(item.value || 0))
  };
}

function upsertChart(id, type, items, label) {
  const canvas = document.getElementById(id);
  if (!canvas || !window.Chart) return;

  const data = chartData(items || []);
  const config = {
    type,
    data: {
      labels: data.labels.length ? data.labels : ["Sin datos"],
      datasets: [{
        label,
        data: data.values.length ? data.values : [0],
        backgroundColor: type === "doughnut" ? CHART_COLORS : CHART_COLORS[0],
        borderColor: type === "doughnut" ? "#ffffff" : CHART_COLORS[0],
        borderWidth: type === "doughnut" ? 2 : 1,
        borderRadius: type === "bar" ? 8 : 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      transitions: { active: { animation: { duration: 0 } } },
      plugins: {
        legend: { display: type === "doughnut", position: "bottom" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${NUMBER_FORMATTER.format(ctx.parsed.y ?? ctx.parsed)}`
          }
        }
      },
      scales: type === "doughnut" ? {} : { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  };

  if (charts[id]) {
    charts[id].data = config.data;
    charts[id].options = config.options;
    charts[id].update("none");
    return;
  }

  charts[id] = new Chart(canvas, config);
}

function renderBilling(data) {
  setMetric("total_facturado", data.cards.total_facturado, { money: true });
  setMetric("total_pagado", data.cards.total_pagado, { money: true });
  setMetric("saldo_pendiente", data.cards.saldo_pendiente, { money: true });
  setMetric("total_mora", data.cards.total_mora, { money: true });
  renderInvoiceTable(data.tables.facturas || []);
  upsertChart("billingBarChart", "bar", data.charts.facturado_por_mes || [], "Total facturado");
  upsertChart("invoiceStatusChart", "doughnut", data.charts.facturas_por_estado || [], "Facturas");
}

function renderCustomers(data) {
  setMetric("cantidad_clientes", data.cards.cantidad_clientes);
  setMetric("cantidad_contratos", data.cards.cantidad_contratos);
  setMetric("ticket_promedio", data.cards.ticket_promedio, { money: true });
  setMetric("ingresos_por_servicio", data.cards.ingresos_por_servicio, { money: true });
  renderCommercialTable(data.tables.comercial || []);
  upsertChart("serviceRevenueChart", "bar", data.charts.ingresos_por_servicio || [], "Ingresos");
  upsertChart("contractTypeChart", "bar", data.charts.contratos_por_tipo || [], "Contratos");
  upsertChart("departmentChart", "bar", data.charts.clientes_por_departamento || [], "Clientes");
}

async function loadDashboards({ force = false } = {}) {
  if (isLoading) return;
  isLoading = true;
  setRefreshStatus(force ? "Actualizando datos..." : "Revisando cambios...", "loading");

  try {
    if (!force) {
      const version = await fetchDashboardVersion();
      if (lastDashboardRevision === version.revision) {
        setRefreshStatus(`Sin cambios ${new Date().toLocaleTimeString("es-NI")}`, "idle");
        return;
      }
      lastDashboardRevision = version.revision;
    }

    const [billing, customers] = await Promise.all([
      fetchDashboard("/dashboard/facturacion/"),
      fetchDashboard("/dashboard/clientes-servicios/")
    ]);
    renderBilling(billing);
    renderCustomers(customers);

    if (force) {
      const version = await fetchDashboardVersion();
      lastDashboardRevision = version.revision;
    }

    setMessage("");
    setRefreshStatus(`Actualizado ${new Date().toLocaleTimeString("es-NI")}`, "fresh");
  } catch (error) {
    setMessage(error.message || "No se pudieron cargar los dashboards.", "error");
    setRefreshStatus("Sin conexión con el dashboard", "error");
  } finally {
    isLoading = false;
  }
}

function activateDashboardTab(button) {
  const tab = button.dataset.dashboardTab;
  document.querySelectorAll("[data-dashboard-tab]").forEach((item) => {
    const selected = item === button;
    item.classList.toggle("active", selected);
    item.setAttribute("aria-selected", selected ? "true" : "false");
  });

  document.querySelectorAll("[data-dashboard-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.dashboardPanel === tab);
  });

  Object.values(charts).forEach((chart) => chart.resize());
}

function bindTabs() {
  document.querySelectorAll("[data-dashboard-tab]").forEach((button) => {
    button.addEventListener("click", () => activateDashboardTab(button));
    button.addEventListener("keydown", (event) => {
      const tabs = Array.from(document.querySelectorAll("[data-dashboard-tab]"));
      const currentIndex = tabs.indexOf(button);
      if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;

      event.preventDefault();
      const offset = event.key === "ArrowRight" ? 1 : -1;
      const next = tabs[(currentIndex + offset + tabs.length) % tabs.length];
      next.focus();
      activateDashboardTab(next);
    });
  });
}

function bindFilters() {
  const form = document.querySelector("#dashboardFilters");
  if (!form) return;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    loadDashboards({ force: true });
  });
}

function startVersionPolling() {
  window.clearInterval(pollTimer);
  pollTimer = window.setInterval(() => {
    if (document.visibilityState === "visible") {
      loadDashboards();
    }
  }, VERSION_POLL_INTERVAL_MS);
}

bindTabs();
bindFilters();
loadDashboards({ force: true });
startVersionPolling();