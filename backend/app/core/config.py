from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
