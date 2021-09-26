from aioredis import Redis
from fastapi import APIRouter
from fastapi import Depends

from app.core.utils.redis_dependency import get_redis
from app.schemas.health_check import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck, tags=["health check"])
async def health_check(*, redis: Redis = Depends(get_redis)) -> HealthCheck:
    message = await redis.get("health_check")
    return HealthCheck(message=message)
