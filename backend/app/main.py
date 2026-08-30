from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Decision Lab")

# CORS для фронта (на Этапе 6 настроим правильно, сейчас позволяем всем)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
def health():
    return {"status": "ok"}
