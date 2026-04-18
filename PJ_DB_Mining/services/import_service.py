from pathlib import Path
from typing import Optional

import pandas as pd

from database.connection import DatabaseManager


TABLE_COLUMN_MAP = {
    "dbo.dim_procesos": ["id_proceso", "proceso", "tipo_proceso"],
    "dbo.preparacion_minerales": [
        "id",
        "fecha",
        "id_proceso",
        "id_encargado",
        "toneladas_procesadas",
        "porcentaje_recuperacion",
        "tiempo_operacion_horas",
        "consumo_energia_kwh",
        "costo_tonelada_usd",
    ],
    "dbo.extraccion_metales": [
        "id",
        "fecha",
        "id_proceso",
        "id_encargado",
        "toneladas_procesadas",
        "porcentaje_extraccion",
        "temperatura_procesos_celcius",
        "consumo_reactivos_kg",
        "costo_operacion_usd",
    ],
    "dbo.refinacion_metales": [
        "fecha",
        "id_proceso",
        "toneladas_procesadas",
        "pureza_inicial_pct",
        "pureza_final_pct",
        "tiempo_refinacion_hrs",
        "consumo_electrico_kwh",
        "costo_total_usd",
    ],
}


class ImportService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def read_csv_preview(self, file_path: str, rows: int = 200) -> pd.DataFrame:
        path = Path(file_path)

        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            df = pd.read_csv(path, encoding="latin1")

        return df.head(rows)

    def import_csv_to_table(self, file_path: str, table_name: str) -> int:
        if table_name not in TABLE_COLUMN_MAP:
            raise ValueError(f"Tabla no soportada: {table_name}")

        path = Path(file_path)

        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            df = pd.read_csv(path, encoding="latin1")

        df.columns = [str(c).strip() for c in df.columns]
        expected_columns = TABLE_COLUMN_MAP[table_name]

        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            raise ValueError(
                "El CSV no coincide con la tabla destino. Faltan columnas: "
                + ", ".join(missing)
            )

        df = df[expected_columns]
        df = df.where(pd.notnull(df), None)

        placeholders = ", ".join(["?" for _ in expected_columns])
        column_sql = ", ".join(expected_columns)
        insert_sql = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"

        rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
        self.db.execute_many(insert_sql, rows)

        return len(rows)

    def get_supported_tables(self) -> list[str]:
        return list(TABLE_COLUMN_MAP.keys())