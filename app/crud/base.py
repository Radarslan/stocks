import pickle
from typing import Any
from typing import List
from typing import Optional

from aioredis import Redis

from app.core.settings.settings import ENCODING_FORMAT
from app.core.settings.settings import TIME_TO_LIVE_IN_SECONDS
from app.schemas.grafana.queries import Targets


async def get_all_keys(redis: Redis) -> Targets:
    return sorted(
        list(
            set(
                [
                    key.decode(ENCODING_FORMAT)
                    async for key in redis.scan_iter(r"*:*", 100)
                ]
            )
        )
    )


def get_all_sources(all_keys: List[str]) -> Targets:
    return sorted(list(set([key.split(":")[0] for key in all_keys])))


async def save_data_to_redis_list(
    redis: Redis, source_type: str, key: str, data: Any
) -> None:
    name = f"{source_type}:{key}"
    await redis.rpush(name, pickle.dumps(data, protocol=5))
    await redis.expire(name, TIME_TO_LIVE_IN_SECONDS)


async def read_data_from_redis_list(
    redis: Redis, key: str
) -> Optional[List[Any]]:
    asset_quotes = await redis.lrange(key, 0, -1)
    if asset_quotes:
        return [pickle.loads(asset_quote) for asset_quote in asset_quotes]
    return None
