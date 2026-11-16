from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlmodel import Session, select

from app import jira
from app.cryptography import decrypt, encrypt
from app.models import JiraConnection, User


def _apply_tokens(conn: JiraConnection, tokens: dict) -> None:
    now = datetime.now(timezone.utc)
    conn.access_token_enc = encrypt(tokens["access_token"])
    if tokens.get("refresh_token"):
        conn.refresh_token_enc = encrypt(tokens["refresh_token"])
    conn.expires_at = now + timedelta(seconds=tokens.get("expires_in", 3600))
    conn.scope = tokens.get("scope", conn.scope)
    conn.updated_at = now


def get_connection(session: Session, user: User) -> JiraConnection | None:
    return session.exec(
        select(JiraConnection).where(JiraConnection.user_id == user.id)
    ).first()


def save_connection(
    session: Session, user: User, tokens: dict, cloud_id: str, site_url: str
) -> JiraConnection:
    conn = get_connection(session, user)
    if not conn:
        conn = JiraConnection(
            user_id=user.id,
            cloud_id=cloud_id,
            site_url=site_url,
            access_token_enc="",
            expires_at=datetime.now(timezone.utc),
        )
    conn.cloud_id = cloud_id
    conn.site_url = site_url
    _apply_tokens(conn, tokens)
    session.add(conn)
    session.commit()
    return conn


def get_access_token(session: Session, conn: JiraConnection) -> str:
    if conn.expires_at - timedelta(seconds=60) > datetime.now(timezone.utc):
        return decrypt(conn.access_token_enc)

    if not conn.refresh_token_enc:
        raise HTTPException(
            status_code=409, detail="Jira connection expired, please reconnect"
        )

    tokens = jira.refresh_access_token(decrypt(conn.refresh_token_enc))
    _apply_tokens(conn, tokens)
    session.add(conn)
    session.commit()
    return tokens["access_token"]

