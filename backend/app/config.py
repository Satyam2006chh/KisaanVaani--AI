from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    groq_api_key: str = ""

    # Sarvam AI (Voice)
    sarvam_api_key: str = ""

    # Firecrawl
    firecrawl_api_key: str = ""

    # Weather
    openweather_api_key: str = ""

    # MongoDB
    mongodb_uri: str = ""

    # Mandi
    data_gov_api_key: str = ""

    # App
    app_env: str = "development"
    secret_key: str = "changeme"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
