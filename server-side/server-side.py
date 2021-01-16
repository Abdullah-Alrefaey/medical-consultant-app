# Importing Modules
import socket
import threading
import ssl
from tinydb import TinyDB, Query


HEADER = 64                                                     # Number of Bytes for message header
PORT = 5050                                                     # PORT Number that the socket will listen to
SERVER = socket.gethostbyname(socket.gethostname())             # Get IP (HOST) of local connected device
ADDR = (SERVER, PORT)                                           # Address of socket to connect
FORMAT = 'utf-8'                                                # Encoding and Decoding messages Format
DISCONNECT_MESSAGE = "!DISCONNECT"                              # DISCONNECT_MESSAGE (if sent, the server will close connection of that client)
TIMEOUT_MESSAGE = "!TIMEOUT"                    # TIMEOUT_MESSAGE (if sent, the server will close connection of that client)
TIMEOUT_SECONDS = 180                                           # Number of seconds to wait before disconnect the idle client
NUM_CLIENT = 0                                                  # Number of current clients
clientsDB = {}                                                  # Dictionary to save clients
db = TinyDB('Users.json')                                       # Database Object for Registered User
User = Query()                                                  # Database Query for searching


def main():
    # Create Socket Object and bind it to specific address
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    # Starting Server
    start_server(server)


def disconnect_client(conn, addr, msg):
    global NUM_CLIENT
    print(f"[Disconnecting Client] {addr}")
    conn.send(f"{msg}".encode(FORMAT))
    conn.close()
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")

    # Remove client from clientsDB
    clientsDB.pop(addr[1], None)
    NUM_CLIENT -= 1


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        # Handle socket.timeout exception (raised by socket.settimeout()) 
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
        except socket.timeout:
            disconnect_client(conn, addr, "!TIMEOUT")
            break

        # If socket received a message header successfully
        if msg_length:
            msg_length = int(msg_length)
            
            # Actual Message
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg:
                # Save client name one time
                if msg[0] == "@":
                    clientsDB[addr[1]]['name'] = msg[1:]

                # Save Receiver name one time
                elif msg[0] == "#":
                    clientsDB[addr[1]]['receiver'] = msg[1:]
                    recv_name = clientsDB[addr[1]]['receiver']

                elif msg == DISCONNECT_MESSAGE:
                    disconnect_client(conn, addr, "Disconnect Client")
                    connected = False
                else:
                    clientsDB[addr[1]]['messages'].append(msg)
                    try:
                        transfer_message_to_client(recv_name, msg)
                        print(f"[{addr}][Msg Received] {msg}")
                    except:
                        raise Exception("Couldn't send message to client")

                # Check if Client Finished Sending Initial Data
                if clientsDB[addr[1]]['name'] and clientsDB[addr[1]]['receiver']:
                    # Check if Name is in The DB, If Not Disconnect
                    Result = db.search(User.name == clientsDB[addr[1]]['name'])
                    if not Result:
                        conn.send(f"User Not Authorized".encode(FORMAT))
                        conn.close()
                        print(f"[Disconnecting Client] {addr} {clientsDB[addr[1]]['name']}, Not Authorized")
                        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
                        break
                    else:
                        # Send Message back to same client
                        conn.send(f"$Welcome, {clientsDB[addr[1]]['name']}".encode(FORMAT))

def transfer_message_to_client(receiverName, msg):
    # Get the receiver who the client want to send message to
    for key, value in clientsDB.items():
        if value['name'] == receiverName:
            print(f"found receiver: {receiverName}")
            receiver_conn = value['connection']
            receiver_conn.send(f"{msg}".encode(FORMAT))
            break


def start_server(server):
    print("[STARTING] server is starting...")
    global NUM_CLIENT
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

        # Add the new Client to a dictionary
        NUM_CLIENT += 1
        new_client = {"id": NUM_CLIENT, "name": "", "receiver": "", "connection": conn, "address": addr, "messages": []}
        print(new_client)

        # TODO
        # Check if client Exists in Database
        # If yes, create thread
        # If no, don't create thread and close conn
        clientsDB[addr[1]] = new_client
        # Start a new thread for this Client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


if __name__ == '__main__':
    main()
