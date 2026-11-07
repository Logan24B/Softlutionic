import os
from unittest.mock import patch, Mock
from bson import ObjectId
from django.test import SimpleTestCase
from rest_framework.test import APIClient


@patch.dict(os.environ, {'CONTACT_PUSH_SECRET': 's' * 40})
class ContactPushTests(SimpleTestCase):
    url = '/api/mobile/v1/push/contact/'

    def call(self, body=None, key='s' * 40):
        return APIClient().post(self.url, body or {'notification_id': str(ObjectId())},
                                format='json', HTTP_X_CONTACT_PUSH_KEY=key)

    @patch('apps.mobile_api.contact_push.collection')
    def test_missing_or_wrong_secret_never_accesses_mongo(self, collection):
        for key in ('', 'wrong'):
            self.assertEqual(self.call(key=key).status_code, 403)
        collection.assert_not_called()

    @patch.dict(os.environ, {'CONTACT_PUSH_SECRET': ''})
    def test_unconfigured_secret_fails_closed(self):
        self.assertEqual(self.call(key='').status_code, 403)

    @patch('apps.mobile_api.contact_push.collection')
    def test_invalid_id_never_accesses_mongo(self, collection):
        self.assertEqual(self.call({'notification_id': 'bad'}).status_code, 400)
        collection.assert_not_called()

    @patch('apps.mobile_api.contact_push.push.enabled', return_value=False)
    @patch('apps.mobile_api.contact_push.collection')
    def test_disabled_fcm_does_not_claim_notification(self, collection, enabled):
        self.assertEqual(self.call().status_code, 503)
        collection.assert_not_called()

    @patch('apps.mobile_api.contact_push.push.enabled', return_value=True)
    @patch('apps.mobile_api.contact_push.push.firebase_app', side_effect=ValueError)
    @patch('apps.mobile_api.contact_push.collection')
    def test_missing_firebase_credentials_does_not_claim(self, collection, app, enabled):
        self.assertEqual(self.call().status_code, 503)
        collection.assert_not_called()

    @patch('apps.mobile_api.contact_push.push.enabled', return_value=True)
    @patch('apps.mobile_api.contact_push.push.firebase_app')
    @patch('apps.mobile_api.contact_push.push.send_notification')
    @patch('apps.mobile_api.contact_push.collection')
    def test_only_persisted_contact_is_sent_and_repeat_is_ignored(self, collection, send, app, enabled):
        document = {'_id': ObjectId(), 'destinatarios_roles': ['ADMIN', 'SUPERUSER']}
        collection.return_value.find_one_and_update.side_effect = [document, None]
        body = {'notification_id': str(document['_id']), 'destinatarios_roles': ['EMPLOYEE']}
        self.assertEqual(self.call(body).status_code, 202)
        self.assertEqual(self.call(body).status_code, 202)
        send.assert_called_once_with(document)
        query = collection.return_value.find_one_and_update.call_args.args[0]
        self.assertEqual(query['tipo'], 'solicitud_contacto')
        self.assertEqual(query['origen'], 'api_contacto')
        self.assertEqual(query['estado'], 'activa')
        self.assertEqual(query['contact_push_attempted_at'], {'$exists': False})
        collection.return_value.insert_one.assert_not_called()

    @patch('apps.mobile_api.contact_push.push.enabled', return_value=True)
    @patch('apps.mobile_api.contact_push.push.firebase_app')
    @patch('apps.mobile_api.contact_push.push.send_notification')
    @patch('apps.mobile_api.contact_push.collection', side_effect=RuntimeError)
    def test_mongo_failure_does_not_dispatch(self, collection, send, app, enabled):
        self.assertEqual(self.call().status_code, 503)
        send.assert_not_called()
