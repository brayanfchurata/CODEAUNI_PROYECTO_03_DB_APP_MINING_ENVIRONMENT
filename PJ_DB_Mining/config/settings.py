from dataclasses import dataclass
from pathlib import Path
import json


SETTINGS_FILE = Path("app_settings.json")


@dataclass
class DbConfig:
    server: str = r"localhost\SQL_BRAYAN"
    database: str = "SQL_PROJECT_B"
    driver: str = "ODBC Driver 17 for SQL Server"
    trusted_connection: bool = True
    username: str = ""
    password: str = ""

    def connection_string(self) -> str:
        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]

        if self.trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.username}")
            parts.append(f"PWD={self.password}")

        return ";".join(parts) + ";"


class SettingsManager:
    @staticmethod
    def load() -> DbConfig:
        if not SETTINGS_FILE.exists():
            return DbConfig()

        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return DbConfig(**data)
        except Exception:
            return DbConfig()

    @staticmethod
    def save(config: DbConfig) -> None:
        SETTINGS_FILE.write_text(
            json.dumps(config.__dict__, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )