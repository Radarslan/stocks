import asyncio
import json
import logging
import select
from time import time
from decimal import Decimal
from signal import SIGINT
from signal import SIGKILL
from signal import SIGTERM

from socket import AF_INET
from socket import SHUT_RDWR
from socket import SOCK_STREAM
from socket import socket
from typing import List
from typing import Optional

from app.core.settings.settings import ENCODING_FORMAT
from app.core.settings.settings import SOCKET_CONNECTIONS
from app.core.settings.settings import SOCKET_DISCONNECT_MESSAGE
from app.core.settings.settings import SOCKET_MESSAGE_LENGTH
from app.core.settings.settings import SOCKET_SOURCE_TYPES
from app.core.settings.settings import TIME_TO_LIVE_IN_SECONDS
from app.schemas.symbols import Asset
from app.schemas.symbols import DXFeedAsset
from app.schemas.symbols import MCFixAsset


class StocksClient:
    asset_quotes = {
        "dxfeed": {

        },
        "mc_fix": {

        }
    }

    def __init__(self):
        self.received_sigterm = False

    def signal_handler(self, signum, frame):
        signals = {
            2: "SIGINT",
            9: "SIGKILL",
            15: "SIGTERM"
        }
        if signum in signals:
            logging.info(f"received {signals[signum]}, exiting")
            self.received_sigterm = True

    async def main_loop(self) -> None:

        client_sockets = [
            self.get_client_socket(configuration)
            for configuration in SOCKET_CONNECTIONS
        ]
        source_type = "UNKNOWN"
        while not self.received_sigterm:
            # sleep to let the api start
            await asyncio.sleep(0.5)

            read_sockets, _, exception_sockets = select.select(
                client_sockets, [], client_sockets
            )

            for notified_socket in read_sockets:
                notified_socket_address = self.get_socket_name(
                    notified_socket.getpeername
                )
                source_type = SOCKET_SOURCE_TYPES.get(
                    notified_socket_address.split(":")[1], "UNKNOWN"
                )
                messages_list = self.get_messages_from_client(
                    client_sockets, notified_socket, source_type
                )
                self.save_messages(messages_list, source_type)
                logging.info(
                    f"saved messages from "
                    f"{source_type} "
                    f"{notified_socket_address}"
                )
                self.trim_asset_quotes_lists()

            for notified_socket in exception_sockets:
                notified_socket_address = self.get_socket_name(
                    notified_socket.getpeername
                )
                logging.info(
                    f"exception occurred for "
                    f" {source_type} "
                    f" {notified_socket_address} "
                )

                if notified_socket in client_sockets:
                    self.delete_socket_from_list(
                        client_sockets, notified_socket
                    )
            if len(client_sockets) == 0:
                break
        await self.close_connections(client_sockets)

    def get_client_socket(self, configuration: dict) -> socket:
        HOST = configuration.get("HOST")
        PORT = configuration.get("PORT")
        client_socket = socket(AF_INET, SOCK_STREAM)
        try:
            logging.info(f"connecting to {HOST}:{PORT}...")
            client_socket.connect((HOST, PORT))
            logging.info(f"connected to {HOST}:{PORT}...")
            client_socket.setblocking(False)
            logging.info(
                f"client added: "
                f"{self.get_socket_name(client_socket.getsockname)}"
            )
            return client_socket
        except Exception as e:
            logging.error(
                f"client socket " f"{HOST}:{PORT} " f"connection error: {e}"
            )

    @staticmethod
    def receive_messages(client_socket: socket) -> Optional[bytes]:
        try:
            message = client_socket.recv(SOCKET_MESSAGE_LENGTH)
            bytes_received = len(message)
            messages = message
            while bytes_received == SOCKET_MESSAGE_LENGTH:
                message = client_socket.recv(SOCKET_MESSAGE_LENGTH)
                messages += message
                bytes_received = len(message)

            if (
                    messages is None
                    or messages == b""
                    or messages == SOCKET_DISCONNECT_MESSAGE
            ):
                return None
            return messages
        except Exception as e:
            logging.error(e)
            return None

    @staticmethod
    def get_socket_name(name_function) -> str:
        active_socket_address = name_function()
        return f"{active_socket_address[0]}:{active_socket_address[1]}"

    @staticmethod
    def delete_socket_from_list(sockets: List[socket], target_socket: socket):
        sockets.pop(sockets.index(target_socket))

    def get_messages_from_client(
            self,
            client_sockets: List[socket], client_socket: socket,
            source_type: str
    ) -> List[str]:
        messages_list = []
        client_full_address = self.get_socket_name(client_socket.getpeername)
        messages = self.receive_messages(client_socket)
        if messages is None:
            logging.info(
                f"no message received "
                f"{source_type} "
                f"or {client_full_address} "
                f"server closed connection"
            )
            if client_socket in client_sockets:
                self.delete_socket_from_list(client_sockets, client_socket)
            return messages_list
        else:
            messages = messages.decode(ENCODING_FORMAT)
            messages_list = messages.split("\n")
        return messages_list

    def save_messages(
            self,
            messages_list: List[str], source_type: str
    ) -> None:

        for message in messages_list:
            data = Asset()
            if source_type == "mc_fix" and len(message) > 0:
                try:
                    # {"s": "GBPUSD", "p": {"r": 1.34023,
                    # "t": "1606811740.13800"}}
                    message = json.loads(message)
                    data = MCFixAsset()
                    data.symbol = message.get("s", "")
                    p = message.get("p", {})
                    data.rate = Decimal(str(p.get("r", 0)))
                    data.timestamp = int(Decimal(p.get("t", 0)) * 1000)
                except Exception as e:
                    logging.error(e)

            elif source_type == "dxfeed":
                # 1630856330469, UNIUSDT, BINANCE, 28.95000000, 0, 0,
                message_values = message.split(",")
                if len(message_values) == 7:
                    data = DXFeedAsset()
                    data.market = message_values[2]
                    data.symbol = message_values[1]
                    data.rate = Decimal(message_values[3])
                    data.timestamp = int(message_values[0])
            if data.symbol != "":
                if data.symbol not in self.asset_quotes[source_type]:
                    self.asset_quotes[source_type][data.symbol] = []
                self.asset_quotes[source_type][data.symbol].append(data)

    def trim_asset_quotes_lists(self) -> None:
        for source_type, asset_quotes in self.asset_quotes.items():
            for symbol, quotes in asset_quotes.items():
                start_index = 0
                found_old = False
                timestamp = time()
                for i, asset_quote in enumerate(quotes):
                    if (timestamp - asset_quote.timestamp / 1000
                            >= TIME_TO_LIVE_IN_SECONDS):
                        found_old = True
                    elif (found_old and timestamp - asset_quote.timestamp
                          < TIME_TO_LIVE_IN_SECONDS):
                        start_index = i
                        break
                if start_index > 0:
                    self.asset_quotes[source_type][symbol] = quotes[
                        start_index:-1
                    ]

    async def close_connections(self, client_sockets: List[socket]):
        logging.info("closing connections")
        for client_socket in client_sockets:
            logging.info(
                f"closing connection for "
                f"{self.get_socket_name(client_socket.getpeername)}"
            )
            client_socket.shutdown(SHUT_RDWR)
            client_socket.close()
