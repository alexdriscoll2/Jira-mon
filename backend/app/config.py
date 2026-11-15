from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    extension_id: str = ""
    database_url: str = "sqlite:///./dev.db"
    jira_client_id: str = ""
    jira_client_secret: str = ""

settings = Settings()