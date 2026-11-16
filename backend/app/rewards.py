from datetime import datetime, timezone
import random
import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app import jira
from app.jira_tokens import get_access_token, get_connection
from app.models import TicketReward, User

# Tickets assigned to me, in a "Done" category status, resolved in the last 7 days.
JQL = (
    "assignee = currentUser() AND statusCategory = Done "
    "AND resolved >= -7d ORDER BY resolved DESC"
)


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value)


def sync_rewards(session: Session, user: User) -> int:
    conn = get_connection(session, user)
    if not conn:
        raise HTTPException(status_code=404, detail="Jira is not connected")
    token = get_access_token(session, conn)

    data = jira.post(
        f"/ex/jira/{conn.cloud_id}/rest/api/3/search/jql",
        token,
        {"jql": JQL, "fields": ["summary", "resolutiondate"], "maxResults": 50},
    )
    issues = data.get("issues", [])
    if not issues:
        return 0

    ids = [issue["id"] for issue in issues]
    already = set(
        session.exec(
            select(TicketReward.jira_issue_id).where(
                TicketReward.user_id == user.id,
                col(TicketReward.jira_issue_id).in_(ids),
            )
        ).all()
    )

    new_count = 0
    for issue in issues:
        if issue["id"] in already:
            continue
        fields = issue.get("fields", {})
        session.add(
            TicketReward(
                user_id=user.id,
                jira_issue_id=issue["id"],
                issue_key=issue["key"],
                summary=fields.get("summary") or "",
                completed_at=_parse_time(fields.get("resolutiondate")),
            )
        )
        new_count += 1

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return 0
    return new_count


def unopened_boxes(session: Session, user: User) -> list[TicketReward]:
    return list(
        session.exec(
            select(TicketReward)
            .where(
                TicketReward.user_id == user.id,
                col(TicketReward.opened_at).is_(None),
            )
            .order_by(col(TicketReward.completed_at).desc())
        ).all()
    )


MAX_POKEMON_ID = 1025

def open_box(session: Session, user: User, reward_id: uuid.UUID) -> TicketReward:
    reward = session.exec(
        select(TicketReward)
        .where(TicketReward.id == reward_id, TicketReward.user_id == user.id)
        .with_for_update()
    ).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Box not found")
    if reward.opened_at is not None:
        raise HTTPException(status_code=409, detail="Box already opened")

    reward.pokemon_id = random.randint(1, MAX_POKEMON_ID)
    reward.opened_at = datetime.now(timezone.utc)
    session.add(reward)
    session.commit()
    session.refresh(reward)
    return reward


def collection(session: Session, user: User) -> list[TicketReward]:
    return list(
        session.exec(
            select(TicketReward)
            .where(
                TicketReward.user_id == user.id,
                col(TicketReward.opened_at).is_not(None),
            )
            .order_by(col(TicketReward.opened_at).desc())
        ).all()
    )
