# Importing Modules
import socket
import threading

HEADER = 64                                             # Number of Bytes for message header
PORT = 5050                                             # PORT Number that the socket will listen to
SERVER = socket.gethostbyname(socket.gethostname())     # Get IP (HOST) of local connected device
ADDR = (SERVER, PORT)                                   # Address of socket to connect
FORMAT = 'utf-8'                                        # Encoding and Decoding messages Foramt
DISCONNECT_MESSAGE = "!DISCONNECT"                      # DISCONNECT_MESSAGE (if sent, the server will close connection of that client)
TIMEOUT_SECONDS = 180                                   # Number of seconds to wait before disconnect the idle client
NUM_CLIENT = 0                                          # Number of current clients
clientsDB = {}                                          # Dictionary to save clients

# Create Socket Object and bind it to specific address
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def disconnect_client(conn, addr, msg):
    global NUM_CLIENT
    print(f"[Disconnecting Client] {conn}")
    conn.send(f"{msg}".encode(FORMAT))
    conn.close()
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")

    # Remove client from DB
    clientsDB.pop(addr[1], None)
    NUM_CLIENT -= 1


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:        
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
        except socket.timeout:
             disconnect_client(conn, addr, "!TIMEOUT")

        if msg_length:
            msg_length = int(msg_length)
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
                        print(f"[{addr}] {msg}")
                    except:
                        raise Exception("Couldn't send message to client")

                # Send Message back to same client
                # conn.send(f"{msg}".encode(FORMAT))

    # conn.close()
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")
        

def transfer_message_to_client(receiverName, msg):
    # Get the receiver who the client want to send message to
    for key, value in clientsDB.items():
        if value['name'] == receiverName:
            print(f"found receiver: {receiverName}")
            receiver_conn = value['connection']
            receiver_conn.send(f"{msg}".encode(FORMAT))
            break


def start_server():
    print("[STARTING] server is starting...")
    global NUM_CLIENT
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        # Accept Client Connection
        conn, addr = server.accept()
        conn.settimeout(TIMEOUT_SECONDS)

        # Start a new thread for this Client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

        # Add the new Client to a dictionary
        NUM_CLIENT += 1
        new_client = {"id": NUM_CLIENT, "name": "", "receiver": "", "connection": conn, "address": addr, "messages": []}
        clientsDB[addr[1]] = new_client
        print(new_client)


# Starting Server
start_server()