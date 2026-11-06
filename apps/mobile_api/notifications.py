"""Authenticated Mongo notifications; SQL notification APIs remain independent."""
import logging
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from django.core.exceptions import ImproperlyConfigured
from pymongo.errors import PyMongoError
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.transaccion.notificaciones.mongo import collection

logger = logging.getLogger(__name__)


def visible_filter(user):
    role = 'SUPERUSER' if user.is_superuser else ('ADMIN' if user.Rol else 'EMPLOYEE')
    return {'destinatarios_roles': role}


def json_value(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_value(item) for item in value]
    return value


class NotificationSerializer(serializers.BaseSerializer):
    def to_representation(self, document):
        result = {key: json_value(document.get(key)) for key in (
            'tipo', 'titulo', 'mensaje', 'origen', 'prioridad', 'estado',
            'fecha_creacion', 'referencia')}
        result['id'] = str(document['_id'])
        result['leida'] = any(read.get('usuario_id_sql') == self.context['user'].pk
                             for read in document.get('lecturas', []))
        return result


class MongoUnavailable(APIException):
    status_code = 503
    default_detail = 'Servicio de notificaciones temporalmente no disponible.'


class NotificationViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc, (PyMongoError, ImproperlyConfigured)):
            logger.error('Mongo notification request failed: action=%s error=%s',
                         self.action, type(exc).__name__)
            exc = MongoUnavailable()
        return super().handle_exception(exc)

    def serialize(self, document, many=False):
        return NotificationSerializer(document, many=many, context={'user': self.request.user}).data

    def list(self, request):
        documents = collection().find(visible_filter(request.user)).sort([
            ('fecha_creacion', -1), ('_id', -1)])
        return Response(self.serialize(list(documents), many=True))

    @action(detail=False, methods=['get'], url_path='no-leidas/count')
    def unread_count(self, request):
        query = visible_filter(request.user)
        query['lecturas.usuario_id_sql'] = {'$ne': request.user.pk}
        return Response({'count': collection().count_documents(query)})

    @action(detail=True, methods=['patch'], url_path='leer')
    def read(self, request, pk=None):
        try:
            object_id = ObjectId(pk)
        except (InvalidId, TypeError):
            raise NotFound('Notificación no encontrada.')
        query = dict(visible_filter(request.user), _id=object_id)
        coll = collection()
        # Predicate is rechecked atomically, even with concurrent requests.
        coll.update_one(dict(query, **{'lecturas.usuario_id_sql': {'$ne': request.user.pk}}),
                        {'$push': {'lecturas': {'usuario_id_sql': request.user.pk,
                                              'fecha_lectura': datetime.now(timezone.utc)}}})
        document = coll.find_one(query)
        if document is None:
            raise NotFound('Notificación no encontrada.')
        return Response(self.serialize(document))
