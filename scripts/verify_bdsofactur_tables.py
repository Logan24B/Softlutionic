import pyodbc


CONNECTION = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost,1433;'
    'DATABASE=BDsofactur;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
    'Encrypt=no'
)

EXPECTED_TABLES = (
    'Clientes',
    'Usuarios',
    'Contratos',
    'Servicios',
    'Facturas',
    'Detalle_Factura',
    'Pagos',
    'Mora',
    'Notificaciones',
    'LogAuditoria',
)

placeholders = ','.join('?' for _ in EXPECTED_TABLES)
query = f'SELECT name FROM sys.tables WHERE name IN ({placeholders}) ORDER BY name'

with pyodbc.connect(CONNECTION, timeout=5) as conn:
    rows = conn.cursor().execute(query, EXPECTED_TABLES).fetchall()

print([row[0] for row in rows])
