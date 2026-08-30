from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.workspaces.members_router import router as workspace_members_router
from app.workspaces.router import router as workspaces_router

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
app.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(workspace_members_router, prefix="/workspaces", tags=["workspace-members"])


@app.get("/health")
def health():
    return {"status": "ok"}
