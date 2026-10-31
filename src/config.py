from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = ""
    # str в Union не даёт pydantic-settings упасть на не-JSON значении вроде "1,2" — его разбирает валидатор
    ADMIN_IDS: Union[List[int], str] = Field(default_factory=list)
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/database.db"
    
    # Paths
    DATA_DIR: Path = Path("./data")
    PHOTOS_DIR: Path = Path("./data/photos")
    DOCS_DIR: Path = Path("./data/documents")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if isinstance(value, int):  # один ID: "123" декодируется как JSON-число
            return [value]
        if isinstance(value, str):
            raw_items = [item.strip() for item in value.split(",") if item.strip()]
            return [int(item) for item in raw_items]
        return value

    def create_directories(self):
        """Создание необходимых директорий"""
        for directory in [self.DATA_DIR, self.PHOTOS_DIR, self.DOCS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

settings = Settings()
