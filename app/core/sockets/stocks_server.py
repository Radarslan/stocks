import asyncio
import logging
import select
from socket import AF_INET
from socket import SHUT_RDWR
from socket import SO_REUSEADDR
from socket import SOCK_STREAM
from socket import SOL_SOCKET
from socket import socket
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


def get_server_socket(configuration: dict) -> socket:
    HOST = configuration.get("HOST")
    PORT = configuration.get("PORT")
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    logging.info(f"binding {HOST}:{PORT}...")
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logging.info(f"listening for connections on {HOST}:{PORT}...")
    return server_socket


def get_server_sockets_for_all_in_configuration() -> Dict[str, socket]:
    return {
        configuration.get("source_type"): get_server_socket(configuration)
        for configuration in SOCKET_CONNECTIONS
    }


def send_message(
        client_socket: socket, source_type: str, message: str
) -> None:
    bytes_sent = 0
    message_length = len(message)

    client_socket_address = client_socket.getsockname()
    client_socket_full_address = (
        f"{client_socket_address[0]}" f":{client_socket_address[1]}"
    )
    while bytes_sent < message_length:
        try:
            sent = client_socket.send(
                message[bytes_sent:].encode(ENCODING_FORMAT)
            )
            bytes_sent += sent
        except Exception as e:
            logging.error(
                f"{source_type} {client_socket_full_address} "
                f"client socket "
                f"sending error: {e}"
            )
            try:
                client_socket.send(
                    SOCKET_DISCONNECT_MESSAGE.encode(ENCODING_FORMAT)
                )
                client_socket.shutdown(SHUT_RDWR)
                client_socket.close()
            except Exception as e:
                logging.error(
                    f"{source_type} {client_socket_full_address} "
                    f"client socket "
                    f" closing error: {e}"
                )
            del client_socket
            break
