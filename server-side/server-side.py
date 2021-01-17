# Importing Modules
import socket
import threading
import ssl
from tinydb import TinyDB, Query


HEADER = 64                                             # Number of Bytes for message header
PORT = 5050                                             # PORT Number that the socket will listen to
SERVER = socket.gethostbyname(socket.gethostname())     # Get IP (HOST) of local connected device
ADDR = (SERVER, PORT)                                   # Address of socket to connect
FORMAT = 'utf-8'                                        # Encoding and Decoding messages Format
DISCONNECT_MESSAGE = "!DISCONNECT"                      # DISCONNECT_MESSAGE (if sent, the server will close connection of that client)
TIMEOUT_MESSAGE = "!TIMEOUT"                            # TIMEOUT_MESSAGE (if sent, the server will close connection of that client)
TIMEOUT_SECONDS = 20                                    # Number of seconds to wait before disconnect the idle client
NUM_CLIENT = 0                                          # Number of current clients
clientsDB = {}                                          # Dictionary to save clients
db = TinyDB('Users.json')                               # Database Object for Registered User
User = Query()                                          # Database Query for searching


def start_server():
    """
    This function responsible for:
    1. Creating a new Socket Object (Server)
    2. Bind the server to specific address
    3. Make it a listening socket (enables a server to accept() connections)
    :return:
    """

    global NUM_CLIENT

    """
    :param socket.AF_INET: address family (Internet address family for IPv4)
    :param socket.SOCK_STREAM: Socket Type (TCP)
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    print("[STARTING] server is starting...")
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    while True:
        # Accept Client Connection
        tempconn, addr = server.accept()

        # Make the socket connection to the clients secure through SSLSocket
        conn = ssl.wrap_socket(tempconn,
                               server_side=True,
                               ca_certs="RootCA.pem",
                               certfile="RootCA.crt",
                               keyfile="RootCA.key",
                               cert_reqs=ssl.CERT_OPTIONAL,
                               ssl_version=ssl.PROTOCOL_TLSv1_2)
        conn.settimeout(TIMEOUT_SECONDS)

        # Add the new Client to a dictionary (Volatile Database)
        NUM_CLIENT += 1
        new_client = {"id": NUM_CLIENT, "name": "", "receiver": "", "connection": conn, "address": addr, "messages": []}
        print(new_client)
        clientsDB[addr[1]] = new_client

        # Start a new thread for this Client
        # Using Multiple threads to allow Multi-client connections.
        # Each thread handles one client in a separate function
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        # Keep tracking how many users are connected to the socket.
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


def handle_client(conn, addr):
    """

    :param conn: Socket Object (Client Connection)
    :param addr: Address (IP, PORT Number) of the client
    :return:
    """
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        # Handle socket.timeout exception (raised by socket.settimeout()) 
        try:
            # Receive the message header sent from client side
            # This header is responsible for knowing the length of the actual incoming message
            msg_length = conn.recv(HEADER).decode(FORMAT)
        except socket.timeout:
            disconnect_client(conn, addr, "!TIMEOUT")
            break

        # If socket received a message header successfully
        if msg_length:
            msg_length = int(msg_length)
            
            # Receive The Actual Message
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg:
                # Save client name one time
                if msg[0] == "@":
                    clientsDB[addr[1]]['name'] = msg[1:]

                # Save Receiver name one time
                elif msg[0] == "#":
                    clientsDB[addr[1]]['receiver'] = msg[1:]

                elif msg == DISCONNECT_MESSAGE:
                    disconnect_client(conn, addr, "Disconnect Client")
                    connected = False
                else:
                    # This case for the normal message
                    clientsDB[addr[1]]['messages'].append(msg)

                    try:
                        transfer_message_to_client(clientsDB[addr[1]]['receiver'], msg)
                        print(f"[{addr}][Msg Received] {msg}")
                    except socket.error as e:
                        print(f"Error client and receiver sending data: {e}")
                        print("Couldn't send message to client")

                # Check if Client Finished Sending Initial Data
                if clientsDB[addr[1]]['name'] and clientsDB[addr[1]]['receiver']:
                    # Check if Client Name Exists in The Database
                    # If not exists, close the socket connection to disconnect the user
                    result = db.search(User.name == clientsDB[addr[1]]['name'])
                    if not result:
                        conn.send(f"User Not Authorized".encode(FORMAT))
                        conn.close()
                        print(f"[Disconnecting Client] {addr} {clientsDB[addr[1]]['name']}, Not Authorized")
                        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
                        break
                    else:
                        # Send Message back to same client
                        try:
                            conn.send(f"$Welcome, {clientsDB[addr[1]]['name']}".encode(FORMAT))
                        except socket.error as e:
                            print(f"Error client and receiver sending data: {e}")
                            print("Couldn't send message to client")

                # If the receiver is not connected
                elif not clientsDB[addr[1]]['receiver']:
                    print("Receiver is not connected")


def disconnect_client(conn, addr, msg):
    """

    :param conn: Socket Object (Client Connection)
    :param addr: Address (IP, PORT Number) of the client
    :param msg: Message to be sent to user
    :return:
    """
    global NUM_CLIENT
    print(f"[Disconnecting Client] {addr}")
    conn.send(f"{msg}".encode(FORMAT))
    conn.close()
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")

    # Remove client from clientsDB
    clientsDB.pop(addr[1], None)
    NUM_CLIENT -= 1


def transfer_message_to_client(receiver_name, msg):
    """

    :param receiver_name: The client name to send message to him
    :param msg: The Actual Message to be sent
    :return:
    """

    # Search in clientsDB to get the receiver who the client want to send message to
    for key, value in clientsDB.items():
        if value['name'] == receiver_name:
            print(f"found receiver: {receiver_name}")
            receiver_conn = value['connection']
            receiver_conn.send(f"{msg}".encode(FORMAT))
            break


if __name__ == '__main__':
    # Start Main Program
    start_server()
