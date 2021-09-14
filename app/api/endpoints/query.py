from typing import Any

from aioredis import Redis
from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies import get_redis
from app.core.business_logic_layer.assets import get_table_rows
from app.core.business_logic_layer.assets import get_timeserie_datapoints
from app.schemas.grafana.queries import CreateQuery

router = APIRouter()


@router.post("", tags=["query"])
async def query(
    *,
    redis: Redis = Depends(get_redis),
    query: CreateQuery,
) -> Any:
    if query and query.targets and query.targets[0].target:
        if query.targets[0].type == "table":
            return await get_table_rows(redis, query.targets[0].target)
        elif query.targets[0].type == "timeserie":
            return [
                await get_timeserie_datapoints(redis, target_query.target)
                for target_query in query.targets
            ]
