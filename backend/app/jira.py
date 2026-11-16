import httpx
from fastapi import HTTPException

from app.config import settings

TOKEN_URL = "https://auth.atlassian.com/oauth/token"
API_BASE = "https://api.atlassian.com"


def redirect_uri() -> str:
    # Must match the URL the extension sent to Atlassian, character for character.
    return f"https://{settings.extension_id}.chromiumapp.org/"


def exchange_code(code: str) -> dict:
    resp = httpx.post(
        TOKEN_URL,
        json={
            "grant_type": "authorization_code",
            "client_id": settings.jira_client_id,
            "client_secret": settings.jira_client_secret,
            "code": code,
            "redirect_uri": redirect_uri(),
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print("Atlassian token error:", resp.status_code, resp.text)  # dev only
        raise HTTPException(status_code=400, detail="Atlassian rejected the login code")
    return resp.json()


def get(path: str, access_token: str):
    resp = httpx.get(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        print("Atlassian API error:", path, resp.status_code, resp.text)  # dev only
        raise HTTPException(status_code=502, detail="Could not reach Jira")
    return resp.json()

def refresh_access_token(refresh_token: str) -> dict:
    resp = httpx.post(
        TOKEN_URL,
        json={
            "grant_type": "refresh_token",
            "client_id": settings.jira_client_id,
            "client_secret": settings.jira_client_secret,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print("Atlassian refresh error:", resp.status_code, resp.text)  # dev only
        raise HTTPException(
            status_code=409, detail="Jira connection expired, please reconnect"
        )
    return resp.json()
