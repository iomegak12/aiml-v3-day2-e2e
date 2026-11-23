"""API settings loaded from environment variables and an optional .env file."""

from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["critical", "error", "warning", "info", "debug", "trace"]


class ConfigurationError(RuntimeError):
    """Raised at startup when a setting is invalid (fail fast, clear message)."""


class Settings(BaseSettings):
    """All runtime settings; names map to upper-case environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",            # unrelated variables in .env are allowed
        protected_namespaces=(),   # allow field names starting with "model_"
    )

    app_name: str = Field("NetCore TAC ETA API", min_length=1)
    app_env: Literal["development", "production"] = "development"
    host: str = Field("0.0.0.0", min_length=1)
    port: int = Field(8000, ge=1, le=65535)
    log_level: LogLevel = "info"
    model_path: Path = Path("models/eta_model.joblib")
    model_metadata_path: Path = Path("models/eta_model.json")
    rate_limit_requests: int = Field(100, ge=1)
    rate_limit_window_seconds: int = Field(60, ge=1)
    rate_limit_block_seconds: int = Field(30, ge=1)
    trust_proxy_headers: bool = False
    docs_enabled: bool = True

    @field_validator("log_level", "app_env", mode="before")
    @classmethod
    def _lower_case(cls, value: Any) -> Any:
        """Accept "INFO" / "Production" as well as lower case."""
        return value.strip().lower() if isinstance(value, str) else value


def format_validation_error(error: ValidationError) -> str:
    """One line per bad setting: ``NAME: reason (got 'value')``."""
    lines = []
    for item in error.errors():
        name = "_".join(str(part) for part in item["loc"]).upper() or "SETTINGS"
        lines.append(f"  {name}: {item['msg']} (got {item.get('input')!r})")
    return "Invalid configuration (check .env / environment variables):\n" + "\n".join(lines)


def load_settings(**overrides: Any) -> Settings:
    """Build Settings, turning validation errors into a readable ConfigurationError.

    Args:
        **overrides: Field values or ``_env_file`` that take precedence over the environment.

    Raises:
        ConfigurationError: If any value is invalid.
    """
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        raise ConfigurationError(format_validation_error(exc)) from None
