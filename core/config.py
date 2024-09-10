import json
import logging
import os
from pathlib import Path
from pprint import pformat
from typing import List, Optional, Any

from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict

DIR_PATH = Path(__file__).parent.parent

DB_PATH = os.path.join(DIR_PATH, "database", "bot.db")  # DIR_PATH / "db.sqlite3"
DB_PATH_ = os.path.join(DIR_PATH, "database")  # DIR_PATH / "db.sqlite3"

CURRENT_PATH = Path(__file__).parent


class DefaultConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


class DBSettings(DefaultConfig):
    URL_SQLITE: str = f"sqlite+aiosqlite:///{DB_PATH}"
    URL_PG: str = "postgresql+asyncpg://postgres:postgres@0.0.0.0:5432/postgres"
    URL_PG_TEST: str = (
        "postgresql+asyncpg://postgres_test:postgres_test@0.0.0.0:5433/postgres_test"
    )

    ECHO: bool = True

    POSTGRES_SYSTEM: str
    POSTGRES_DRIVER: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    PGADMIN_PORT: Optional[int] = None
    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: str
    PGADMIN_CONFIG_SERVER_MODE: bool

    @property
    def url_postgres(self) -> str:
        """Build a connection string for PostgreSQL"""
        return URL.create(
            drivername=f"{self.POSTGRES_SYSTEM}+{self.POSTGRES_DRIVER}",
            username=self.POSTGRES_USER,
            database=self.POSTGRES_DB,
            password=self.POSTGRES_PASSWORD,
            port=self.POSTGRES_PORT,
            host=self.POSTGRES_HOST,
        ).render_as_string(hide_password=False)


class RedisSettings(DefaultConfig):
    """Redis connection variables"""
    REDIS_DATABASE: str = 1
    REDIS_HOST: Optional[str] = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[Any] = None
    REDIS_USER: Optional[Any] = None
    REDIS_USER_PASSWORD: Optional[Any] = None
    REDIS_TTL_STATE: Optional[int] = None
    REDIS_TTL_DATA: Optional[int] = None


class TgBot(DefaultConfig):
    """Telegram API settings"""
    TELEGRAM_TOKEN: Optional[str] = None
    TELEGRAM_TOKEN_DEV: Optional[str] = None
    WEBHOOK_HOST: Optional[str] = None
    WEBHOOK_PATH: Optional[str] = None
    BOT_WEBAPP_HOST: Optional[str] = None
    BOT_WEBAPP_PORT: Optional[int] = None
    ADMINS: Optional[List[int]] = None
    BOSS: Optional[List[int]] = None
    BOSS_ONLY: Optional[int] = None
    OBSERVERS: Optional[List[int]] = None
    MASTER: Optional[int] = None

    @property
    def address(self) -> str:
        return f"{self.WEBHOOK_HOST}{self.WEBHOOK_PATH}"


class GoogleSheetsSettings(DefaultConfig):
    """Google API settings"""

    SERVICE_PASSWORD: Optional[str] = None
    SERVICE_ACCOUNT_FILE: Optional[str] = None

    BOOK_TABLE_ID: Optional[str] = None
    SHEET_EXITS: Optional[str] = None
    SHEET_STAFF: Optional[str] = None

    FOLDER_ID_PHOTO_SAVE: Optional[str] = None
    BOOK_WRITE_OFF_ID: Optional[str] = None
    SHEET_CODES: Optional[str] = None

    BOOK_SUPERVISOR: Optional[str] = None
    SHEET_DAY_CHECK: Optional[str] = None
    SHEET_POINT_CHECK: Optional[str] = None
    SHEET_SALES: Optional[str] = None

    BOOK_SALARY: Optional[str] = None
    SHEET_SALARY: Optional[str] = None
    SHEET_SAFE: Optional[str] = None

    BOOK_PAYMENTS: Optional[str] = None
    SHEET_PAYMENTS: Optional[str] = None

    BOOK_HOME: Optional[str] = None
    SHEET_HOME: Optional[str] = None
    HOME_SHEET_ID: Optional[int] = None
    SHEET_PROJECTS: Optional[str] = None
    PROJECTS_SHEET_ID: Optional[int] = None
    FOLDER_ID_BP: Optional[str] = None

    @property
    def credentials(self) -> str:
        return os.path.join(CURRENT_PATH, self.SERVICE_ACCOUNT_FILE)

    @property
    def load_credentials(self) -> dict:
        with open(self.credentials, "r") as read_file:
            return json.load(read_file)


class Settings(BaseSettings):
    """App base settings"""
    dev: bool = True
    # use_redis: bool = False
    # use_sqlite: bool = True
    use_redis: bool = True
    use_sqlite: bool = False
    gs: GoogleSheetsSettings = GoogleSheetsSettings()
    db: DBSettings = DBSettings()
    bot: TgBot = TgBot()
    redis: RedisSettings = RedisSettings()

    def show(self) -> None:
        """Prints the formatted model dump."""
        print(pformat(self.model_dump()))


settings = Settings()
