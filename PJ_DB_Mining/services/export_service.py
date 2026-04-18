from pathlib import Path

import pandas as pd


class ExportService:
    @staticmethod
    def export_to_csv(df: pd.DataFrame, file_path: str) -> None:
        if df.empty:
            raise ValueError("El DataFrame está vacío.")
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

    @staticmethod
    def export_to_excel(dataframes: dict[str, pd.DataFrame], file_path: str) -> None:
        if not dataframes:
            raise ValueError("No hay dataframes para exportar.")

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            for sheet_name, df in dataframes.items():
                if df is not None and not df.empty:
                    safe_sheet_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

    @staticmethod
    def ensure_parent_dir(file_path: str) -> None:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)