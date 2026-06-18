from mssql.base import DatabaseWrapper as MssqlDatabaseWrapper


class DatabaseWrapper(MssqlDatabaseWrapper):
    sql_server_version = MssqlDatabaseWrapper.sql_server_version
    to_azure_sql_db = MssqlDatabaseWrapper.to_azure_sql_db

    def _build_connection_string(self, conn_params, driver):
        connstr = super()._build_connection_string(conn_params, driver)
        connstr = connstr.replace(f'DRIVER={driver}', f'DRIVER={{{driver}}}')
        connstr = connstr.replace(';MARS_Connection=yes', '')
        return connstr.replace(
            ';Trusted_Connection=yes;DATABASE=',
            ';DATABASE=',
        ).replace(
            ';TrustServerCertificate=yes',
            ';Trusted_Connection=yes;TrustServerCertificate=yes',
        )
