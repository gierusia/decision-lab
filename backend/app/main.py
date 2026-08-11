from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры модулей подключаются сюда по мере готовности этапов, например:
# from app.auth.router import router as auth_router
# app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
def health() -> dict[str, str]:
    """Простая проверка живости — именно её дёргает фронт на Этапе 0,
    чтобы убедиться, что связка frontend -> backend работает."""
    return {"status": "ok", "service": settings.PROJECT_NAME}
