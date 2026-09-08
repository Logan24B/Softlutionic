from mssql.base import Database, DatabaseWrapper as MssqlDatabaseWrapper


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

    def get_new_connection(self, conn_params):
        original_connect = Database.connect

        def connect_without_unicode_results(connstr, *args, **kwargs):
            kwargs.pop('unicode_results', None)
            return original_connect(connstr, *args, **kwargs)

        Database.connect = connect_without_unicode_results
        try:
            return super().get_new_connection(conn_params)
        finally:
            Database.connect = original_connect