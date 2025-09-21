from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    ENV: str = "production"
    CORS_ORIGINS_RAW: str = "*"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CURRENCY: str = "usd"
    SUCCESS_URL: str = "https://prello.app/success"
    CANCEL_URL: str = "https://prello.app/cancel"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def CORS_ORIGINS(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS_RAW.split(",") if o.strip()]

settings = Settings()
