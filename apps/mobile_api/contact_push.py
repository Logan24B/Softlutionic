"""Private bridge for notifications already persisted by the contact API."""
import os
from secrets import compare_digest
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transaccion.notificaciones.mongo import collection
from . import push


class ContactPushPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        expected = os.environ.get('CONTACT_PUSH_SECRET', '')
        supplied = request.headers.get('X-Contact-Push-Key', '')
        return (len(expected) >= 32 and
                compare_digest(expected.encode('utf-8'), supplied.encode('utf-8')))


class ContactPushView(APIView):
    authentication_classes = []
    permission_classes = [ContactPushPermission]

    def post(self, request):
        try:
            notification_id = ObjectId(str(request.data.get('notification_id', '')))
        except (InvalidId, TypeError):
            return Response({'detail': 'Invalid notification ID.'}, status=400)
        if not push.enabled():
            return Response({'detail': 'Push unavailable.'}, status=503)
        # Check credentials before claiming: configuration failures remain retryable.
        try:
            push.firebase_app()
            coll = collection()
            document = coll.find_one_and_update(
                {'_id': notification_id, 'tipo': 'solicitud_contacto',
                 'origen': 'api_contacto', 'estado': 'activa',
                 'contact_push_attempted_at': {'$exists': False}},
                {'$set': {'contact_push_attempted_at': datetime.now(timezone.utc)}})
        except Exception as exc:
            push.logger.error('Contact push bridge failed: error=%s', type(exc).__name__)
            return Response({'detail': 'Push unavailable.'}, status=503)
        if document is not None:
            # Existing sender rechecks active SQL accounts, roles and read status.
            # Atomic claim suppresses repeated HTTP calls, including concurrent ones.
            push.send_notification(document)
        # Best effort attempt, never a delivery receipt. No second Mongo notification.
        return Response(status=202)
