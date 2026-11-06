"""JWT-bound device registration and private, data-only FCM delivery."""
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from threading import Lock, BoundedSemaphore
from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from pymongo.errors import PyMongoError
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.transaccion.notificaciones.mongo import collection
from .notifications import MongoUnavailable, visible_filter

logger = logging.getLogger(__name__)
_firebase_lock = Lock()
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='mobile-fcm')
_capacity = BoundedSemaphore(100)


def devices():
    return collection().database['mobile_push_devices']


def token_key(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def enabled():
    return os.environ.get('FCM_ENABLED', '').lower() in ('true', '1', 'yes')


def firebase_app():
    import firebase_admin
    from firebase_admin import credentials
    with _firebase_lock:
        try:
            return firebase_admin.get_app('softlutionic')
        except ValueError:
            raw = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
            if not raw and not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                raise ImproperlyConfigured('Firebase server credentials are missing.')
            credential = credentials.Certificate(json.loads(raw)) if raw else credentials.ApplicationDefault()
            return firebase_admin.initialize_app(credential, {'httpTimeout': 10}, name='softlutionic')


class DeviceInput(serializers.Serializer):
    token = serializers.CharField(min_length=20, max_length=4096, trim_whitespace=True)
    previous_token = serializers.CharField(min_length=20, max_length=4096, required=False)


class DeviceThrottle(UserRateThrottle):
    rate = '20/min'


class PushDeviceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DeviceThrottle]
    unregister = False

    def post(self, request):
        serializer = DeviceInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        try:
            coll = devices()
            key = token_key(values['token'])
            if self.unregister:
                coll.delete_one({'_id': key, 'user_id': request.user.pk})
                return Response(status=204)
            # A device token belongs to the currently authenticated account only.
            coll.update_one({'_id': key}, {'$set': {
                'token': values['token'], 'user_id': request.user.pk,
                'updated_at': datetime.now(timezone.utc),
            }}, upsert=True)
            old = values.get('previous_token')
            if old and old != values['token']:
                coll.delete_one({'_id': token_key(old), 'user_id': request.user.pk})
        except (PyMongoError, ImproperlyConfigured) as exc:
            logger.error('Push device registration failed: error=%s', type(exc).__name__)
            raise MongoUnavailable()
        return Response({'user_id': str(request.user.pk)}, status=200)


def send_notification(document):
    """Called only after a notification is persisted. Failures never undo SQL."""
    if not enabled():
        return
    try:
        from firebase_admin import messaging
        app = firebase_app()
        coll = devices()
        # Re-evaluate current SQL roles; never trust a role stored on a device.
        for device in coll.find({}, {'token': 1, 'user_id': 1}):
            user = get_user_model().objects.filter(pk=device.get('user_id'), is_active=True).first()
            if user is None:
                coll.delete_one({'_id': device['_id']})
                continue
            if visible_filter(user)['destinatarios_roles'] not in document.get('destinatarios_roles', []):
                continue
            if any(read.get('usuario_id_sql') == user.pk for read in document.get('lecturas', [])):
                continue
            try:
                messaging.send(messaging.Message(
                    token=device['token'],
                    data={'notification_id': str(document['_id']), 'user_id': str(user.pk),
                          'tipo': str(document.get('tipo') or '')},
                    android=messaging.AndroidConfig(priority='high', ttl=300),
                ), app=app)
            except messaging.UnregisteredError:
                coll.delete_one({'_id': device['_id'], 'token': device['token']})
            except Exception as exc:
                logger.error('FCM delivery failed: error=%s', type(exc).__name__)
    except Exception as exc:
        logger.error('FCM dispatch failed: error=%s', type(exc).__name__)


def enqueue_notification(document):
    """Bounded best-effort background send; never delays the financial response."""
    if not enabled():
        return
    if not _capacity.acquire(blocking=False):
        logger.error('FCM queue full; notification remains available through the API.')
        return

    def deliver():
        try:
            close_old_connections()
            send_notification(document)
        finally:
            close_old_connections()
            _capacity.release()

    try:
        _executor.submit(deliver)
    except Exception as exc:
        _capacity.release()
        logger.error('FCM queue failed: error=%s', type(exc).__name__)
