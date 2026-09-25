(() => {
  'use strict';
  const form = document.querySelector('#reportFilters');
  const message = document.querySelector('#reportMessage');
  const content = document.querySelector('#reportContent');
  const print = document.querySelector('#printReport');
  const money = new Intl.NumberFormat('es-NI', { style: 'currency', currency: 'NIO' });
  const number = new Intl.NumberFormat('es-NI', { maximumFractionDigits: 0 });
  let report = null;
  let pages = {};
  const definitions = [
    ['monthly', 'Evolución mensual', 'Facturación y cobros del período; importes independientes.', [['mes','Mes'],['facturado','Facturado','money'],['cobrado','Cobrado','money']]],
    ['methods', 'Cobros por método de pago', 'Únicamente pagos confirmados del período.', [['metodo','Método'],['cobrado','Cobrado','money']]],
    ['aging', 'Antigüedad de cartera actual', 'Saldo de capital agrupado por días de atraso.', [['antiguedad','Antigüedad'],['saldo','Saldo','money']]],
    ['portfolio', 'Cartera pendiente actual', 'Prioridad por días de atraso y saldo. Incluye abonos parciales.', [['factura','Factura'],['cliente','Cliente'],['telefono','Teléfono'],['vencimiento','Vencimiento'],['dias','Días de atraso'],['saldo','Saldo','money']]],
    ['services', 'Facturación por servicio', 'Detalle de servicios facturados en el período, de mayor a menor.', [['servicio','Servicio'],['unidades','Unidades'],['facturado','Facturado','money']]],
    ['customers', 'Clientes por facturación', 'Todos los clientes con facturas en el período, de mayor a menor.', [['cliente','Cliente'],['facturas','Facturas'],['facturado','Facturado','money']]],
    ['renewals', 'Contratos por vencer', 'Activos hoy, con vencimiento en los próximos 30 días.', [['contrato','Contrato'],['cliente','Cliente'],['tipo','Tipo'],['fin','Vencimiento'],['dias','Días restantes']]]
  ];
  function node(tag, text, className) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function localDate(date) {
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  }
  function preset() {
    const today = new Date();
    let start = new Date(today.getFullYear(), today.getMonth(), 1), end = today;
    const value = document.querySelector('#period').value;
    if (value === 'custom') return;
    if (value === 'previous') { start = new Date(today.getFullYear(), today.getMonth()-1, 1); end = new Date(today.getFullYear(), today.getMonth(), 0); }
    if (value === 'year') start = new Date(today.getFullYear(), 0, 1);
    form.elements.start.value = localDate(start); form.elements.end.value = localDate(end);
  }
  function csvCell(value) {
    let text = String(value ?? '');
    if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  }
  function download(def) {
    const [key, title, , columns] = def;
    const rows = [[title], ['Período', report.start, report.end], ['Generado', report.generated_at], ['Moneda', 'NIO'], columns.map(c => c[1]), ...report[key].map(row => columns.map(c => row[c[0]]))];
    const blob = new Blob(['\ufeff' + rows.map(row => row.map(csvCell).join(';')).join('\r\n')], {type:'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob), link = node('a');
    link.href = url; link.download = `SoftFactur-${key}-${report.start}-${report.end}.csv`;
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function renderSections(all = false) {
    const container = document.querySelector('#reportSections'); container.replaceChildren();
    definitions.forEach(def => {
      const [key, title, note, columns] = def, rows = report[key], page = pages[key] || 0;
      const section = node('section', undefined, 'panel report-section'); section.id = key;
      const header = node('div', undefined, 'report-heading'); header.append(node('h2', title));
      const exportButton = node('button', 'Exportar CSV', 'button-link secondary'); exportButton.type = 'button'; exportButton.disabled = !rows.length;
      exportButton.addEventListener('click', () => download(def)); header.append(exportButton); section.append(header);
      const wrap = node('div', undefined, 'report-table-wrap'), table = node('table'); table.append(node('caption', note));
      const head = node('thead'), hr = node('tr'); columns.forEach(c => { const th = node('th', c[1]); th.scope = 'col'; hr.append(th); }); head.append(hr); table.append(head);
      const body = node('tbody');
      const visible = all ? rows : rows.slice(page*15, page*15+15);
      const maximum = rows.reduce((max, row) => Math.max(max, Number(row[columns[columns.length-1][0]]) || 0), 1);
      visible.forEach(row => {
        const tr = node('tr'); columns.forEach(([field, , type], i) => {
          const td = node('td', type === 'money' ? money.format(Number(row[field])) : row[field], type === 'money' ? 'amount' : '');
          if (type === 'money' && i === columns.length-1 && ['services','aging','monthly'].includes(key)) {
            const bar = node('span', undefined, 'report-bar'); bar.style.width = `${Math.max(0, Number(row[field])) / maximum * 70}px`; bar.setAttribute('aria-hidden','true'); td.append(bar);
          }
          tr.append(td);
        }); body.append(tr);
      });
      if (!rows.length) { const tr = node('tr'), td = node('td', 'No hay registros para este reporte.'); td.colSpan = columns.length; tr.append(td); body.append(tr); }
      table.append(body); wrap.append(table); section.append(wrap);
      if (rows.length > 15 && !all) {
        const pager = node('div', undefined, 'report-pager');
        const prev = node('button', 'Anterior', 'button-link secondary'), next = node('button', 'Siguiente', 'button-link secondary');
        prev.disabled = page === 0; next.disabled = (page+1)*15 >= rows.length;
        prev.onclick = () => { pages[key] = page-1; renderSections(); document.getElementById(key).scrollIntoView(); };
        next.onclick = () => { pages[key] = page+1; renderSections(); document.getElementById(key).scrollIntoView(); };
        pager.append(prev, node('span', `${page*15+1}–${Math.min((page+1)*15, rows.length)} de ${rows.length}`), next); section.append(pager);
      }
      container.append(section);
    });
  }
  function render() {
    document.querySelector('#reportStamp').textContent = `Período: ${report.start} a ${report.end} · Generado: ${new Date(report.generated_at).toLocaleString('es-NI')} · Moneda: córdobas (NIO)`;
    const metrics = document.querySelector('#reportMetrics'); metrics.replaceChildren();
    [['facturado','Facturación del período','purple'],['cobrado','Cobros confirmados del período','teal'],['cartera','Cartera pendiente actual','orange'],['vencido','Cartera vencida actual','pink'],['ticket','Ticket promedio del período','purple'],['pagos_por_confirmar','Pagos por confirmar del período','orange'],['facturas','Facturas del período','teal'],['renovaciones','Contratos por vencer en 30 días','pink']].forEach(([key,title,color]) => {
      const card = node('article', undefined, `metric-card ${color}`), inner = node('div');
      inner.append(node('h3',title), node('strong', ['facturas','renovaciones'].includes(key) ? number.format(report.summary[key]) : money.format(Number(report.summary[key])))); card.append(inner); metrics.append(card);
    });
    renderSections();
  }
  async function load() {
    if (!form.reportValidity()) return;
    if (form.elements.start.value > form.elements.end.value) { message.textContent = 'La fecha inicial debe ser anterior a la final.'; message.dataset.error = 'true'; return; }
    form.querySelector('button').disabled = true; print.disabled = true; content.hidden = true;
    message.dataset.error = 'false'; message.textContent = 'Generando reportes…';
    try {
      const params = new URLSearchParams(new FormData(form));
      report = await window.SoftFacturAuth.fetch(`/reportes/?${params}`); pages = {}; render();
      content.hidden = false; print.disabled = false;
      message.textContent = report.summary.facturas ? 'Reporte actualizado. Las exportaciones incluyen todas las filas.' : 'No hay facturas en este período. Consulta los cobros y la cartera actual en sus secciones.';
    } catch (error) { report = null; message.textContent = `No se pudo generar el reporte: ${error.message} Puedes volver a intentarlo.`; message.dataset.error = 'true'; }
    finally { form.querySelector('button').disabled = false; }
  }
  form.addEventListener('submit', event => { event.preventDefault(); load(); });
  document.querySelector('#period').addEventListener('change', preset);
  form.querySelectorAll('input').forEach(input => { input.max = localDate(new Date()); input.addEventListener('change', () => { document.querySelector('#period').value = 'custom'; }); });
  window.addEventListener('beforeprint', () => { if (report) renderSections(true); });
  window.addEventListener('afterprint', () => { if (report) renderSections(); });
  print.addEventListener('click', () => window.print());
  preset();
  window.SoftFacturAuth.requireSession().then(user => { if (user?.Rol) load(); });
})();
