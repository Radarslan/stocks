from aioredis import Redis
from fastapi import APIRouter
from fastapi import Depends
from starlette.requests import Request

from app.api.dependencies import get_redis
from app.crud.base import get_all_keys
from app.crud.base import get_all_sources
from app.schemas.grafana.queries import Targets

router = APIRouter()


@router.post("", response_model=Targets, tags=["search"])
async def search(
    *, request: Request, redis: Redis = Depends(get_redis)
) -> Targets:
    all_keys = await get_all_keys(redis)
    all_sources = get_all_sources(all_keys)
    return all_sources + all_keys
