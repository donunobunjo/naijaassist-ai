from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NaijaMobile AI"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql://postgres:password@localhost:5432/naijamobile"
    price_freshness_days: int = 7
    # inventory_freshness_hours: int = 24
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    meta_app_secret: str = ""
    meta_graph_api_version: str = ""
    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    max_context_messages: int = 12

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
