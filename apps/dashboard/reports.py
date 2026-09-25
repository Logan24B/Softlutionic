"""Read-only management reports. Money is calculated with Decimal throughout."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transaccion.contratos.models import Contrato
from apps.transaccion.factura.models import DetalleFactura, Factura
from apps.transaccion.pagos.models import Pago
from .api import IsDashboardAdmin


ZERO = Decimal('0.00')


def report_dates(params, today):
    try:
        start = date.fromisoformat(params.get('start') or today.replace(day=1).isoformat())
        end = date.fromisoformat(params.get('end') or today.isoformat())
    except (ValueError, TypeError):
        raise ValidationError({'detail': 'Usa fechas válidas con formato AAAA-MM-DD.'})
    if start > end or end > today:
        raise ValidationError({'detail': 'El inicio debe ser anterior al fin y el fin no puede ser futuro.'})
    if (end - start).days > 1095:
        raise ValidationError({'detail': 'Selecciona un período de hasta tres años.'})
    return start, end


def build_report(start, end, now):
    today = now.date()
    confirmed = Pago.objects.filter(EstadoPago=True, Fecha_Pago__lte=now)
    invoices = list(Factura.objects.exclude(EstadoId__estado__iexact='Anulada')
                    .filter(Fecha_Emision__lte=today)
                    .select_related('ContratoId__ClienteId')
                    .prefetch_related(Prefetch('pagos', queryset=confirmed, to_attr='confirmed_payments')))
    monthly = {}
    month = start.replace(day=1)
    while month <= end:
        monthly[month.strftime('%Y-%m')] = {'mes': month.strftime('%Y-%m'), 'facturado': ZERO, 'cobrado': ZERO}
        month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    total = ZERO
    count = 0
    customers = {}
    portfolio = []
    aging = dict.fromkeys(['Al día', '1–30 días', '31–60 días', '61–90 días', 'Más de 90 días'], ZERO)
    for invoice in invoices:
        client = invoice.ContratoId.ClienteId
        name = f'{client.Nombre} {client.Apellido}'
        if start <= invoice.Fecha_Emision <= end:
            total += invoice.Monto_Total
            count += 1
            monthly[invoice.Fecha_Emision.strftime('%Y-%m')]['facturado'] += invoice.Monto_Total
            item = customers.setdefault(client.pk, {'cliente': name, 'facturas': 0, 'facturado': ZERO})
            item['facturas'] += 1
            item['facturado'] += invoice.Monto_Total
        paid = sum((p.Monto_Pagado for p in invoice.confirmed_payments), ZERO)
        balance = max(ZERO, invoice.Monto_Total - paid)
        if balance:
            due = timezone.make_aware(datetime.combine(invoice.Fecha_Vencimiento, invoice.Hora_Vencimiento))
            overdue = now > due
            days = max(1, (today - invoice.Fecha_Vencimiento).days) if overdue else 0
            bucket = 'Al día' if not days else '1–30 días' if days <= 30 else '31–60 días' if days <= 60 else '61–90 días' if days <= 90 else 'Más de 90 días'
            aging[bucket] += balance
            portfolio.append({'factura': invoice.CodigoFact, 'cliente': name, 'telefono': client.Telefono,
                              'vencimiento': invoice.Fecha_Vencimiento.isoformat(), 'dias': days, 'saldo': balance})
    lower = timezone.make_aware(datetime.combine(start, time.min))
    upper = min(now, timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min)))
    payments = list(Pago.objects.filter(Fecha_Pago__gte=lower, Fecha_Pago__lte=upper)
                    .exclude(FacturaId__EstadoId__estado__iexact='Anulada'))
    # The next midnight belongs to the following period.
    payments = [p for p in payments if timezone.localtime(p.Fecha_Pago).date() <= end]
    collected = ZERO
    pending = ZERO
    methods = {'Efectivo': ZERO, 'Transferencia': ZERO}
    for payment in payments:
        if payment.EstadoPago:
            collected += payment.Monto_Pagado
            methods[payment.metodo_descripcion] += payment.Monto_Pagado
            monthly[timezone.localtime(payment.Fecha_Pago).strftime('%Y-%m')]['cobrado'] += payment.Monto_Pagado
        else:
            pending += payment.Monto_Pagado
    services = {}
    details = DetalleFactura.objects.filter(FacturaId__Fecha_Emision__range=(start, end)).exclude(
        FacturaId__EstadoId__estado__iexact='Anulada').select_related('ServicioId')
    for detail in details:
        item = services.setdefault(detail.ServicioId_id, {'servicio': detail.ServicioId.Nombre_Servicio, 'unidades': 0, 'facturado': ZERO})
        item['unidades'] += detail.Cantidad
        item['facturado'] += Decimal(detail.PrecioVenta) * detail.Cantidad
    contracts = Contrato.objects.filter(EstadoContrato=True, Fecha_Inc__lte=today,
                                        Fecha_Fin__gte=today, Fecha_Fin__lte=today + timedelta(days=30))
    renewals = [{'contrato': c.pk, 'cliente': str(c.ClienteId), 'tipo': str(c.TipoContratoId or 'Sin tipo'),
                 'fin': c.Fecha_Fin.isoformat(), 'dias': (c.Fecha_Fin - today).days}
                for c in contracts.select_related('ClienteId', 'TipoContratoId').order_by('Fecha_Fin', 'pk')]
    return {'start': start.isoformat(), 'end': end.isoformat(), 'generated_at': now.isoformat(), 'currency': 'NIO',
            'summary': {'facturado': total, 'cobrado': collected, 'facturas': count,
                        'ticket': total / count if count else ZERO, 'pagos_por_confirmar': pending,
                        'cartera': sum(aging.values(), ZERO), 'vencido': sum(aging.values(), ZERO) - aging['Al día'],
                        'renovaciones': len(renewals)},
            'monthly': list(monthly.values()), 'methods': [{'metodo': k, 'cobrado': v} for k, v in methods.items()],
            'aging': [{'antiguedad': k, 'saldo': v} for k, v in aging.items()],
            'customers': sorted(customers.values(), key=lambda x: (-x['facturado'], x['cliente'])),
            'services': sorted(services.values(), key=lambda x: (-x['facturado'], x['servicio'])),
            'portfolio': sorted(portfolio, key=lambda x: (-x['dias'], -x['saldo'], x['factura'])), 'renewals': renewals}


class ManagementReportsAPIView(APIView):
    permission_classes = [IsDashboardAdmin]

    def get(self, request):
        now = timezone.localtime()
        start, end = report_dates(request.query_params, now.date())
        response = Response(build_report(start, end, now))
        response['Cache-Control'] = 'no-store'
        return response
