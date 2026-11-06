"""Shared, lazy MongoDB access. No network access during Django startup."""
import logging
import os
from datetime import datetime, timezone
from threading import Lock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from pymongo import MongoClient

logger = logging.getLogger(__name__)
_lock = Lock()
_client = None
_pid = None


def collection():
    global _client, _pid
    with _lock:
        if _client is None or _pid != os.getpid():
            if not settings.MONGODB_URI:
                raise ImproperlyConfigured('MONGODB_URI no configurada.')
            _client = MongoClient(
                settings.MONGODB_URI, tz_aware=True, connect=False,
                serverSelectionTimeoutMS=3000, connectTimeoutMS=3000,
                socketTimeoutMS=3000, timeoutMS=5000,
            )
            _pid = os.getpid()
        return _client[settings.MONGODB_DATABASE][settings.MONGODB_NOTIFICATIONS_COLLECTION]


def notify_after_commit(instance):
    """Called after the complete serializer create, inside its SQL transaction."""
    from apps.transaccion.factura.models import Factura

    if isinstance(instance, Factura):
        kind, title = 'factura_generada', 'Nueva factura generada'
        reference = {'tipo': 'factura', 'id_sql': instance.pk,
                     'codigo_factura': instance.CodigoFact}
        message = f'Se registró la factura {instance.CodigoFact}.'
    else:
        kind, title = 'pago_registrado', 'Nuevo pago registrado'
        reference = {'tipo': 'pago', 'id_sql': instance.pk,
                     'factura_id_sql': instance.FacturaId_id}
        message = f'Se registró el pago con recibo {instance.NumeroRecibo}.'

    def publish():
        try:
            collection().insert_one({
                'tipo': kind, 'titulo': title, 'mensaje': message,
                'origen': 'django_softlutionic', 'referencia': reference,
                'prioridad': 'normal', 'estado': 'activa',
                'destinatarios_roles': ['ADMIN', 'SUPERUSER'],
                'fecha_creacion': datetime.now(timezone.utc), 'lecturas': [],
            })
        except Exception as exc:
            # Do not log the exception text: driver errors can contain connection data.
            logger.error('Mongo notification failed after SQL commit: tipo=%s id_sql=%s error=%s',
                         kind, reference['id_sql'], type(exc).__name__)

    transaction.on_commit(publish, using=instance._state.db)
