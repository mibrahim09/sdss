import sys
import os
import threading
import socket
import time
import datetime
from datetime import timezone
import uuid
import math
import struct
# https://bluesock.org/~willkg/dev/ansi.html
ANSI_RESET = "\u001B[0m"
ANSI_RED = "\u001B[31m"
ANSI_GREEN = "\u001B[32m"
ANSI_YELLOW = "\u001B[33m"
ANSI_BLUE = "\u001B[34m"

_NODE_UUID = str(uuid.uuid4())[:8]


def print_yellow(msg):
    print(f"{ANSI_YELLOW}{msg}{ANSI_RESET}")


def print_blue(msg):
    print(f"{ANSI_BLUE}{msg}{ANSI_RESET}")


def print_red(msg):
    print(f"{ANSI_RED}{msg}{ANSI_RESET}")


def print_green(msg):
    print(f"{ANSI_GREEN}{msg}{ANSI_RESET}")


def get_broadcast_port():
    return 35498


def get_node_uuid():
    return _NODE_UUID


class NeighborInfo(object):
    def __init__(self, delay, last_timestamp, ip=None, tcp_port=None):
        # Ip and port are optional, if you want to store them.
        self.delay = delay
        self.last_timestamp = last_timestamp
        self.ip = ip
        self.tcp_port = tcp_port


############################################
#######  Y  O  U  R     C  O  D  E  ########
############################################


# Don't change any variable's name.
# Use this hashmap to store the information of your neighbor nodes.
neighbor_information = {}
tcp_connections = {}
MY_TCP_PORT = 0
# Leave the server socket as global variable.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Leave broadcaster as a global variable.
broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setup the UDP socket


def send_broadcast_thread(port):
    node_uuid = get_node_uuid()
    while True:
        # TODO: write logic for sending broadcasts.
        BROADCAST_STR = str(node_uuid) + ' ON ' + str(port)
        # print(BROADCAST_STR)
        packet = struct.pack(str(len(BROADCAST_STR)) + 's', bytes(BROADCAST_STR, 'utf-8'))
        broadcaster.sendto(packet, ('255.255.255.255', get_broadcast_port()))
        time.sleep(1)   # Leave as is.


def receive_broadcast_thread():
    """
    Receive broadcasts from other nodes,
    launches a thread to connect to new nodes
    and exchange timestamps.
    """
    current_node = get_node_uuid()
    while True:
        # TODO: write logic for receiving broadcasts.
        data, (ip, port) = broadcaster.recvfrom(4096)
        items = data.decode('UTF-8').split(' ')
        key = items[0]
        actual_port = int(items[2])
        if key != current_node:
            print_blue(f"RECV: {data} FROM: {ip}:{port}")

            if key not in neighbor_information or neighbor_information[key].last_timestamp % 10 == 0:
                tcp_thread = daemon_thread_builder(exchange_timestamps_thread, args=(key, ip, actual_port, ))
                tcp_thread.start()
            else:
                neighbor_information[key].last_timestamp = neighbor_information[key].last_timestamp + 1

def tcp_server_thread(accepted_socket, address):
    """
    Accept connections from other nodes and send them
    this node's timestamp once they connect.
    """
    current_timestamp = datetime.datetime.now().replace(tzinfo=timezone.utc).timestamp()
    accepted_socket.sendto(struct.pack('!f', current_timestamp), address)
    accepted_socket.close()
    pass


def exchange_timestamps_thread(other_uuid: str, other_ip: str, other_tcp_port: int):
    """
    Open a connection to the other_ip, other_tcp_port
    and do the steps to exchange timestamps.

    Then update the neighbor_info map using other node's UUID.
    """
    print_yellow(f"ATTEMPTING TO CONNECT TO {other_uuid}")
    address = (other_ip, other_tcp_port)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(address)
    received_time_stamp = struct.unpack('!f', tcp_socket.recv(4096))[0]
    current_timestamp = datetime.datetime.now().replace(tzinfo=timezone.utc).timestamp()

    delay = current_timestamp - received_time_stamp
    # print_red(f'Current: [{current_timestamp}] ==> Received [{received_time_stamp}]')
    print_red(f'[{other_uuid}] Current delay {abs(delay)}')
    node = NeighborInfo(delay, 1, other_ip, other_tcp_port)
    neighbor_information.update({other_uuid: node})

    pass


def daemon_thread_builder(target, args=()) -> threading.Thread:
    """
    Use this function to make threads. Leave as is.
    """
    th = threading.Thread(target=target, args=args)
    th.setDaemon(True)
    return th


def entrypoint():
    server.bind(('', 0))
    server.listen(5)
    MY_TCP_PORT = server.getsockname()[1]
    print('Server Initialized on port: ', MY_TCP_PORT)

    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcaster.bind(('', get_broadcast_port()))

    send_thread = daemon_thread_builder(send_broadcast_thread, args=(MY_TCP_PORT, ))
    send_thread.start()

    receive_thread = daemon_thread_builder(receive_broadcast_thread, args=())
    receive_thread.start()

    while True:
        accepted_socket, address = server.accept()
        accept_thread = daemon_thread_builder(tcp_server_thread, args=(accepted_socket, address, ))
        accept_thread.start()

    # for value in neighbor_information.values():
    #     print('key:', value)
    # for value in neighbor_information.keys():
    #     print('value:', value)

    pass

############################################
############################################


def main():
    """
    Leave as is.
    """
    print("*" * 50)
    print_red("To terminate this program use: CTRL+C")
    print_red("If the program blocks/throws, you have to terminate it manually.")
    print_green(f"NODE UUID: {get_node_uuid()}")
    print("*" * 50)
    #time.sleep(2)   # Wait a little bit.
    entrypoint()


if __name__ == "__main__":
    main()