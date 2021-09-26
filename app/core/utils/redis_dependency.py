import logging
from typing import AsyncGenerator

from aioredis import ConnectionError
from aioredis import RedisError

from app.db.redis import redis


async def get_redis() -> AsyncGenerator:
    try:
        await redis.set("health_check", "OK")
        yield redis
    except ConnectionError as e:
        logging.error(f"connection to redis failed: {e}")
    finally:
        try:
            await redis.close()
        except RedisError as e:
            logging.error(f"closing connection to redis failed: {e}")
