from copy import deepcopy
from datetime import date, datetime, timezone
from unittest.mock import patch

from bson import ObjectId
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import SimpleTestCase, TransactionTestCase
from pymongo.errors import ConnectionFailure
from rest_framework.test import APIClient

from apps.catalogos.clientes.models import Cliente
from apps.catalogos.departamentos.models import Departamentos
from apps.transaccion.contratos.models import Contrato
from apps.transaccion.factura.models import EstadoFactura, Factura
from apps.transaccion.factura.serializers import FacturaSerializer
from apps.transaccion.pagos.models import Pago
from apps.transaccion.pagos.serializers import PagoSerializer
from .api import AtomicInvoiceSerializer


class Cursor(list):
    def sort(self, ordering):
        return Cursor(sorted(self, key=lambda doc: doc['fecha_creacion'], reverse=True))


class FakeCollection:
    """Small query-contract fake; no external databases or extra test dependencies."""
    def __init__(self, documents):
        self.documents = deepcopy(documents)

    def matches(self, doc, query):
        for key, value in query.items():
            if key == 'destinatarios_roles' and value not in doc[key]:
                return False
            if key == '_id' and value != doc[key]:
                return False
            if key == 'lecturas.usuario_id_sql' and any(
                    read['usuario_id_sql'] == value['$ne'] for read in doc['lecturas']):
                return False
        return True

    def find(self, query):
        return Cursor(deepcopy([doc for doc in self.documents if self.matches(doc, query)]))

    def find_one(self, query):
        return next(iter(self.find(query)), None)

    def count_documents(self, query):
        return len(self.find(query))

    def update_one(self, query, update):
        for doc in self.documents:
            if self.matches(doc, query):
                doc['lecturas'].append(update['$push']['lecturas'])
                break


class NotificationEndpointTests(SimpleTestCase):
    def setUp(self):
        from types import SimpleNamespace
        self.users = [SimpleNamespace(pk=i, is_authenticated=True, is_superuser=root, Rol=admin)
                      for i, root, admin in [(1, False, True), (2, True, False), (3, False, False)]]
        self.id = ObjectId()
        self.coll = FakeCollection([{
            '_id': self.id, 'tipo': 'solicitud_contacto', 'titulo': 'Contacto',
            'mensaje': 'Solicitud', 'origen': 'api_contacto', 'prioridad': 'normal',
            'estado': 'activa', 'fecha_creacion': datetime(2026, 11, 6, tzinfo=timezone.utc),
            'destinatarios_roles': ['ADMIN', 'SUPERUSER'], 'lecturas': [],
            'referencia': {'tipo': 'solicitud_contacto', 'id_referencia': ObjectId()},
        }])
        self.mock = patch('apps.mobile_api.notifications.collection', return_value=self.coll).start()
        self.update = patch.object(self.coll, 'update_one', wraps=self.coll.update_one).start()
        self.addCleanup(patch.stopall)
        self.client = APIClient()
        self.base = '/api/mobile/v1/notificaciones/'

    def test_roles_count_and_serialization(self):
        for user, count in zip(self.users, [1, 1, 0]):
            self.client.force_authenticate(user)
            response = self.client.get(self.base)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), count)
            self.assertEqual(self.client.get(self.base + 'no-leidas/count/').data, {'count': count})
            if count:
                doc = response.json()[0]
                self.assertEqual(doc['id'], str(self.id))
                self.assertEqual(doc['fecha_creacion'], '2026-11-06T00:00:00Z')
                self.assertIsInstance(doc['referencia']['id_referencia'], str)
                self.assertFalse(doc['leida'])
                self.assertNotIn('lecturas', doc)

    def test_idempotent_read_and_user_isolation(self):
        self.client.force_authenticate(self.users[0])
        for _ in range(2):
            response = self.client.patch(self.base + f'{self.id}/leer/',
                                         {'usuario_id_sql': 999, 'rol': 'EMPLOYEE'}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data['leida'])
        self.assertEqual(len(self.coll.documents[0]['lecturas']), 1)
        query, update = self.update.call_args.args
        self.assertEqual(query['lecturas.usuario_id_sql'], {'$ne': 1})
        self.assertEqual(query['destinatarios_roles'], 'ADMIN')
        self.assertIn('$push', update)
        self.assertEqual(self.coll.documents[0]['lecturas'][0]['usuario_id_sql'], 1)
        self.assertEqual(self.client.get(self.base + 'no-leidas/count/').data['count'], 0)
        self.client.force_authenticate(self.users[1])
        self.assertEqual(self.client.get(self.base + 'no-leidas/count/').data['count'], 1)

    def test_forbidden_unknown_invalid_and_anonymous(self):
        self.client.force_authenticate(self.users[2])
        for identifier in [str(self.id), str(ObjectId()), 'bad-id']:
            self.assertEqual(self.client.patch(self.base + identifier + '/leer/').status_code, 404)
        self.assertEqual(self.coll.documents[0]['lecturas'], [])
        self.client = APIClient()
        for url, method in [(self.base, 'get'), (self.base + 'no-leidas/count/', 'get'),
                            (self.base + f'{self.id}/leer/', 'patch')]:
            self.assertEqual(getattr(self.client, method)(url).status_code, 401)

    def test_mongo_failure_is_503(self):
        self.client.force_authenticate(self.users[0])
        self.mock.side_effect = ConnectionFailure('secret connection detail')
        with self.assertLogs('apps.mobile_api.notifications', level='ERROR'):
            response = self.client.get(self.base)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.content.decode())

    def test_staff_is_not_business_authority(self):
        self.users[2].is_staff = True
        self.client.force_authenticate(self.users[2])
        self.assertEqual(self.client.get(self.base).data, [])

    def test_reading_does_not_allow_crud(self):
        self.client.force_authenticate(self.users[0])
        self.assertEqual(self.client.post(self.base, {}).status_code, 405)
        self.assertEqual(self.client.delete(self.base + f'{self.id}/').status_code, 404)

    def test_sort_descending(self):
        newer = deepcopy(self.coll.documents[0])
        newer.update(_id=ObjectId(), fecha_creacion=datetime(2026, 11, 7, tzinfo=timezone.utc))
        self.coll.documents.append(newer)
        self.client.force_authenticate(self.users[0])
        self.assertEqual(self.client.get(self.base).data[0]['id'], str(newer['_id']))


class NotificationCommitTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='notification-test')
        department = Departamentos.objects.create(Nombre='Prueba')
        customer = Cliente.objects.create(DepartamentoId=department, Nombre='Prueba', Apellido='SQL',
                                         Telefono='123', Correo='test@example.test', Direccion='Prueba')
        self.contract = Contrato.objects.create(ClienteId=customer, Fecha_Inc=date.today(),
                                               Fecha_Fin=date.today(), Descripcion='Prueba')
        for name in ['Pendiente', 'Pagada', 'Vencida', 'Anulada']:
            EstadoFactura.objects.get_or_create(estado=name)
        self.mongo = patch('apps.transaccion.notificaciones.mongo.collection').start()
        self.addCleanup(patch.stopall)

    def invoice(self, code=123):
        return FacturaSerializer().create(dict(UsuarioId=self.user, ContratoId=self.contract,
                                               Fecha_Emision=date.today(), Hora_Emision='10:00', CodigoFact=code))

    def payment(self, invoice):
        return PagoSerializer().create(dict(FacturaId=invoice, Fecha_Pago=datetime.now(timezone.utc),
                                            Monto_Pagado=10, EstadoPago=True, NumeroRecibo=456))

    def test_invoice_only_after_commit_and_not_on_update(self):
        with transaction.atomic():
            invoice = self.invoice()
            self.mongo.assert_not_called()
        document = self.mongo.return_value.insert_one.call_args.args[0]
        self.assertEqual(document['referencia'], {'tipo': 'factura', 'id_sql': invoice.pk, 'codigo_factura': 123})
        FacturaSerializer().update(invoice, {})
        self.assertEqual(self.mongo.return_value.insert_one.call_count, 1)

    def test_payment_only_after_commit(self):
        invoice = self.invoice()
        self.mongo.reset_mock()
        with transaction.atomic():
            payment = self.payment(invoice)
            self.mongo.assert_not_called()
        doc = self.mongo.return_value.insert_one.call_args.args[0]
        self.assertEqual(doc['referencia'], {'tipo': 'pago', 'id_sql': payment.pk, 'factura_id_sql': invoice.pk})

    def test_rollback_discards_both_events(self):
        with self.assertRaises(ValueError):
            with transaction.atomic():
                self.payment(self.invoice())
                raise ValueError('rollback')
        self.mongo.assert_not_called()
        self.assertEqual(Factura.objects.count(), 0)
        self.assertEqual(Pago.objects.count(), 0)

    def test_invalid_mobile_lines_rollback_invoice_and_event(self):
        from types import SimpleNamespace
        serializer = AtomicInvoiceSerializer(context={'request': SimpleNamespace(user=self.user)})
        with self.assertRaises(Exception):
            with transaction.atomic():
                serializer.create(dict(ContratoId=self.contract, Fecha_Emision=date.today(),
                                       Hora_Emision='10:00', CodigoFact=124,
                                       lineas=[{'ServicioId': 999999, 'Cantidad': 1}]))
        self.mongo.assert_not_called()
        self.assertFalse(Factura.objects.exists())

    def test_mongo_failure_preserves_committed_invoice_and_payment(self):
        self.mongo.side_effect = ConnectionFailure('secret')
        with self.assertLogs('apps.transaccion.notificaciones.mongo', level='ERROR') as logs:
            invoice = self.invoice()
            payment = self.payment(invoice)
        self.assertTrue(Factura.objects.filter(pk=invoice.pk).exists())
        self.assertTrue(Pago.objects.filter(pk=payment.pk).exists())
        self.assertEqual(len(logs.output), 2)
        self.assertNotIn('secret', ''.join(logs.output))
