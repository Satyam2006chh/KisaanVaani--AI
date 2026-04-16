from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = ""
    sarvam_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    app_env: str = "development"
    secret_key: str = "changeme"
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env without erroring

settings = Settings()
