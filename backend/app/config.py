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
    # Чат/группа, куда бот доставляет обращения из мини-аппа (id, напр. -1001234567890)
    support_chat_id: str = ""
    # Telegram id админов через запятую — им доступен раздел «Заявки» в мини-аппе
    admin_ids: str = ""

    # Хранилище обращений (SQLite). В Docker монтируется в volume: DB_PATH=/data/support.db
    db_path: str = "support.db"

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
    trial_days: int = 7
    trial_traffic_gb: int = 100
    trial_device_limit: int = 3
    renew_days: int = 30
    # Срок ручного продления оператором (forward→кнопка в боте), месяцев
    renew_months: int = 6

    # Напоминание об окончании подписки: за сколько дней предупреждать и как
    # часто бот проверяет панель (фоновый цикл рядом с polling).
    notify_before_days: int = 3
    notify_check_interval_hours: int = 6

    # Misc
    cors_origins: str = "http://localhost:5173,http://localhost:5180"
    dev_telegram_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_id_list(self) -> list[int]:
        ids: list[int] = []
        for part in self.admin_ids.split(","):
            part = part.strip()
            if part:
                try:
                    ids.append(int(part))
                except ValueError:
                    continue
        return ids

    @property
    def api_base(self) -> str:
        return self.remnawave_base_url.rstrip("/") + "/api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
