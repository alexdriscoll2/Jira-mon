from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlmodel import Session, select

import uuid

from app.database import get_session
from app.config import settings
from app.models import User, UserCreate, UserRead
from app.routers import auth
from app.routers import jira as jira_router


app = FastAPI(title="Jiramon API")

app.include_router(auth.router)
app.include_router(jira_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"chrome-extension://{settings.extension_id}",
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check(session: Session = Depends(get_session)):
    result = session.connection().execute(text("select 1")).scalar()
    return {"db": result}

@app.post("/users", response_model=UserRead, status_code=201)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=data.email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user