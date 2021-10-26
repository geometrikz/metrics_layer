try:
    import snowflake.connector
except ModuleNotFoundError:
    pass

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
except ModuleNotFoundError:
    pass

from metrics_layer.core.parse.connections import (
    BaseConnection,
    ConnectionType,
    MetricsLayerConnectionError,
)


class QueryRunner:
    def __init__(self, query: str, connection: BaseConnection):
        self.query = query
        self.connection = connection
        self._query_runner_lookup = {
            ConnectionType.snowflake: self._run_snowflake_query,
            ConnectionType.bigquery: self._run_bigquery_query,
        }
        if self.connection.type not in self._query_runner_lookup:
            supported = list(self._query_runner_lookup.keys())
            raise MetricsLayerConnectionError(
                f"Connection type {self.connection.type} not supported, supported types are {supported}"
            )

    # 3 min timeout default set in seconds (aborts query after timeout)
    def run_query(self, timeout: int = 180, **kwargs):
        query_runner = self._query_runner_lookup[self.connection.type]
        df = query_runner(timeout=timeout)
        return df

    def _run_snowflake_query(self, timeout: int):
        snowflake_connection = self._get_snowflake_connection(self.connection)
        self._run_snowflake_pre_queries(snowflake_connection)

        cursor = snowflake_connection.cursor()
        cursor.execute(self.query, timeout=timeout)

        df = cursor.fetch_pandas_all()
        snowflake_connection.close()
        return df

    def _run_bigquery_query(self, timeout: int):
        bigquery_connection = self._get_bigquery_connection(self.connection)
        df = bigquery_connection.query(self.query, timeout=timeout, job_retry=None).to_dataframe()
        bigquery_connection.close()
        return df

    def _run_snowflake_pre_queries(self, snowflake_connection):
        to_execute = ""
        if self.connection.warehouse:
            to_execute += f"USE WAREHOUSE {self.connection.warehouse};"
        if self.connection.database:
            to_execute += f'USE DATABASE "{self.connection.database.upper()}";'
        if self.connection.schema:
            to_execute += f'USE SCHEMA "{self.connection.schema.upper()}";'

        if to_execute != "":
            snowflake_connection.execute_string(to_execute)

    @staticmethod
    def _get_snowflake_connection(connection: BaseConnection):
        try:
            return snowflake.connector.connect(
                account=connection.account,
                user=connection.username,
                password=connection.password,
                role=connection.role,
            )
        except (ModuleNotFoundError, NameError):
            raise ModuleNotFoundError(
                "MetricsLayer could not find the Snowflake modules it needs to run the query. "
                "Make sure that you have those modules installed or reinstall MetricsLayer with "
                "the [snowflake] option e.g. pip install metrics-layer[snowflake]"
            )

    @staticmethod
    def _get_bigquery_connection(connection: BaseConnection):
        try:
            service_account_creds = service_account.Credentials.from_service_account_info(
                connection.credentials
            )
            connection = bigquery.Client(project=connection.project_id, credentials=service_account_creds)
        except (ModuleNotFoundError, NameError):
            raise ModuleNotFoundError(
                "MetricsLayer could not find the BigQuery modules it needs to run the query. "
                "Make sure that you have those modules installed or reinstall MetricsLayer with "
                "the [bigquery] option e.g. pip install metrics-layer[bigquery]"
            )
        return connection