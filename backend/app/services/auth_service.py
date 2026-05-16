from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, ResetPasswordRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: RegisterRequest) -> str:
        existing = self.db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            phone_number=payload.phone_number,
            is_admin=False,
        )
        self.db.add(user)
        self.db.commit()
        return create_access_token(subject=user.email)

    def login(self, payload: LoginRequest) -> str:
        user = self.db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        return create_access_token(subject=user.email)

    def reset_password(self, payload: ResetPasswordRequest) -> None:
        user = self.db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if len(payload.new_password.strip()) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters.",
            )
        user.hashed_password = get_password_hash(payload.new_password.strip())
        self.db.add(user)
        self.db.commit()
