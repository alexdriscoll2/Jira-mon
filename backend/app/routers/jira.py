from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app import jira
from app.database import get_session
from app.jira_tokens import get_access_token, get_connection
from app.models import User
from app.security import get_current_user

router = APIRouter(prefix="/jira", tags=["jira"])


@router.get("/whoami")
def whoami(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    conn = get_connection(session, user)
    if not conn:
        raise HTTPException(status_code=404, detail="Jira is not connected")
    token = get_access_token(session, conn)
    me = jira.get(f"/ex/jira/{conn.cloud_id}/rest/api/3/myself", token)
    return {"displayName": me.get("displayName"), "site": conn.site_url}
