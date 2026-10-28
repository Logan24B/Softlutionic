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
        Cliente.objects.create(DepartamentoId_id=pk,Nombre='Ana',Apellido='PÃ©rez',Cedula='001-010190-0001A',Telefono='+505 8888 1111',Correo='ana@example.test',Direccion='Centro')
        self.assertEqual(self.client.delete(f'/api/mobile/v1/departamentos/{pk}/').status_code,409)
    def test_invoice_atomic_rollback_and_totals(self):
        self.login('employee-test')
        dep=Departamentos.objects.create(Nombre='Managua')
        customer=Cliente.objects.create(DepartamentoId=dep,Nombre='Ana',Apellido='PÃ©rez',Telefono='+505 8888 2222',Correo='ap@example.test',Direccion='Centro')
        kind, _ = TipoContrato.objects.get_or_create(Nombre='Servicio mensual')
        contract=Contrato.objects.create(ClienteId=customer,TipoContratoId=kind,Fecha_Inc=date.today(),Fecha_Fin=date.today()+timedelta(days=60),Descripcion='Contrato real de prueba')
        for state in ['Pendiente','Pagada','Vencida','Anulada']: EstadoFactura.objects.get_or_create(estado=state)
        service=Servicio.objects.create(Nombre_Servicio='Soporte',Descripcion='Soporte tÃ©cnico',Precio=150,Duracion='1 hora')
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


class MobileAuthorizationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.root = User.objects.create_superuser(username='root', password='test-pass')
        self.admin = User.objects.create_user(username='manager', password='test-pass', Rol=True)
        self.other = User.objects.create_user(username='other', password='test-pass', Rol=True)
        self.employee = User.objects.create_user(username='worker', password='test-pass')
        self.service = Servicio.objects.create(Nombre_Servicio='Support', Descripcion='Support', Precio=10, Duracion='1h')
        self.client = APIClient()

    def as_user(self, actor):
        self.client.force_authenticate(actor)

    def payload(self, **overrides):
        return dict(PrimerNombre='Nuevo', SegundoNombre='Usuario', Email='new@example.test',
                    Usuario='new', Contrasena='Strong-password-938!', Rol=False, **overrides)

    def url(self, user):
        return f'/api/mobile/v1/usuarios/{user.pk}/'

    def test_identity_and_login(self):
        for actor, role in [(self.root, 'Superusuario'), (self.admin, 'Administrador'), (self.employee, 'Empleado')]:
            with self.subTest(role=role):
                self.as_user(actor)
                user = self.client.get('/api/mobile/v1/auth/me/').data['user']
                self.assertEqual(user['is_superuser'], actor.is_superuser)
                self.assertEqual(user['is_staff'], actor.is_staff)
                self.assertEqual(user['rol_descripcion'], role)
                self.assertTrue({'id', 'Usuario', 'PrimerNombre', 'SegundoNombre', 'Email', 'Rol', 'is_active'} <= user.keys())
                self.assertNotIn('password', user)
                self.assertNotIn('Contrasena', user)
        self.client.force_authenticate(None)
        response = self.client.post('/api/mobile/v1/auth/login/', {'username': 'root', 'password': 'test-pass'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['user']['is_superuser'])
        self.assertTrue({'access', 'refresh'} <= response.data.keys())

    def test_superuser_manages_admin_and_employee(self):
        self.as_user(self.root)
        payload = self.payload()
        payload['Rol'] = True
        self.assertEqual(self.client.post('/api/mobile/v1/usuarios/', payload).status_code, 201)
        for target in [self.other, self.employee]:
            self.assertEqual(self.client.patch(self.url(target), {'PrimerNombre': 'Editado'}).status_code, 200)
        for role in [True, False]:
            self.assertEqual(self.client.patch(self.url(self.employee), {'Rol': role}).status_code, 200)
        self.assertEqual(self.client.delete(self.url(self.other)).status_code, 204)

    def test_admin_manages_only_employees(self):
        self.as_user(self.admin)
        self.assertEqual(self.client.post('/api/mobile/v1/usuarios/', self.payload()).status_code, 201)
        self.assertEqual(self.client.patch(self.url(self.employee), {'PrimerNombre': 'Editado', 'is_active': False, 'Contrasena': 'Changed-password-938!'}).status_code, 200)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)
        self.assertTrue(self.employee.check_password('Changed-password-938!'))
        data = self.client.get('/api/mobile/v1/usuarios/').data
        self.assertTrue(all(not u['Rol'] and not u['is_superuser'] for u in data))
        self.assertEqual(self.client.get('/api/mobile/v1/usuarios/administradores/').data, [])
        self.assertEqual(self.client.delete(self.url(self.employee)).status_code, 204)

    def test_admin_cannot_create_or_promote_admin(self):
        self.as_user(self.admin)
        payload = self.payload()
        payload['Rol'] = True
        self.assertEqual(self.client.post('/api/mobile/v1/usuarios/', payload).status_code, 403)
        for role in [True, 'true', '1']:
            self.assertEqual(self.client.patch(self.url(self.employee), {'Rol': role}).status_code, 403)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.Rol)

    def test_admin_cannot_manage_admin_or_superuser(self):
        self.as_user(self.admin)
        for target in [self.admin, self.other, self.root]:
            for method in ['get', 'patch', 'put', 'delete']:
                with self.subTest(target=target.username, method=method):
                    response = getattr(self.client, method)(self.url(target), {'Rol': False, 'is_active': False, 'Contrasena': 'Changed-password-938!'})
                    self.assertEqual(response.status_code, 403)
            target.refresh_from_db()
            self.assertTrue(target.Rol)
            self.assertTrue(target.is_active)
            self.assertTrue(target.check_password('test-pass'))

    def test_employee_services_and_users(self):
        self.as_user(self.employee)
        base = '/api/mobile/v1/servicios/'
        self.assertEqual(self.client.get(base).status_code, 200)
        self.assertEqual(self.client.get(f'{base}{self.service.pk}/').status_code, 200)
        self.assertEqual(self.client.post(base, {}).status_code, 403)
        for method in ['put', 'patch', 'delete']:
            self.assertEqual(getattr(self.client, method)(f'{base}{self.service.pk}/', {}).status_code, 403)
        for url in ['/api/mobile/v1/usuarios/', self.url(self.employee), '/api/mobile/v1/usuarios/empleados/', '/api/mobile/v1/usuarios/administradores/']:
            for method in ['get', 'post', 'put', 'patch', 'delete']:
                self.assertEqual(getattr(self.client, method)(url, {}).status_code, 403)
        schema = self.client.get('/api/mobile/v1/schema/').data
        caps = next(m['permissions'] for m in schema if m['name'] == 'servicios')
        self.assertEqual(caps, dict(read=True, create=False, update=False, delete=False))

    def test_protected_flags_rejected_for_every_actor(self):
        for actor in [self.root, self.admin, self.employee]:
            self.as_user(actor)
            for field in ['is_superuser', 'is_staff']:
                for value in [True, False]:
                    payload = self.payload()
                    payload[field] = value
                    self.assertEqual(self.client.post('/api/mobile/v1/usuarios/', payload).status_code, 403)
                    for method in ['patch', 'put']:
                        self.assertEqual(getattr(self.client, method)(self.url(self.employee), {field: value}).status_code, 403)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_superuser)
        self.assertFalse(self.employee.is_staff)

    def test_superuser_accounts_cannot_be_modified(self):
        self.as_user(self.root)
        for method in ['patch', 'put', 'delete']:
            self.assertEqual(getattr(self.client, method)(self.url(self.root), {'PrimerNombre': 'Changed'}).status_code, 403)

    def test_staff_is_not_business_authority_and_superuser_has_priority(self):
        from .registry import capabilities
        self.employee.is_staff = True
        self.assertFalse(capabilities(self.employee, 'usuarios')['read'])
        self.assertFalse(capabilities(self.employee, 'servicios')['create'])
        self.root.Rol = False
        self.assertTrue(capabilities(self.root, 'usuarios')['create'])

    def test_service_admin_crud_and_existing_limits(self):
        for actor in [self.admin, self.root]:
            self.as_user(actor)
            response = self.client.post('/api/mobile/v1/servicios/', {'Nombre_Servicio': actor.username, 'Descripcion': 'Support', 'Precio': 20, 'Duracion': '1h'})
            self.assertEqual(response.status_code, 201, response.data)
            url = f"/api/mobile/v1/servicios/{response.data['id']}/"
            self.assertEqual(self.client.patch(url, {'Precio': 30}).status_code, 200)
            self.assertEqual(self.client.delete(url).status_code, 204)
            self.assertEqual(self.client.post('/api/mobile/v1/moras/', {}).status_code, 403)
            self.assertEqual(self.client.delete('/api/mobile/v1/facturas/999/').status_code, 403)


    def test_superuser_user_visibility_list_and_details(self):
        self.as_user(self.root)
        response = self.client.get('/api/mobile/v1/usuarios/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({u['id'] for u in response.data},
                         {self.root.pk, self.admin.pk, self.other.pk, self.employee.pk})
        for target, description in [(self.root, 'Superusuario'), (self.admin, 'Administrador'),
                                    (self.employee, 'Empleado')]:
            with self.subTest(target=target.username):
                response = self.client.get(self.url(target))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['rol_descripcion'], description)
                for field in ['is_superuser', 'Rol', 'is_staff', 'is_active']:
                    self.assertEqual(response.data[field], getattr(target, field))
                listed = next(u for u in self.client.get('/api/mobile/v1/usuarios/').data
                              if u['id'] == target.pk)
                self.assertEqual(listed, response.data)

    def test_admin_user_visibility_list_and_details(self):
        self.as_user(self.admin)
        response = self.client.get('/api/mobile/v1/usuarios/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([u['id'] for u in response.data], [self.employee.pk])
        self.assertFalse(response.data[0]['is_superuser'])
        self.assertFalse(response.data[0]['Rol'])
        self.assertEqual(self.client.get(self.url(self.employee)).status_code, 200)
        for target in [self.admin, self.other, self.root]:
            with self.subTest(target=target.username):
                response = self.client.get(self.url(target))
                self.assertEqual(response.status_code, 403)
                self.assertNotIn('Usuario', response.data)
        for action in ['administradores', 'empleados']:
            response = self.client.get(f'/api/mobile/v1/usuarios/{action}/')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(all(not u['Rol'] and not u['is_superuser'] for u in response.data))

    def test_employee_user_visibility_list_and_details(self):
        self.as_user(self.employee)
        self.assertEqual(self.client.get('/api/mobile/v1/usuarios/').status_code, 403)
        for target in [self.employee, self.admin, self.root]:
            self.assertEqual(self.client.get(self.url(target)).status_code, 403)
