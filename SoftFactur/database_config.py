"""Local SQL Server is the only active data source."""


def database_config():
    return {
        'ENGINE': 'SoftFactur.db.backends.mssql_no_mars',
        'NAME': 'BDsofactur',
        'HOST': r'localhost\SQLEXPRESS', 'PORT': '',
        'OPTIONS': {'driver': 'ODBC Driver 18 for SQL Server',
                    'extra_params': 'Encrypt=yes;TrustServerCertificate=yes',
                    'connection_timeout': 30},
    }
