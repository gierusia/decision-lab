from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.core.session import clear_session_cookie, set_session_cookie
from app.auth.presenters import to_user_out

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if service.get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        return to_user_out(service.create_user(db, payload.email, payload.password, payload.full_name))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(subject=str(user.id))
    set_session_cookie(response, token)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return to_user_out(current_user)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return to_user_out(
            service.update_profile(
                db,
                current_user,
                full_name=payload.full_name,
                current_password=payload.current_password,
                new_password=payload.new_password,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
