import pyodbc


CONNECTION = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost,1433;'
    'DATABASE=master;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
    'Encrypt=no'
)


with pyodbc.connect(CONNECTION, timeout=5, autocommit=True) as conn:
    conn.cursor().execute(
        "IF DB_ID('BDsofactur') IS NULL CREATE DATABASE BDsofactur"
    )

print('BDsofactur lista')
