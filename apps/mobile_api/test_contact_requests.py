"""Contact authorization tests: isolated SQL auth, no Mongo reads or writes."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class ContactAuthorizationTests(TestCase):
    url = '/api/mobile/v1/solicitudes-contacto/'

    def authenticated(self, **roles):
        user = get_user_model().objects.create_user(username='contact-test', **roles)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer '+str(RefreshToken.for_user(user).access_token))
        return client

    def test_anonymous_requires_jwt(self):
        self.assertEqual(APIClient().get(self.url).status_code, 401)

    def test_staff_without_business_role_is_denied_and_has_no_schema(self):
        client = self.authenticated(is_staff=True, Rol=False)
        self.assertEqual(client.get(self.url).status_code, 403)
        self.assertNotIn('solicitudes-contacto', [m['name'] for m in client.get('/api/mobile/v1/schema/').data])

    def test_admin_schema_is_read_only_and_post_is_rejected(self):
        client = self.authenticated(Rol=True)
        module = next(m for m in client.get('/api/mobile/v1/schema/').data if m['name']=='solicitudes-contacto')
        self.assertEqual(module['permissions'], dict(read=True, create=False, update=False, delete=False))
        self.assertEqual(client.post(self.url, {}, format='json').status_code, 405)

    def test_superuser_precedes_false_business_role(self):
        client = self.authenticated(is_superuser=True, Rol=False)
        self.assertIn('solicitudes-contacto', [m['name'] for m in client.get('/api/mobile/v1/schema/').data])
        self.assertEqual(client.post(self.url, {}, format='json').status_code, 405)
