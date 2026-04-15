from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = ""
    sarvam_api_key: str = ""
    mongodb_uri: str = ""
    app_env: str = "production"
    secret_key: str = "changeme"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
