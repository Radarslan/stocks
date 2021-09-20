import json
import logging
import sys

from decouple import config

# general
ENVIRONMENT: str = config("ENVIRONMENT", "localhost")

API_VERSION: str = config("API_VERSION", "/api")
PROJECT_NAME: str = config("PROJECT_NAME", "Stocks")

BACKEND_CORS_ORIGINS: str = config("BACKEND_CORS_ORIGINS", "*")
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# logging
MILLISECONDS_LENGTH = 3
MODULE_NAME_LENGTH = 20
LINE_NUMBER_LENGTH = 5
LOGGING_LEVEL_NAME_LENGTH = 8
LOG_FORMAT = (
    f"[%(asctime)s"
    f".%(msecs){MILLISECONDS_LENGTH}d] "
    f"[%(module){MODULE_NAME_LENGTH}s] "
    f"[%(lineno){LINE_NUMBER_LENGTH}d] "
    f"[%(levelname){LOGGING_LEVEL_NAME_LENGTH}s]: "
    f"%(message)s"
)

logging.basicConfig(
    datefmt=DATETIME_FORMAT,
    format=LOG_FORMAT,
    level=logging.DEBUG,
    stream=sys.stdout,
    force=True,
)

# time periods
HALF_AN_HOUR = 1800

# database
DATABASE_PASSWORD: str = config("DATABASE_PASSWORD", "gibberish")
DATABASE_HOST: str = config(
    "DATABASE_HOST", "database" if ENVIRONMENT == "docker" else "127.0.0.1"
)
DATABASE_PORT: int = config("DATABASE_PORT", 5005, cast=int)
DATABASE_NAME: int = config("DATABASE_NAME", 0, cast=int)
TIME_TO_LIVE_IN_SECONDS: int = config(
    "TIME_TO_LIVE_IN_SECONDS", HALF_AN_HOUR, cast=int
)

# sockets
BINANCE_WEB_SOCKET_URL: str = config(
    "BINANCE_WEB_SOCKET_URL",
    "wss://stream.binance.com:9443/stream?streams=!miniTicker@arr",
)
SOCKET_MESSAGE_LENGTH: int = config("SOCKET_MESSAGE_LENGTH", 4096, cast=int)
SOCKET_DISCONNECT_MESSAGE: str = config(
    "SOCKET_DISCONNECT_MESSAGE", "DISCONNECTED!"
)
ENCODING_FORMAT: str = "utf-8"
LOCAL_APP_CFG = """
    {
        "SOCKET_CONNECTIONS": [
            {
                "url_slug": "dxfeed",
                "source_type": "dxfeed",
                "HOST": "127.0.0.1",
                "PORT": 1234
            },
            {
                "url_slug": "dxfeed",
                "source_type": "mc_fix",
                "HOST": "127.0.0.1",
                "PORT": 4321
            }
        ]
    }
    """
LOCAL_APP_CFG = """
    {
        "SOCKET_CONNECTIONS": [
            {
                "url_slug": "dxfeed",
                "source_type": "dxfeed",
                "HOST": "127.0.0.1",
                "PORT": 1234
            },
            {
                "url_slug": "dxfeed",
                "source_type": "mc_fix",
                "HOST": "127.0.0.1",
                "PORT": 4321
            }
        ]
    }
    """
APP_CFG = config("APP_CFG", LOCAL_APP_CFG)
try:
    if ENVIRONMENT == "localhost":
        SOCKET_CONNECTIONS = json.loads(LOCAL_APP_CFG).get(
            "SOCKET_CONNECTIONS"
        )
    else:
        SOCKET_CONNECTIONS = json.loads(APP_CFG).get("SOCKET_CONNECTIONS")
    SOCKET_SOURCE_TYPES = {
        f"{connection.get('PORT')}": connection.get("source_type")
        for connection in SOCKET_CONNECTIONS
    }
except Exception as e:
    logging.error("failed to get socket connections configuration")
    logging.error(e)
    sys.exit(1)

# data validation

ASSET_DECIMAL_PLACES = 10
