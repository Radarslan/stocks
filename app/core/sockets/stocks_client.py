import logging
from socket import AF_INET
from socket import SHUT_RDWR
from socket import SOCK_STREAM
from socket import socket
from typing import Dict

from app.core.settings.settings import ENCODING_FORMAT
from app.core.settings.settings import SOCKET_CONNECTIONS
from app.core.settings.settings import SOCKET_DISCONNECT_MESSAGE


def get_client_socket(configuration: dict) -> socket:
    HOST = configuration.get("HOST")
    PORT = configuration.get("PORT")
    client_socket = socket(AF_INET, SOCK_STREAM)
    try:
        logging.info(f"connecting to {HOST}:{PORT}...")
        client_socket.connect((HOST, PORT))
        logging.info(f"connected to {HOST}:{PORT}...")
        client_socket.setblocking(False)
        return client_socket
    except Exception as e:
        logging.error(
            f"client socket " f"{HOST}:{PORT} " f"connection error: {e}"
        )


def get_client_sockets_for_all_in_configuration() -> Dict[str, socket]:
    return {
        configuration.get("source_type"): get_client_socket(configuration)
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
            # logging.info(
            #     f"sent to {source_type} "
            #     f"{client_socket_full_address} "
            #     f"{sent} bytes"
            #     )
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
