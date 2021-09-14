import asyncio
import logging
import select
from socket import AF_INET
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

"""
questions:
0) how information will be sent ot server?
1) how many clients will be connected?
2) 

create async function that
0) creates server socket, binds address and listens to it
1) receives data non stop
2) parses data check socket buffering video
2) writes data to redis
1) need to create a loop for app cfg parse
2) create a thread for each entry
    _thread = threading.Thread(target=asyncio.run, args=(some_callback("some 
    text"),))
    _thread.start()
3) 
"""


def get_server_socket(configuration: dict) -> socket:
    HOST = configuration.get("HOST")
    PORT = configuration.get("PORT")
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logging.info(f"listening for connections on {HOST}:{PORT}...")
    return server_socket


def get_server_sockets_for_all_in_configuration() -> List[socket]:
    return [
        get_server_socket(configuration)
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


def get_messages_from_client(
    client_sockets: Dict[str, socket], client_socket: socket, source_type: str
) -> List[str]:
    messages_list = []
    client_full_address = get_socket_name(client_socket.getpeername)
    messages = receive_messages(client_socket)
    if messages is None:
        logging.info(
            f"no message received "
            f"{source_type} "
            f"or {client_full_address} "
            f"client closed connection"
        )
        if client_full_address in client_sockets:
            del client_sockets[client_full_address]
        return messages_list
    else:
        # logging.info(
        #     f"got messages from "
        #     f"{source_type} "
        #     f"{client_full_address}"
        # )
        messages = messages.decode(ENCODING_FORMAT)
        messages_list = messages.split("\n")

        client_sockets[client_full_address] = client_socket
    return messages_list


async def main_loop(server_sockets: List[socket]) -> None:
    client_sockets = {}
    source_type = "UNKNOWN"

    while True:
        sockets_list = server_sockets + list(client_sockets.values())

        read_sockets, _, exception_sockets = select.select(
            sockets_list, [], sockets_list
        )

        for notified_socket in read_sockets:
            notified_socket_address = get_socket_name(
                notified_socket.getsockname
            )
            source_type = SOCKET_SOURCE_TYPES.get(
                notified_socket_address.split(":")[1], "UNKNOWN"
            )
            if notified_socket in server_sockets:
                client_socket, client_address = notified_socket.accept()
                client_socket_address = (
                    f"{client_address[0]}" f":{client_address[1]}"
                )
                # logging.info(
                #     f"accepted new connection from "
                #     f"{client_socket_address}"
                # )
                messages_list = get_messages_from_client(
                    client_sockets, client_socket, source_type
                )
                # save_messages_to_redis(messages_list, source_type)
                await save_messages_to_redis(messages_list, source_type)
                logging.info(
                    f"saved messages from "
                    f"{source_type} "
                    f"{notified_socket_address}"
                )
            else:
                messages_list = get_messages_from_client(
                    client_sockets, notified_socket, source_type
                )
                # save_messages_to_redis(messages_list, source_type)
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
            if (
                notified_socket_address is None
                or notified_socket_address == ()
            ):
                notified_socket_address = get_socket_name(
                    notified_socket.getsockname
                )
                if notified_socket_address in client_sockets:
                    del client_sockets[notified_socket_address]

            logging.info(
                f"exception occurred for "
                f" {source_type} "
                f" {notified_socket_address} "
            )

            if notified_socket_address in client_sockets:
                del client_sockets[notified_socket_address]

        if len(sockets_list) == 0:
            break

        if len(client_sockets) == 0:
            sleep(180)
            if len(client_sockets) == 0:
                if len(server_sockets) > 0:
                    for server_socket in server_sockets:
                        server_socket.close()
                break


if __name__ == "__main__":
    server_sockets = get_server_sockets_for_all_in_configuration()
    asyncio.run(main_loop(server_sockets))
    # for server_socket in server_sockets:
    #     thread = Thread(target=main_loop, args=(server_socket,))
    #     thread.name = f"{server_socket.getsockname()}"
    #     logging.info(f"starting thread for {server_socket}")
    #     thread.start()
    #     logging.info(f"started thread for {server_socket}")
