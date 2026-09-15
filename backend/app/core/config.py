from pathlib import Path
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore"
    )
    DATABASE_URL: str = "sqlite:///./previum.db"
    POSTGRES_DB: str = "previum"
    POSTGRES_USER: str = "previum_user"
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    JWT_SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1500, ge=1)

    @model_validator(mode="after")
    def postgres_url(self):
        if "DATABASE_URL" not in self.model_fields_set and self.POSTGRES_PASSWORD:
            from sqlalchemy import URL
            self.DATABASE_URL = URL.create(
                "postgresql+psycopg", username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD.get_secret_value(),
                host=self.POSTGRES_HOST, port=self.POSTGRES_PORT,
                database=self.POSTGRES_DB,
            ).render_as_string(hide_password=False)
        return self

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode()) < 32:
            raise ValueError("JWT_SECRET_KEY deve ter pelo menos 32 bytes aleatórios")
        return value


settings = Settings()
