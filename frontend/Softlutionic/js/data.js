const departamentos = [];
const clientes = [];
const usuarios = [];
const servicios = [];
const contratos = [];
const facturas = [];
const detalleFactura = [];
const pagos = [];
const mora = [];
const notificaciones = [];

function formatoMoneda(valor) {
  return `C$ ${Number(valor || 0).toLocaleString("es-NI", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function obtenerDepartamentoPorId(id) {
  return departamentos.find((departamento) => departamento.Id === id);
}

function obtenerClientePorId(id) {
  return clientes.find((cliente) => cliente.Id === id);
}

function obtenerNombreCliente(id) {
  const cliente = obtenerClientePorId(id);
  return cliente ? `${cliente.Nombres} ${cliente.Apellidos || ""}`.trim() : "Cliente no encontrado";
}

function obtenerServicioPorId(id) {
  return servicios.find((servicio) => servicio.Id === id);
}

function obtenerContratoPorId(id) {
  return contratos.find((contrato) => contrato.Id === id);
}

function obtenerUsuarioPorId(id) {
  return usuarios.find((usuario) => usuario.Id === id);
}

function obtenerContratosPorCliente(clienteId) {
  return contratos.filter((contrato) => contrato.ClienteId === clienteId);
}

function obtenerDetallesPorFactura(facturaId) {
  return detalleFactura.filter((detalle) => detalle.FacturaId === facturaId);
}

function calcularSubtotalLinea(cantidad, precioUnitario) {
  return Number(cantidad) * Number(precioUnitario);
}

function calcularIVA(subtotal, porcentajeIVA = 0.15) {
  return Number(subtotal) * porcentajeIVA;
}

function calcularTotalLinea(cantidad, precioUnitario, descuento = 0, aplicaIVA = true) {
  const subtotal = calcularSubtotalLinea(cantidad, precioUnitario);
  const iva = aplicaIVA ? calcularIVA(subtotal) : 0;
  const total = subtotal - Number(descuento) + iva;
  return { subtotal, iva, descuento: Number(descuento), total };
}

function calcularTotalesFactura(detalles) {
  return detalles.reduce(
    (totales, item) => {
      totales.subtotal += Number(item.SubtotalLinea || 0);
      totales.iva += Number(item.IVALinea || 0);
      totales.descuento += Number(item.DescuentoLinea || 0);
      totales.total += Number(item.TotalLinea || 0);
      return totales;
    },
    { subtotal: 0, iva: 0, descuento: 0, total: 0 }
  );
}

function generarCodigoFactura() {
  return "FAC-000001";
}

function obtenerResumenFacturas() {
  return [];
}

function obtenerTotalFacturado() {
  return 0;
}

function obtenerFacturasPendientes() {
  return [];
}

function obtenerClientesActivos() {
  return [];
}

function obtenerServiciosActivos() {
  return [];
}
