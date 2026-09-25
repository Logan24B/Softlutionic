from datetime import date, datetime, time
from decimal import Decimal

from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError

from apps.catalogos.clientes.models import Cliente
from apps.catalogos.departamentos.models import Departamentos
from apps.catalogos.servicios.models import Servicio
from apps.seguridad.usuarios.models import user
from apps.transaccion.contratos.models import Contrato
from apps.transaccion.factura.models import Factura, EstadoFactura, DetalleFactura
from apps.transaccion.pagos.models import Pago
from .reports import ManagementReportsAPIView, build_report, report_dates


class ReportAccessTests(SimpleTestCase):
    def test_dates_reject_invalid_reversed_future_and_excessive_ranges(self):
        for params in [{'start': 'invalid'}, {'start': '2026-02-30'},
                       {'start': '2026-07-02', 'end': '2026-07-01'},
                       {'end': '2027-01-01'}, {'start': '2020-01-01'}]:
            with self.subTest(params=params), self.assertRaises(ValidationError):
                report_dates(params, date(2026, 7, 15))

    def test_employee_and_anonymous_cannot_read_reports(self):
        for actor in [None, user(username='employee', Rol=False)]:
            request = APIRequestFactory().get('/api/reportes/')
            if actor:
                force_authenticate(request, user=actor)
            self.assertEqual(ManagementReportsAPIView.as_view()(request).status_code, 403)


class ReportCalculationTests(TestCase):
    def setUp(self):
        self.admin = user.objects.create(username='reports-admin', Rol=True)
        department = Departamentos.objects.create(Nombre='Managua')
        client = Cliente.objects.create(DepartamentoId=department, Nombre='Cliente', Apellido='Prueba',
                                        Telefono='+505 8888 7777', Correo='report@example.test', Direccion='Prueba')
        self.contract = Contrato.objects.create(ClienteId=client, Fecha_Inc=date(2026,1,1),
                                                Fecha_Fin=date(2026,7,30), Descripcion='Prueba')
        self.pending = EstadoFactura.objects.get_or_create(estado='Pendiente')[0]
        self.cancelled = EstadoFactura.objects.get_or_create(estado='Anulada')[0]
        self.now = timezone.make_aware(datetime(2026,7,15,12))

    def invoice(self, code, total, emitted, state=None):
        # Bulk insertion preserves explicit dates and avoids unrelated workflow signals.
        Factura.objects.bulk_create([Factura(UsuarioId=self.admin, ContratoId=self.contract,
            Fecha_Emision=emitted, Hora_Emision=time(0), Fecha_Vencimiento=date(2026,7,1),
            Hora_Vencimiento=time(23,59), Monto_Total=total, CodigoFact=code, EstadoId=state or self.pending)])
        return Factura.objects.get(CodigoFact=code)

    def payment(self, invoice, amount, confirmed, day, receipt):
        Pago.objects.bulk_create([Pago(FacturaId=invoice, Monto_Pagado=amount, EstadoPago=confirmed,
            Fecha_Pago=timezone.make_aware(datetime(2026,7,day,0)), NumeroRecibo=receipt)])

    def test_partial_unconfirmed_cancelled_and_overpaid_invoices(self):
        old = self.invoice(1, 100, date(2026,6,1))
        current = self.invoice(2, 200, date(2026,7,1))
        cancelled = self.invoice(3, 900, date(2026,7,1), self.cancelled)
        self.payment(old, 40, True, 2, 1)
        self.payment(old, 60, False, 3, 2)
        self.payment(current, 250, True, 4, 3)
        self.payment(cancelled, 900, True, 4, 4)
        self.payment(old, 10, True, 16, 5)
        result = build_report(date(2026,7,1), date(2026,7,15), self.now)
        self.assertEqual(result['summary']['facturado'], Decimal('200'))
        self.assertEqual(result['summary']['cobrado'], Decimal('290'))
        self.assertEqual(result['summary']['cartera'], Decimal('60'))
        self.assertEqual(result['summary']['vencido'], Decimal('60'))
        self.assertEqual(result['summary']['pagos_por_confirmar'], Decimal('60'))
        self.assertEqual(len(result['portfolio']), 1)
        self.assertEqual(result['summary']['renovaciones'], 1)

    def test_payment_next_midnight_excluded_and_empty_month_zero_filled(self):
        invoice = self.invoice(1, 100, date(2026,6,1))
        self.payment(invoice, 20, True, 2, 1)
        result = build_report(date(2026,7,1), date(2026,7,1), self.now)
        self.assertEqual(result['summary']['cobrado'], 0)
        self.assertEqual(result['monthly'], [{'mes':'2026-07','facturado':0,'cobrado':0}])
        self.assertEqual(result['summary']['cartera'], 80)

    def test_admin_endpoint_and_no_cache(self):
        request = APIRequestFactory().get('/api/reportes/')
        force_authenticate(request, user=self.admin)
        response = ManagementReportsAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_service_totals_exclude_cancelled_and_multiple_payments_do_not_duplicate(self):
        invoice = self.invoice(1, 300, date(2026,7,1))
        cancelled = self.invoice(2, 100, date(2026,7,1), self.cancelled)
        service = Servicio.objects.create(Nombre_Servicio='Internet', Precio=100, Duracion='Mensual')
        DetalleFactura.objects.bulk_create([
            DetalleFactura(FacturaId=invoice, ServicioId=service, PrecioVenta=100, Cantidad=3),
            DetalleFactura(FacturaId=cancelled, ServicioId=service, PrecioVenta=100, Cantidad=1)])
        self.payment(invoice, 20, True, 2, 1)
        self.payment(invoice, 30, True, 3, 2)
        result = build_report(date(2026,7,1), date(2026,7,15), self.now)
        self.assertEqual(result['services'], [{'servicio':'Internet','unidades':3,'facturado':300}])
        self.assertEqual(result['customers'][0]['facturado'], 300)
        self.assertEqual(result['summary']['cartera'], 250)
