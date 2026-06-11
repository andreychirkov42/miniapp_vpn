from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    bot_token: str = ""
    bot_username: str = "akenaivpn_bot"
    webapp_url: str = "https://example.com"
    support_url: str = "https://t.me/akenaivpn_support"
    channel_url: str = "https://t.me/AkenaiVPN"

    # Remnawave
    remnawave_mock: bool = True
    remnawave_base_url: str = "https://panel.example.com"
    remnawave_token: str = ""
    # Альтернатива токену: вход по логину/паролю админки (панель выдаёт JWT)
    remnawave_username: str = ""
    remnawave_password: str = ""
    remnawave_squad_uuid: str = ""
    subscription_domain: str = ""
    # Фиксированная ссылка подписки для mock-режима (реальный тестовый юзер)
    mock_subscription_url: str = ""

    # Tariff defaults
    trial_days: int = 3
    trial_traffic_gb: int = 5
    renew_days: int = 30

    # Misc
    cors_origins: str = "http://localhost:5173,http://localhost:5180"
    dev_telegram_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def api_base(self) -> str:
        return self.remnawave_base_url.rstrip("/") + "/api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
