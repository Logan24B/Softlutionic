"""Read-only administrative access to existing contact-form documents."""
import logging
from django.core.exceptions import ImproperlyConfigured
from pymongo.errors import PyMongoError
from rest_framework import permissions, serializers, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.transaccion.notificaciones.mongo import collection
from .notifications import json_value
from .policy import MobileAuthorizationPolicy as Policy

logger = logging.getLogger(__name__)
CONTACT_COLLECTION = 'solicitudes_contacto'
# Source keys verified by a read-only query of the real collection.
CONTACT_FIELDS = {
    'nombre': 'nombre', 'correo': 'correo', 'telefono': 'telefono',
    'asunto': 'asunto', 'mensaje': 'mensaje', 'estado': 'estado',
    'prioridad': 'prioridad', 'origen': 'origen', 'tipo': 'tipo',
    'fecha_creacion': 'fecha_creacion',
}


class ContactAdminPermission(permissions.BasePermission):
    message = 'No tienes permiso para consultar solicitudes de contacto.'

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and Policy.is_admin(request.user))


class ContactRequestSerializer(serializers.BaseSerializer):
    def to_representation(self, document):
        result = {name: json_value(document.get(source)) for name, source in CONTACT_FIELDS.items()}
        result['id'] = str(document['_id'])
        return result


class ContactUnavailable(APIException):
    status_code = 503
    default_detail = 'Servicio de solicitudes de contacto temporalmente no disponible.'


class ContactStorageError(RuntimeError):
    """Safe exception text for logs; original driver messages may contain secrets."""


class ContactRequestViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, ContactAdminPermission]
    http_method_names = ['get', 'head', 'options']

    def list(self, request):
        try:
            # Reuses the notification MongoClient and configured database, without writes.
            requests = collection().database[CONTACT_COLLECTION]
            projection = {source: 1 for source in CONTACT_FIELDS.values()}
            documents = requests.find({}, projection).sort([('fecha_creacion', -1), ('_id', -1)])
            return Response(ContactRequestSerializer(list(documents), many=True).data)
        except (PyMongoError, ImproperlyConfigured) as exc:
            # Keep traceback and exception class without exposing driver connection text.
            logger.exception('Contact requests unavailable: error=%s', type(exc).__name__,
                             exc_info=(ContactStorageError,
                                       ContactStorageError('Consulta de contacto no disponible.'),
                                       exc.__traceback__))
            raise ContactUnavailable() from None
