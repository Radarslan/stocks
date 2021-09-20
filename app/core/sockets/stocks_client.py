import asyncio
import logging
import select

from socket import AF_INET
from socket import SHUT_RDWR
from socket import SOCK_STREAM
from socket import socket
from typing import Dict
from time import sleep
from typing import Dict
from typing import List
from typing import Optional

from app.core.business_logic_layer.messages import save_messages_to_redis

from app.core.settings.settings import ENCODING_FORMAT
from app.core.settings.settings import SOCKET_CONNECTIONS
from app.core.settings.settings import SOCKET_DISCONNECT_MESSAGE
from app.core.settings.settings import SOCKET_MESSAGE_LENGTH
from app.core.settings.settings import SOCKET_SOURCE_TYPES


def get_client_socket(configuration: dict) -> socket:
    HOST = configuration.get("HOST")
    PORT = configuration.get("PORT")
    client_socket = socket(AF_INET, SOCK_STREAM)
    try:
        logging.info(f"connecting to {HOST}:{PORT}...")
        client_socket.connect((HOST, PORT))
        logging.info(f"connected to {HOST}:{PORT}...")
        client_socket.setblocking(False)
        logging.info(f"client added: {client_socket.getsockname()}")
        return client_socket
    except Exception as e:
        logging.error(
            f"client socket " f"{HOST}:{PORT} " f"connection error: {e}"
        )


def get_client_sockets_for_all_in_configuration() -> List[socket]:
    return [
        get_client_socket(configuration)
        for configuration in SOCKET_CONNECTIONS
    ]


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


def get_socket_name(name_function) -> str:
    active_socket_address = name_function()
    return f"{active_socket_address[0]}" f":{active_socket_address[1]}"


def delete_socket_from_list(sockets: List[socket], target_socket: socket):
    sockets.pop(sockets.index(target_socket))


def get_messages_from_client(
        client_sockets: List[socket], client_socket: socket,
        source_type: str
) -> List[str]:
    messages_list = []
    client_full_address = get_socket_name(client_socket.getpeername)
    messages = receive_messages(client_socket)
    if messages is None:
        logging.info(
            f"no message received "
            f"{source_type} "
            f"or {client_full_address} "
            f"server closed connection"
        )
        if client_socket in client_sockets:
            delete_socket_from_list(client_sockets, client_socket)
        return messages_list
    else:
        messages = messages.decode(ENCODING_FORMAT)
        messages_list = messages.split("\n")
    return messages_list


async def main_loop(client_sockets: List[socket]) -> None:
    source_type = "UNKNOWN"

    while True:

        read_sockets, _, exception_sockets = select.select(
            client_sockets, [], client_sockets
            )

        for notified_socket in read_sockets:
            notified_socket_address = get_socket_name(
                notified_socket.getpeername
            )
            source_type = SOCKET_SOURCE_TYPES.get(
                notified_socket_address.split(":")[1], "UNKNOWN"
            )
            messages_list = get_messages_from_client(
                client_sockets, notified_socket, source_type
            )
            await save_messages_to_redis(messages_list, source_type)
            logging.info(
                f"saved messages from "
                f"{source_type} "
                f"{notified_socket_address}"
            )

        for notified_socket in exception_sockets:
            notified_socket_address = get_socket_name(
                notified_socket.getpeername
            )
            logging.info(
                f"exception occurred for "
                f" {source_type} "
                f" {notified_socket_address} "
            )

            if notified_socket in client_sockets:
                delete_socket_from_list(client_sockets, notified_socket)
        if len(client_sockets) == 0:
            break


if __name__ == "__main__":
    client_sockets = get_client_sockets_for_all_in_configuration()
    asyncio.run(main_loop(client_sockets))
