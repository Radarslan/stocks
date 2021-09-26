import pickle

from typing import Any
from typing import List
from typing import Optional

from aioredis import Redis

from app.core.settings.settings import ENCODING_FORMAT
from app.schemas.grafana.queries import Targets


async def get_all_keys(redis: Redis) -> Targets:
    return sorted(
        list(
            set(
                [
                    ":".join(key.decode(ENCODING_FORMAT).split(":")[:2])
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


async def read_data_from_redis_list(
    redis: Redis, key: str
) -> Optional[List[Any]]:
    asset_quotes = await redis.lrange(key, 0, -1)
    if asset_quotes:
        return [pickle.loads(asset_quote) for asset_quote in asset_quotes]
    return None
