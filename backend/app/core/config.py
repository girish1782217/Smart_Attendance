from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_JWT_SECRET = "insecure-dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smart Attendance Management System"
    environment: str = "development"

    database_url: str = "sqlite:///./dev.db"

    jwt_secret: str = INSECURE_DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_timeout_seconds: float = 10.0

    cors_origins: str = "http://localhost:5173"

    low_attendance_default_threshold: float = 75.0

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_production_settings(settings: Settings) -> None:
    """Fails fast at startup rather than silently running an insecure
    deployment. Called from create_app() — see docs/sdd/16-security-spec.md."""
    if settings.is_production and settings.jwt_secret == INSECURE_DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET must be set to a secure, non-default value when ENVIRONMENT=production."
        )
