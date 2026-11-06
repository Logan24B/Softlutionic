from types import SimpleNamespace
from django.test import SimpleTestCase
from rest_framework.test import APIClient
from .push import DeviceInput


class PushRegistrationBoundaryTests(SimpleTestCase):
    def test_registration_and_revocation_require_jwt(self):
        for path in ('/api/mobile/v1/push/devices/', '/api/mobile/v1/push/devices/unregister/'):
            with self.subTest(path=path):
                self.assertEqual(APIClient().post(path, {}, format='json').status_code, 401)

    def test_invalid_jwt_cannot_register(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid')
        self.assertEqual(client.post('/api/mobile/v1/push/devices/', {}, format='json').status_code, 401)

    def test_empty_token_rejected_before_database_access(self):
        client = APIClient()
        client.force_authenticate(user=SimpleNamespace(pk=1, is_authenticated=True))
        self.assertEqual(client.post('/api/mobile/v1/push/devices/', {'token': ''}, format='json').status_code, 400)

    def test_client_cannot_choose_user_or_role(self):
        serializer = DeviceInput(data={'token': 'a' * 32, 'user_id': 99, 'rol': 'SUPERUSER'})
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('user_id', serializer.validated_data)
        self.assertNotIn('rol', serializer.validated_data)
