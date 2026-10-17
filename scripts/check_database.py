"""Read-only Django connection check. Never print provider exception messages."""
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoftFactur.settings')


def main():
    try:
        import django
        django.setup()
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT DB_NAME(), CONVERT(nvarchar(128), SERVERPROPERTY(\'Edition\'))')
            database, edition = cursor.fetchone()
        connection.close()
        print(json.dumps({'connected': True, 'database': database, 'edition': edition}))
        return 0
    except Exception as error:
        # Extract identifiers only; messages may contain authentication details.
        args = getattr(error, 'args', ())
        state = args[0] if args and isinstance(args[0], str) and re.fullmatch(r'[A-Z0-9]{5}', args[0]) else None
        numbers = sorted(set(re.findall(r'\((\d{3,6})\)', str(error))))
        print(json.dumps({'connected': False, 'error_type': type(error).__name__,
                          'sqlstate': state, 'sql_error_numbers': numbers}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
