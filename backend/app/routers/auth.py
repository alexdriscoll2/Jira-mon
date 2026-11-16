from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app import jira
from app.database import get_session
from app.models import User, UserRead
from app.security import create_session_token, get_current_user
from app.jira_tokens import save_connection

router = APIRouter(prefix="/auth", tags=["auth"])


class JiraCallback(BaseModel):
    code: str

class LoginResponse(BaseModel):
    user: UserRead
    session_token: str


@router.post("/jira/callback", response_model=LoginResponse)
def jira_callback(data: JiraCallback, session: Session = Depends(get_session)):
    tokens = jira.exchange_code(data.code)
    access_token = tokens["access_token"]

    sites = jira.get("/oauth/token/accessible-resources", access_token)
    if not sites:
        raise HTTPException(status_code=400, detail="No Jira site was authorized")
    site = sites[0]
    cloud_id = site["id"]
    site_url = site["url"]

    me = jira.get(f"/ex/jira/{cloud_id}/rest/api/3/myself", access_token)
    account_id = me["accountId"]
    email = me.get("emailAddress")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Your Atlassian profile hides your email address",
        )

    user = session.exec(
        select(User).where(User.atlassian_account_id == account_id)
    ).first()
    if not user:
        # Maybe the row exists already (e.g. made by the test endpoint): link it.
        user = session.exec(select(User).where(User.email == email)).first()
    if user:
        user.atlassian_account_id = account_id
    else:
        user = User(email=email, atlassian_account_id=account_id)

    session.add(user)
    session.commit()
    session.refresh(user)
    save_connection(session, user, tokens, cloud_id, site_url)
    return {"user": user, "session_token": create_session_token(user.id)}

@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user