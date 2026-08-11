from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Общие
    PROJECT_NAME: str = "Decision Lab"
    ENV: str = "local"

    # База данных
    DATABASE_URL: str = "postgresql://decision_lab:decision_lab@postgres:5432/decision_lab"

    # Auth (понадобится на Этапе 1, заводим сразу чтобы не трогать core потом)
    JWT_SECRET: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS — список origin'ов через запятую в .env, например:
    # CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
