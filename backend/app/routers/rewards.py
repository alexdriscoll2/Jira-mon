from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app import rewards
from app.database import get_session
from app.models import RewardRead, User
from app.security import get_current_user
from app import pokemon
from app.models import CollectionItem, PokemonRead

import uuid


router = APIRouter(prefix="/rewards", tags=["rewards"])


class SyncResult(BaseModel):
    new_count: int
    unopened: list[RewardRead]


@router.post("/sync", response_model=SyncResult)
def sync(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    new_count = rewards.sync_rewards(session, user)
    return {"new_count": new_count, "unopened": rewards.unopened_boxes(session, user)}


class OpenResult(BaseModel):
    reward: RewardRead
    pokemon: PokemonRead


@router.post("/{reward_id}/open", response_model=OpenResult)
def open_box(
    reward_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    reward = rewards.open_box(session, user, reward_id)
    return {"reward": reward, "pokemon": pokemon.describe(reward.pokemon_id)}


@router.get("/collection", response_model=list[CollectionItem])
def get_collection(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return [
        {
            "reward_id": r.id,
            "issue_key": r.issue_key,
            "summary": r.summary,
            "opened_at": r.opened_at,
            "pokemon": pokemon.describe(r.pokemon_id),
        }
        for r in rewards.collection(session, user)
    ]
