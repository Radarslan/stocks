import asyncio
import json
import logging

import websockets

from app.core.business_logic_layer.messages import get_binance_messages
from app.core.settings.settings import BINANCE_WEB_SOCKET_URL
from app.core.sockets.stocks_client import (
    get_client_sockets_for_all_in_configuration,
)
from app.core.sockets.stocks_client import send_message


async def main():
    url = BINANCE_WEB_SOCKET_URL
    client_sockets = get_client_sockets_for_all_in_configuration()
    async with websockets.connect(url) as client:
        while True:
            try:
                binance_data = await client.recv()
                binance_data = json.loads(binance_data)
                binance_data = binance_data.get("data", [])
            except Exception as e:
                logging.error(e)
            else:
                binance_messages = get_binance_messages(binance_data)
                for source_type in client_sockets:
                    send_message(
                        client_sockets[source_type],
                        source_type,
                        binance_messages[source_type],
                    )
                    logging.info(
                        f"sent all messages to {source_type} {client_sockets[source_type]}"
                    )
                    # logging.info(f"{binance_messages[source_type]}")
                # break


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
