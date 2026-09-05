from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.seed_admins import seed_admins
from app.dashboard.router import router as dashboard_router
from app.decisions.router import router as decisions_router
from app.experiments.router import router as experiments_router
from app.workspaces.members_router import router as workspace_members_router
from app.workspaces.router import router as workspaces_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_admins()
    yield


app = FastAPI(title="Decision Lab", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(workspace_members_router, prefix="/workspaces", tags=["workspace-members"])
app.include_router(decisions_router, prefix="/workspaces", tags=["decisions"])
app.include_router(experiments_router, prefix="/workspaces", tags=["experiments"])
app.include_router(dashboard_router, prefix="/workspaces", tags=["dashboard"])


@app.get("/health")
def health():
    return {"status": "ok"}
