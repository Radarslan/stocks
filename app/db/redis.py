from aioredis import Redis

from app.core.settings.settings import DATABASE_HOST
from app.core.settings.settings import DATABASE_NAME
from app.core.settings.settings import DATABASE_PASSWORD
from app.core.settings.settings import DATABASE_PORT

redis = Redis(
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    password=DATABASE_PASSWORD,
    db=DATABASE_NAME,
)
