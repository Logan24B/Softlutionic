const invoices = [
  {
    number: "FAC-000148",
    customer: "Comercial La Unión",
    date: "18/04/2026",
    amount: "C$ 24,850",
    status: "Pagada"
  },
  {
    number: "FAC-000149",
    customer: "Farmacia Central",
    date: "19/04/2026",
    amount: "C$ 11,320",
    status: "Pendiente"
  },
  {
    number: "FAC-000150",
    customer: "Distribuidora Norte",
    date: "20/04/2026",
    amount: "C$ 38,700",
    status: "Vencida"
  },
  {
    number: "FAC-000151",
    customer: "Hotel Las Palmas",
    date: "21/04/2026",
    amount: "C$ 16,940",
    status: "Pagada"
  },
  {
    number: "FAC-000152",
    customer: "Supermercado Central",
    date: "22/04/2026",
    amount: "C$ 9,750",
    status: "Pendiente"
  }
];

const statusClasses = {
  Pagada: "paid",
  Pendiente: "pending",
  Vencida: "overdue"
};

function createTableCell(content, options = {}) {
  const cell = document.createElement("td");
  const element = options.strong ? document.createElement("strong") : cell;

  element.textContent = content;

  if (options.strong) {
    cell.appendChild(element);
  }

  return cell;
}

function createStatusBadge(status) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");

  badge.className = `status ${statusClasses[status] || "neutral"}`;
  badge.textContent = status;

  cell.appendChild(badge);
  return cell;
}

function renderInvoices(tableBody, invoiceList) {
  const fragment = document.createDocumentFragment();

  invoiceList.forEach((invoice) => {
    const row = document.createElement("tr");

    row.append(
      createTableCell(invoice.number, { strong: true }),
      createTableCell(invoice.customer),
      createTableCell(invoice.date),
      createTableCell(invoice.amount, { strong: true }),
      createStatusBadge(invoice.status)
    );

    fragment.appendChild(row);
  });

  tableBody.replaceChildren(fragment);
}

const invoiceTable = document.querySelector("#invoiceTable");

if (invoiceTable) {
  renderInvoices(invoiceTable, invoices);
}
