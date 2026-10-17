import os


def database_config():
    # Si no existe DB_ENV, se utilizará SQL Server local.
    environment = os.getenv('DB_ENV', 'local').lower()

    # =========================
    # AZURE SQL DATABASE
    # =========================
    if environment == 'azure':
        return {
            'ENGINE': 'SoftFactur.db.backends.mssql_no_mars',
            'NAME': 'softlutionic-sistema-db',
            'USER': 'adminsoftlutionic',
            'PASSWORD': os.environ['DB_PASSWORD'],
            'HOST': 'sql-softlutionic2.database.windows.net',
            'PORT': '1433',

            'OPTIONS': {
                'driver': 'ODBC Driver 18 for SQL Server',
                'extra_params': (
                    'Encrypt=yes;'
                    'TrustServerCertificate=no'
                ),
                'connection_timeout': 30,
            },
        }

    # =========================
    # SQL SERVER LOCAL
    # =========================
    return {
        'ENGINE': 'SoftFactur.db.backends.mssql_no_mars',
        'NAME': 'BDsofactur',
        'HOST': r'localhost\SQLEXPRESS',
        'PORT': '',

        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'extra_params': (
                'Encrypt=yes;'
                'TrustServerCertificate=yes'
            ),
            'connection_timeout': 30,
        },
    }
