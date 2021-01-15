# Importing Packages
from PyQt5 import QtWidgets, QtCore
import ClientGUI as m
import sys
import socket
import time
import ssl
from threading import Thread, Event

HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
TIMEOUT_MESSAGE = "!TIMEOUT"


class MedicalConsultantClient(m.Ui_MainWindow):

    def __init__(self, starterWindow):
        """
        Main loop of the UI
        :param mainWindow: QMainWindow Object
        """
        super(MedicalConsultantClient, self).setupUi(starterWindow)

        # Setup
        self.connect_btn.clicked.connect(self.connect_server)
        self.disconnect_btn.clicked.connect(self.disconnect_server)
        self.client_message_text.returnPressed.connect(self.message_changed)
        self.client_message_text.setDisabled(True)
        self.disconnect_btn.setDisabled(True)

    def connect_server(self):
        self.client_name = self.client_name_text.text()
        self.receiver_name = self.receive_name_text.text()
        SERVER, PORT = self.host.text(), int(self.port.text())
        ADDR = (SERVER, PORT)

        # Creat a new Socket
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            print(f"Error creating socket: {e}")
            sys.exit(1)

        # Connect to a given host/port
        try:
            self.client.connect(ADDR)
        except socket.gaierror as e:
            print(f"Address-related error connecting to server: {e}")
            sys.exit(1)
        except socket.error as e:
            print(f"Connection error: {e}")
            sys.exit(1)

        # If Connected Successfully
        self.status_label.setText("Connected To Successfully!")
        self.server_message_text.setText("...")
        self.client_message_text.setDisabled(False)
        self.disconnect_btn.setDisabled(False)

        # Send Client and Receiver Name
        try:
            time.sleep(0.1)
            self.send_message("@" + self.client_name)
            time.sleep(0.1)
            self.send_message("#" + self.receiver_name)
        except socket.error as e:
            print(f"Error client and receiver sending data: {e}")

        # Start Handling incoming messages from other client
        # Start a new Timer thread for this Client
        self.client_timer = setInterval(0.3, self.handle_received_message)

    def disconnect_server(self):
        self.send_message(DISCONNECT_MESSAGE)
        self.status_label.setText("Disconnect From Server!")
        self.server_message_text.setText("Bye, " + self.client_name_text.text())
        self.client_message_text.setDisabled(True)
        self.disconnect_btn.setDisabled(True)
        self.client_timer.cancel()
        self.client.close()

    def handle_received_message(self):
        global received_message
        try:
            received_message = self.client.recv(2048).decode(FORMAT)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            sys.exit(1)
        # socket was closed for some other reason
        except ConnectionResetError:
            self.status_label.setText("Server is Closed!")
            self.client_message_text.setDisabled(True)
            self.disconnect_btn.setDisabled(True)

        # Handle TIMEOUT Connection
        if received_message == TIMEOUT_MESSAGE:
            self.client_timer.cancel()
            self.client.close()
            self.client = None
            self.server_message_text.setText(received_message)
            self.status_label.setText("Disconnect From Server!")
            self.client_message_text.setDisabled(True)
            self.disconnect_btn.setDisabled(True)
        elif received_message[0] == "$":
            self.server_message_text.setText(received_message[1:])
        elif received_message == "User Not Authorized":
            self.client_timer.cancel()
            self.client.close()
            self.client = None
            self.server_message_text.setText(received_message)
            self.status_label.setText("Not Authorized")
            self.client_message_text.setDisabled(True)
            self.disconnect_btn.setDisabled(True)
        else:
            self.received_message_text.setText(received_message)

            # Append Received Message to chat area on left side
            received_message = self.receiver_name + ": " + received_message
            self.chat_area.append(received_message)
            self.chat_area.setAlignment(QtCore.Qt.AlignLeft)

            # self.chatting.setText(
            #     '%s<p>%s</p>' % (self.chatting.text(), received_message))
            # self.chatting.setAlignment(QtCore.Qt.AlignLeft)


    def message_changed(self):
        message = self.client_message_text.text()

        # Check if client disconnect from server or normal message
        if message == DISCONNECT_MESSAGE:
            self.disconnect_server()
        else:
            self.send_message(message)
            # Append Sent Message to chat area on right side
            self.chat_area.append(message)
            self.chat_area.setAlignment(QtCore.Qt.AlignRight)

            # self.chatting.setText(
            #     '%s<p>%s</p>' % (self.chatting.text(), message))
            # self.chatting.setAlignment(QtCore.Qt.AlignRight)
            # self.client_message_text.clear()


    def send_message(self, msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)


# Class to creat an interval for specific function using Threads
class setInterval():
    def __init__(self, interval, action) :
        self.interval = interval
        self.action = action
        self.stopEvent = Event()
        thread = Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) :
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime-time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self) :
        self.stopEvent.set()


def main():
    """
    the application startup functions
    :return:
    """
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = MedicalConsultantClient(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
