from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = ""
    sarvam_api_key: str = ""
    openweather_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    app_env: str = "development"
    secret_key: str = "changeme"

    # ─── Tools ──────────────────────────────────
    firecrawl_api_key: str = ""
    datagov_api_key: str = ""

    class Config:
        env_file = [".env", "backend/.env"]
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env without erroring

settings = Settings()
