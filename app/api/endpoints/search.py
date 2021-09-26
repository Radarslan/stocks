from fastapi import APIRouter
from starlette.requests import Request

from app.crud.in_memory_base import get_all_keys
from app.crud.in_memory_base import get_all_sources
from app.schemas.grafana.queries import Targets

router = APIRouter()


@router.post("", response_model=Targets, tags=["search"])
async def search(*, request: Request) -> Targets:
    all_keys = get_all_keys()
    all_sources = get_all_sources(all_keys)
    return all_sources + all_keys
