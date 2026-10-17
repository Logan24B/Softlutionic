"""Run the application with Waitress, including a database readiness check."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import time


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    logs = root / '.runtime' / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[
            RotatingFileHandler(
                logs / 'server.log', maxBytes=5_000_000,
                backupCount=5, encoding='utf-8',
            ),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger('softfactur.startup')
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoftFactur.settings')
        os.environ['SOFTFACTUR_DEBUG'] = 'false'
        from django.core.wsgi import get_wsgi_application
        from django.db import connections
        from waitress import serve

        application = get_wsgi_application()
        for attempt in range(1, 13):
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                break
            except Exception:
                connections.close_all()
                if attempt == 12:
                    raise
                logger.warning('SQL Server not ready; retry %s/12 in 10 seconds', attempt)
                time.sleep(10)
        connections.close_all()
        logger.info('Starting Waitress on 0.0.0.0:8000')
        serve(application, listen='0.0.0.0:8000')
    except Exception:
        logger.exception('Application stopped with an error')
        raise


if __name__ == '__main__':
    main()
