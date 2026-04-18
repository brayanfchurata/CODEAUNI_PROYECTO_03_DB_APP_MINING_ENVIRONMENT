from typing import Optional

import pandas as pd
import pyodbc

from config.settings import DbConfig


class DatabaseManager:
    def __init__(self, config: Optional[DbConfig] = None):
        self.config = config or DbConfig()
        self.connection: Optional[pyodbc.Connection] = None

    def connect(self) -> pyodbc.Connection:
        if self.connection is None:
            self.connection = pyodbc.connect(
                self.config.connection_string(),
                timeout=5
            )
        return self.connection

    def disconnect(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> bool:
        conn = pyodbc.connect(self.config.connection_string(), timeout=5)
        conn.close()
        return True

    def query_df(self, sql: str, params: Optional[list] = None) -> pd.DataFrame:
        if self.connection is None:
            self.connect()
        return pd.read_sql(sql, self.connection, params=params or [])

    def execute(self, sql: str, params: Optional[list] = None) -> None:
        if self.connection is None:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(sql, params or [])
        self.connection.commit()
        cursor.close()

    def execute_many(self, sql: str, rows: list[tuple]) -> None:
        if self.connection is None:
            self.connect()

        cursor = self.connection.cursor()
        cursor.fast_executemany = True
        cursor.executemany(sql, rows)
        self.connection.commit()
        cursor.close()