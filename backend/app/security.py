import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.models import User

ALGORITHM = "HS256"
bearer = HTTPBearer()


def create_session_token(user_id: uuid.UUID) -> str:
    if not settings.session_secret:
        raise RuntimeError("SESSION_SECRET is not set")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.session_expire_minutes),
    }
    return jwt.encode(payload, settings.session_secret, algorithm=ALGORITHM)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    session: Session = Depends(get_session),
) -> User:
    invalid = HTTPException(
        status_code=401,
        detail="Invalid or expired session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            creds.credentials, settings.session_secret, algorithms=[ALGORITHM]
        )
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise invalid

    user = session.get(User, user_id)
    if not user:
        raise invalid
    return user
