import enum
import secrets
import typing

from pydantic_settings import BaseSettings


@enum.unique
class Environment(enum.Enum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class Settings(BaseSettings):
    SITE_NAME: str = "BeanGrid"
    PROJECT_NAME: str = "beangrid"

    ENV: Environment = Environment.DEVELOPMENT
    MAINTENANCE_MODE: bool = False

    SESSION_SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_MAX_AGE: int = 14 * 24 * 60 * 60  # 14 days, in seconds

    # LLM Configuration
    LLM_MODEL: str = "xai/grok-3"
    LLM_API_BASE: str = "https://api.x.ai/v1"
    LLM_API_KEY: str = ""  # Set your X.AI API key here or via environment variable


# Do not import and access this directly, use settings instead
_settings = Settings()


class SettingsProxy:
    def __init__(self, get_settings: typing.Callable[[], Settings]):
        self._get_settings = get_settings

    def __getattr__(self, item: str) -> typing.Any:
        global_settings = self._get_settings()
        return getattr(global_settings, item)


settings: Settings = SettingsProxy(lambda: _settings)
