ctconst api = {
    usuarios: "/api/usuarios/",
    contratos: "/api/contratos/?activo=true&ordering=id",
    servicios: "/api/servicios/?ordering=Nombre_Servicio",
    facturas: "/api/facturas/",
    detalles: "/api/detalles-factura/",
};

const state = {
    usuarios: [],
    contratos: [],
    servicios: [],
    facturas: [],
    nextCode: null,
    currentInvoice: null,
};

const els = {
    apiStatus: document.querySelector("#apiStatus"),
    usuarioSelect: document.querySelector("#usuarioSelect"),
    contratoSelect: document.querySelector("#contratoSelect"),
    fechaEmision: document.querySelector("#fechaEmision"),
    fechaVencimiento: document.querySelector("#fechaVencimiento"),
    serviciosBody: document.querySelector("#serviciosBody"),
    serviceCount: document.querySelector("#serviceCount"),
    nextCode: document.querySelector("#nextCode"),
    form: document.querySelector("#invoiceForm"),
    message: document.querySelector("#message"),
    invoicePreview: document.querySelector("#invoicePreview"),
    printButton: document.querySelector("#printButton"),
    resetButton: document.querySelector("#resetButton"),
};

document.addEventListener("DOMContentLoaded", init);
els.form.addEventListener("submit", generateInvoice);
els.resetButton.addEventListener("click", resetForm);
els.printButton.addEventListener("click", () => window.print());

async function init() {
    setDefaultDates();
    setStatus("Conectando con la API...");

    try {
        const [usuarios, contratos, servicios, facturas] = await Promise.all([
            fetchJson(api.usuarios),
            fetchJson(api.contratos),
            fetchJson(api.servicios),
            fetchJson(`${api.facturas}?ordering=-CodigoFact`),
        ]);

        state.usuarios = asList(usuarios);
        state.contratos = asList(contratos);
        state.servicios = asList(servicios);
        state.facturas = asList(facturas);
        state.nextCode = getNextInvoiceCode(state.facturas);

        renderUsers();
        renderContracts();
        renderServices();
        renderNextCode();
        setStatus("API conectada", "ok");
        setMessage("Lista la interfaz para generar factura.", "ok");
    } catch (error) {
        setStatus("API no disponible", "error");
        setMessage(error.message, "error");
    }
}

async function generateInvoice(event) {
    event.preventDefault();
    setMessage("Generando factura...");
    toggleForm(false);

    try {
        const selectedServices = getSelectedServices();
        if (!selectedServices.length) {
            throw new Error("Selecciona al menos un servicio para facturar.");
        }

        const facturaPayload = {
            UsuarioId: Number(els.usuarioSelect.value),
            ContratoId: Number(els.contratoSelect.value),
            Fecha_Emision: toApiDate(els.fechaEmision.value),
            Hora_Emision: toApiTime(els.fechaEmision.value),
            Fecha_Vencimiento: toApiDate(els.fechaVencimiento.value),
            Hora_Vencimiento: toApiTime(els.fechaVencimiento.value),
            CodigoFact: state.nextCode,
        };

        const factura = await fetchJson(api.facturas, {
            method: "POST",
            body: JSON.stringify(facturaPayload),
        });

        for (const item of selectedServices) {
            await fetchJson(api.detalles, {
                method: "POST",
                body: JSON.stringify({
                    FacturaId: factura.id,
                    ServicioId: item.id,
                    Cantidad: item.cantidad,
                }),
            });
        }

        const facturaFinal = await fetchJson(`${api.facturas}${factura.id}/`);
        state.currentInvoice = facturaFinal;
        state.facturas.unshift(facturaFinal);
        state.nextCode = getNextInvoiceCode(state.facturas);

        renderNextCode();
        renderInvoice(facturaFinal);
        setMessage(`Factura ${facturaFinal.CodigoFact} generada correctamente.`, "ok");
        els.printButton.disabled = false;
    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        toggleForm(true);
    }
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        ...options,
    });

    let data = null;
    try {
        data = await response.json();
    } catch {
        data = null;
    }

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

    if (Array.isArray(data)) {
        return data.join(" ");
    }

    return Object.entries(data)
        .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : value}`)
        .join(" | ");
}

function asList(data) {
    if (Array.isArray(data)) {
        return data;
    }

    if (data && Array.isArray(data.results)) {
        return data.results;
    }

    return [];
}

function renderUsers() {
    els.usuarioSelect.innerHTML = "";

    state.usuarios.forEach((usuario) => {
        const option = document.createElement("option");
        option.value = usuario.id;
        option.textContent = `${usuario.PrimerNombre} ${usuario.SegundoNombre} (${usuario.Usuario || usuario.Email})`;
        els.usuarioSelect.appendChild(option);
    });
}

function renderContracts() {
    els.contratoSelect.innerHTML = "";

    state.contratos.forEach((contrato) => {
        const cliente = contrato.cliente_detalle || {};
        const option = document.createElement("option");
        option.value = contrato.id;
        option.textContent = `Contrato ${contrato.id} - ${cliente.Nombre || "Cliente"} ${cliente.Apellido || ""}`;
        els.contratoSelect.appendChild(option);
    });
}

function renderServices() {
    if (!state.servicios.length) {
        els.serviciosBody.innerHTML = `<tr><td colspan="4">No hay servicios disponibles.</td></tr>`;
        return;
    }

    els.serviciosBody.innerHTML = state.servicios.map((servicio) => `
        <tr>
            <td>
                <input type="checkbox" data-service-check="${servicio.id}" aria-label="Seleccionar ${escapeHtml(servicio.Nombre_Servicio)}">
            </td>
            <td>
                <strong>${escapeHtml(servicio.Nombre_Servicio)}</strong>
                <span class="service-desc">${escapeHtml(servicio.Descripcion || "")}</span>
            </td>
            <td class="money">${formatMoney(servicio.Precio)}</td>
            <td>
                <input class="qty-input" type="number" min="1" value="1" data-service-qty="${servicio.id}" aria-label="Cantidad ${escapeHtml(servicio.Nombre_Servicio)}">
            </td>
        </tr>
    `).join("");

    els.serviciosBody.addEventListener("change", renderSelectedCount);
    els.serviciosBody.addEventListener("input", renderSelectedCount);
    renderSelectedCount();
}

function renderSelectedCount() {
    const count = getSelectedServices().length;
    els.serviceCount.textContent = `${count} seleccionado${count === 1 ? "" : "s"}`;
}

function renderNextCode() {
    els.nextCode.textContent = `Codigo ${state.nextCode || "-"}`;
}

function renderInvoice(factura) {
    const contrato = factura.contrato_detalle || {};
    const cliente = contrato.cliente_detalle || {};
    const usuario = factura.usuario_detalle || {};
    const detalles = factura.detalles || [];

    els.invoicePreview.innerHTML = `
        <div class="invoice-header">
            <div class="brand-block">
                <strong>SoftFactur</strong>
                <span>Sistema de facturacion y control de servicios</span>
                <span>Managua, Nicaragua</span>
            </div>
            <div class="invoice-meta">
                <strong>Factura #${escapeHtml(factura.CodigoFact)}</strong>
                <span>Emision: ${formatDate(factura.Fecha_Emision, factura.Hora_Emision)}</span>
                <span>Vence: ${formatDate(factura.Fecha_Vencimiento, factura.Hora_Vencimiento)}</span>
            </div>
        </div>

        <div class="client-box">
            <div>
                <h3>Cliente</h3>
                <span>${escapeHtml(cliente.Nombre || "")} ${escapeHtml(cliente.Apellido || "")}</span>
                <span>${escapeHtml(cliente.Correo || "")}</span>
                <span>${escapeHtml(cliente.Telefono || "")}</span>
                <span>${escapeHtml(cliente.Direccion || "")}</span>
            </div>
            <div>
                <h3>Contrato y emisor</h3>
                <span>Contrato ${escapeHtml(contrato.id || "")}: ${escapeHtml(contrato.Descripcion || "")}</span>
                <span>Estado: ${escapeHtml(contrato.estado_descripcion || "")}</span>
                <span>Emitido por: ${escapeHtml(usuario.PrimerNombre || "")} ${escapeHtml(usuario.SegundoNombre || "")}</span>
            </div>
        </div>

        <table class="invoice-table">
            <thead>
                <tr>
                    <th>Servicio</th>
                    <th class="right">Precio</th>
                    <th class="right">Cantidad</th>
                    <th class="right">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                ${detalles.map((detalle) => {
                    const servicio = detalle.servicio_detalle || {};
                    return `
                        <tr>
                            <td>${escapeHtml(servicio.Nombre_Servicio || "")}</td>
                            <td class="right">${formatMoney(detalle.PrecioVenta)}</td>
                            <td class="right">${escapeHtml(detalle.Cantidad)}</td>
                            <td class="right">${formatMoney(detalle.Subtotal)}</td>
                        </tr>
                    `;
                }).join("")}
            </tbody>
        </table>

        <div class="invoice-total">
            <div class="total-row">
                <span>Subtotal</span>
                <strong class="right">${formatMoney(factura.Monto_Total)}</strong>
            </div>
            <div class="total-row final">
                <span>Total</span>
                <strong class="right">${formatMoney(factura.Monto_Total)}</strong>
            </div>
        </div>

        <p class="note">Comprobante generado desde la API de SoftFactur. Documento preparado para impresion.</p>
    `;
}

function getSelectedServices() {
    return state.servicios
        .map((servicio) => {
            const checked = document.querySelector(`[data-service-check="${servicio.id}"]`);
            const qty = document.querySelector(`[data-service-qty="${servicio.id}"]`);

            return {
                id: servicio.id,
                cantidad: Math.max(1, Number(qty?.value || 1)),
                checked: Boolean(checked?.checked),
            };
        })
        .filter((servicio) => servicio.checked);
}

function getNextInvoiceCode(facturas) {
    const codes = facturas
        .map((factura) => Number(factura.CodigoFact))
        .filter((codigo) => Number.isFinite(codigo));

    return (codes.length ? Math.max(...codes) : 1000) + 1;
}

function setDefaultDates() {
    const now = new Date();
    const due = new Date(now);
    due.setDate(due.getDate() + 30);

    els.fechaEmision.value = toInputDateTime(now);
    els.fechaVencimiento.value = toInputDateTime(due);
}

function toInputDateTime(date) {
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 16);
}

function toApiDate(value) {
    return String(value || "").slice(0, 10);
}

function toApiTime(value) {
    const timeMatch = String(value || "").match(/T(\d{2}:\d{2})(?::(\d{2}))?/);

    if (!timeMatch) {
        return "00:00:00";
    }

    return `${timeMatch[1]}:${timeMatch[2] || "00"}`;
}

function resetForm() {
    els.form.reset();
    setDefaultDates();
    renderSelectedCount();
    setMessage("Formulario limpio.");
}

function toggleForm(enabled) {
    els.form.querySelectorAll("button, input, select").forEach((element) => {
        element.disabled = !enabled;
    });
}

function setStatus(text, type = "") {
    els.apiStatus.textContent = text;
    els.apiStatus.className = `api-status ${type}`.trim();
}

function setMessage(text, type = "") {
    els.message.textContent = text;
    els.message.className = `message ${type}`.trim();
}

function formatMoney(value) {
    return new Intl.NumberFormat("es-NI", {
        style: "currency",
        currency: "NIO",
    }).format(Number(value || 0));
}

function formatDate(value, time = "00:00:00") {
    if (!value) {
        return "";
    }

    return new Intl.DateTimeFormat("es-NI", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(`${value}T${time || "00:00:00"}`));
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
