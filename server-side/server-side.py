import socket 
import threading

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

num_clients = 0
clientsDB = {}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg:
                # Save client name one time
                if msg[0] == "@":
                    clientsDB[addr[1]]['name'] = msg[1:]
                    print(f"Client Name is: {clientsDB[addr[1]]['name']}")
                # Save Receiver name one time
                elif msg[0] == "#":
                    clientsDB[addr[1]]['receiver'] = msg[1:]
                    print(f"Receiver Name is: {clientsDB[addr[1]]['receiver']}")
                elif msg == DISCONNECT_MESSAGE:
                    connected = False
                else:
                    clientsDB[addr[1]]['messages'].append(msg)

                print(f"[{addr}] {msg}")
                recv_name = clientsDB[addr[1]]['receiver']

                try:
                    transfer_message_to_client(recv_name, msg)
                except:
                    raise Exception("Couldn't send message to client")
                # Send Message back to same client
                # conn.send(f"{msg}".encode(FORMAT))

    conn.close()
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
    num_clients = 0
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        # Accept Client Connection
        conn, addr = server.accept()

        # Start a new thread for this Client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

        # Add the new Client to a dictionary
        num_clients += 1
        new_client = {"id": num_clients, "name": "", "receiver": "", "connection": conn, "messages": []}
        clientsDB[addr[1]] = new_client
        print(new_client)


# Starting Server
start_server()