import json
import logging
from decimal import Decimal
from time import time
from typing import List

from app.crud.base import save_data_to_redis_list
from app.db.redis import redis
from app.schemas.symbols import SYMBOL_QUOTE
from app.schemas.symbols import Asset
from app.schemas.symbols import DXFeedAsset
from app.schemas.symbols import MCFixAsset


def get_binance_messages(binance_data: SYMBOL_QUOTE) -> SYMBOL_QUOTE:
    messages = {"dxfeed": "", "mc_fix": ""}

    alternate_market_names = ["BINANCE", "COMP"]
    increment = 0
    for symbol in binance_data:
        name = symbol.get("s")
        last_price = symbol.get("c")
        event_time = symbol.get("E")
        messages["mc_fix"] += (
                json.dumps(
                    {
                        "s": name,
                        "p": {
                            "r": float(last_price),
                            "t": str(event_time / 1000),
                        },
                    }
                )
                + "\n"
        )
        messages["dxfeed"] += (
            f"{event_time},"
            f"{name},"
            f"{alternate_market_names[increment % 2]},"
            f"{last_price},"
            f"0,0,"
            f"{time()}"
            f"\n"
        )
        increment += 1

    return messages


async def save_messages_to_redis(
        messages_list: List[str], source_type: str
) -> None:
    for message in messages_list:
        data = {
            "market": "",
            "symbol": "",
            "rate": Decimal(0.0),
            "timestamp": 0
        }
        if source_type == "mc_fix" and len(message) > 0:
            try:
                # {"s": "GBPUSD", "p": {"r": 1.34023, "t": "1606811740.13800"}}
                message = json.loads(message)
                p = message.get("p", {})
                data = {
                    "symbol": message.get("s", ""),
                    "rate": str(p.get("r", 0)),
                    "timestamp": str(Decimal(p.get("t", 0)) * 1000)
                }
            except Exception as e:
                logging.error(e)

        elif source_type == "dxfeed":
            # 1630856330469, UNIUSDT, BINANCE, 28.95000000, 0, 0,
            message_values = message.split(",")
            if len(message_values) == 7:
                data = {
                    "market": message_values[2],
                    "symbol": message_values[1],
                    "rate": str(message_values[3]),
                    "timestamp": str(message_values[0])
                }
        symbol = data.get("symbol", "")
        if symbol != "":
            await save_data_to_redis_list(
                redis, source_type, symbol, data
            )
