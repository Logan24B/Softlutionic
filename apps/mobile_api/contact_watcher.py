"""Small, bounded Mongo sweep; independent of calls from the contact producer."""
import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Thread
from django.db import close_old_connections
from apps.transaccion.notificaciones.mongo import collection
from . import push

logger = logging.getLogger(__name__)
_lock = Lock()
_thread = None
_stop = Event()


def sweep(now=None):
    if not push.enabled():
        return 0
    push.firebase_app()  # Never claim an event without configured Firebase.
    now = now or datetime.now(timezone.utc)
    coll = collection()
    count = 0
    for _ in range(20):
        document = coll.find_one_and_update(
            {'tipo': 'solicitud_contacto', 'origen': 'api_contacto', 'estado': 'activa',
             'fecha_creacion': {'$gte': now - timedelta(minutes=5), '$lte': now},
             'contact_push_attempted_at': {'$exists': False}},
            {'$set': {'contact_push_attempted_at': now}},
            sort=[('fecha_creacion', 1), ('_id', 1)])
        if document is None:
            break
        push.send_notification(document)
        count += 1
    return count


def run():
    logger.warning('Contact notification watcher started (15s interval, 5min window).')
    while not _stop.is_set():
        try:
            close_old_connections()
            count = sweep()
            if count:
                logger.warning('Contact notification watcher: attempted=%s', count)
        except Exception as exc:
            logger.error('Contact notification watcher failed: error=%s', type(exc).__name__)
        finally:
            close_old_connections()
        _stop.wait(15)


def start():
    global _thread
    if os.environ.get('CONTACT_PUSH_POLL_ENABLED', '').lower() != 'true' or not push.enabled():
        return
    with _lock:
        if _thread is None or not _thread.is_alive():
            _stop.clear()
            _thread = Thread(target=run, name='contact-notification-watcher', daemon=True)
            _thread.start()


def stop():
    _stop.set()
