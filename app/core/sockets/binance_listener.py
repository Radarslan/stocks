import asyncio
import json
import logging
import websockets

from app.core.business_logic_layer.messages import get_binance_messages
from app.core.settings.settings import BINANCE_WEB_SOCKET_URL
from app.core.sockets.stocks_server import send_message
from app.core.sockets.stocks_server import (
    get_server_sockets_for_all_in_configuration
)


async def main():
    url = BINANCE_WEB_SOCKET_URL
    server_sockets = get_server_sockets_for_all_in_configuration()
    client_sockets = {
        source_type: server_sockets[source_type].accept()[0]
        for source_type in server_sockets
    }
    async with websockets.connect(url) as client:
        while True:
            try:
                binance_data = await client.recv()
                binance_data = json.loads(binance_data)
                binance_data = binance_data.get("data", [])
                binance_messages = get_binance_messages(binance_data)
            except Exception as e:
                logging.error(e)
            try:
                for source_type in client_sockets:
                    send_message(
                        client_sockets[source_type],
                        source_type,
                        binance_messages[source_type],
                    )
                    logging.info(
                        f"sent all messages to {source_type} "
                        f"{client_sockets[source_type]}"
                    )
            except Exception as e:
                logging.error(f"failed to send data, exiting: {e}")
                break


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
