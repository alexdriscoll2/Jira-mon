import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel, UniqueConstraint


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

class TicketReward(SQLModel, table=True):
    __tablename__ = "ticket_rewards"
    __table_args__ = (
        UniqueConstraint("user_id", "jira_issue_id", name="uq_reward_user_issue"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    jira_issue_id: str
    issue_key: str
    summary: str = ""
    completed_at: datetime = Field(sa_type=DateTime(timezone=True))
    opened_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    pokemon_id: int | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )


class RewardRead(SQLModel):
    id: uuid.UUID
    issue_key: str
    summary: str
    completed_at: datetime
    opened_at: datetime | None
    pokemon_id: int | None

class PokemonRead(SQLModel):
    id: int
    name: str | None
    sprite_url: str


class CollectionItem(SQLModel):
    reward_id: uuid.UUID
    issue_key: str
    summary: str
    opened_at: datetime
    pokemon: PokemonRead
