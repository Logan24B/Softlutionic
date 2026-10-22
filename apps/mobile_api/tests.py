from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.catalogos.departamentos.models import Departamentos
from apps.catalogos.clientes.models import Cliente
from apps.catalogos.servicios.models import Servicio
from apps.transaccion.contratos.models import Contrato, TipoContrato
from apps.transaccion.factura.models import EstadoFactura, Factura

class MobileApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username='admin-test', email='admin@example.test', password='test-pass', Rol=True)
        self.employee = get_user_model().objects.create_user(username='employee-test', password='test-pass')
        self.client = APIClient()
    def login(self, user='admin-test'):
        response = self.client.post('/api/mobile/v1/auth/login/', {'username':user, 'password':'test-pass'})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+response.data['access'])
        return response.data
    def test_jwt_email_refresh_and_web_coexist(self):
        data=self.login('admin@example.test')
        self.assertEqual(self.client.get('/api/mobile/v1/auth/me/').status_code,200)
        self.assertEqual(self.client.post('/api/mobile/v1/auth/refresh/', {'refresh':data['refresh']}).status_code,200)
        web=APIClient()
        self.assertEqual(web.post('/api/auth/login/', {'usuario':'admin-test','contrasena':'test-pass'}).status_code,200)
        self.assertEqual(web.get('/api/auth/session/').status_code,200)
    def test_anonymous_denied_and_employee_permissions(self):
        self.assertEqual(self.client.get('/api/mobile/v1/clientes/').status_code,401)
        self.login('employee-test')
        self.assertEqual(self.client.get('/api/mobile/v1/usuarios/').status_code,403)
        self.assertEqual(self.client.get('/api/mobile/v1/dashboard/facturacion/').status_code,403)
        self.assertEqual(self.client.post('/api/mobile/v1/moras/', {}).status_code,403)
        names=[m['name'] for m in self.client.get('/api/mobile/v1/schema/').data]
        self.assertNotIn('usuarios',names)
        self.assertIn('clientes',names)
    def test_crud_validation_and_protected_dependency(self):
        self.login()
        response=self.client.post('/api/mobile/v1/departamentos/', {'Nombre':'Managua'})
        self.assertEqual(response.status_code,201)
        pk=response.data['id']
        self.assertEqual(self.client.patch(f'/api/mobile/v1/departamentos/{pk}/', {'Nombre':'Masaya'}).status_code,200)
        self.assertEqual(self.client.post('/api/mobile/v1/departamentos/', {'Nombre':'Masaya'}).status_code,400)
        Cliente.objects.create(DepartamentoId_id=pk,Nombre='Ana',Apellido='Pérez',Cedula='001-010190-0001A',Telefono='+505 8888 1111',Correo='ana@example.test',Direccion='Centro')
        self.assertEqual(self.client.delete(f'/api/mobile/v1/departamentos/{pk}/').status_code,409)
    def test_invoice_atomic_rollback_and_totals(self):
        self.login('employee-test')
        dep=Departamentos.objects.create(Nombre='Managua')
        customer=Cliente.objects.create(DepartamentoId=dep,Nombre='Ana',Apellido='Pérez',Telefono='+505 8888 2222',Correo='ap@example.test',Direccion='Centro')
        kind, _ = TipoContrato.objects.get_or_create(Nombre='Servicio mensual')
        contract=Contrato.objects.create(ClienteId=customer,TipoContratoId=kind,Fecha_Inc=date.today(),Fecha_Fin=date.today()+timedelta(days=60),Descripcion='Contrato real de prueba')
        for state in ['Pendiente','Pagada','Vencida','Anulada']: EstadoFactura.objects.get_or_create(estado=state)
        service=Servicio.objects.create(Nombre_Servicio='Soporte',Descripcion='Soporte técnico',Precio=150,Duracion='1 hora')
        payload={'ContratoId':contract.pk,'CodigoFact':10001,'Fecha_Emision':date.today().isoformat(),'Hora_Emision':'10:00:00','lineas':[{'ServicioId':service.pk,'Cantidad':2},{'ServicioId':999999,'Cantidad':1}]}
        bad=self.client.post('/api/mobile/v1/facturas/',payload,format='json')
        self.assertEqual(bad.status_code,400)
        self.assertFalse(Factura.objects.filter(CodigoFact=10001).exists())
        payload['lineas']=payload['lineas'][:1]
        good=self.client.post('/api/mobile/v1/facturas/',payload,format='json')
        self.assertEqual(good.status_code,201,good.data)
        invoice=Factura.objects.get(CodigoFact=10001)
        self.assertEqual(invoice.UsuarioId,self.employee)
        self.assertEqual(invoice.Monto_Total,300)
        self.assertEqual(invoice.Fecha_Vencimiento, date.today()+timedelta(days=30))
        self.assertEqual(self.client.delete(f'/api/mobile/v1/facturas/{invoice.pk}/').status_code,403)
