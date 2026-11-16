import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    atlassian_account_id: str | None = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )


class UserCreate(SQLModel):
    email: str


class UserRead(SQLModel):
    id: uuid.UUID
    email: str
    atlassian_account_id: str | None
    created_at: datetime


class JiraConnection(SQLModel, table=True):
    __tablename__ = "jira_connections"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    cloud_id: str
    site_url: str
    access_token_enc: str
    refresh_token_enc: str | None = None
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))
    scope: str = ""
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
