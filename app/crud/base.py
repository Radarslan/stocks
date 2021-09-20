from time import time
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
    name = f"{source_type}:{key}:{time()}"
    await redis.hset(name, mapping=data)
    await redis.expire(name, TIME_TO_LIVE_IN_SECONDS)


async def read_data_from_redis_list(
        redis: Redis, name: str
) -> Optional[List[Any]]:
    result = []
    async for key_name in redis.scan_iter(f"{name}*", 100):
        asset_quote = await redis.hgetall(key_name)
        result.append(
            {
                key.decode(ENCODING_FORMAT): value.decode(ENCODING_FORMAT)
                for key, value in asset_quote.items()
            }
        )
    return result
