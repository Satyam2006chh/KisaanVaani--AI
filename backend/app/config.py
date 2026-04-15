from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = ""
    sarvam_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    app_env: str = "development"
    secret_key: str = "changeme"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
