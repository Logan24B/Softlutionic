from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from django.test import SimpleTestCase
from .contact_watcher import sweep


class ContactWatcherTests(SimpleTestCase):
    @patch('apps.mobile_api.contact_watcher.push.enabled', return_value=False)
    @patch('apps.mobile_api.contact_watcher.collection')
    def test_disabled_does_not_connect(self, coll, enabled):
        self.assertEqual(sweep(), 0)
        coll.assert_not_called()

    @patch('apps.mobile_api.contact_watcher.push.enabled', return_value=True)
    @patch('apps.mobile_api.contact_watcher.push.firebase_app', side_effect=ValueError)
    @patch('apps.mobile_api.contact_watcher.collection')
    def test_missing_credentials_never_claim(self, coll, firebase, enabled):
        with self.assertRaises(ValueError):
            sweep()
        coll.assert_not_called()

    @patch('apps.mobile_api.contact_watcher.push.enabled', return_value=True)
    @patch('apps.mobile_api.contact_watcher.push.firebase_app')
    @patch('apps.mobile_api.contact_watcher.push.send_notification')
    @patch('apps.mobile_api.contact_watcher.collection')
    def test_claim_is_bounded_recent_contact_only_and_uses_existing_sender(self, coll, send, firebase, enabled):
        document = {'_id': 'persisted', 'destinatarios_roles': ['ADMIN', 'SUPERUSER']}
        coll.return_value.find_one_and_update.side_effect = [document, None]
        now = datetime.now(timezone.utc)
        self.assertEqual(sweep(now), 1)
        send.assert_called_once_with(document)
        query, update = coll.return_value.find_one_and_update.call_args.args
        self.assertEqual(query['tipo'], 'solicitud_contacto')
        self.assertEqual(query['origen'], 'api_contacto')
        self.assertEqual(query['estado'], 'activa')
        self.assertEqual(query['fecha_creacion'], {'$gte': now-timedelta(minutes=5), '$lte': now})
        self.assertEqual(query['contact_push_attempted_at'], {'$exists': False})
        self.assertEqual(update['$set']['contact_push_attempted_at'], now)
        coll.return_value.insert_one.assert_not_called()

    @patch('apps.mobile_api.contact_watcher.push.enabled', return_value=True)
    @patch('apps.mobile_api.contact_watcher.push.firebase_app')
    @patch('apps.mobile_api.contact_watcher.push.send_notification')
    @patch('apps.mobile_api.contact_watcher.collection')
    def test_backlog_is_limited_to_twenty_per_sweep(self, coll, send, firebase, enabled):
        coll.return_value.find_one_and_update.return_value = {'_id': 'persisted'}
        self.assertEqual(sweep(), 20)
        self.assertEqual(send.call_count, 20)
