from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlmodel import Session

from app.database import get_session
from app.config import settings


app = FastAPI(title="Jiramon API")

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