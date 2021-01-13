# Importing Packages
from PyQt5 import QtWidgets
import ClientGUI as m
import sys
import socket
import time
import threading

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.1.108"
ADDR = (SERVER, PORT)


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


    def connect_server(self):
        SERVER, PORT = self.host.text(), int(self.port.text())
        client_name = "@" + self.client_name_text.text()
        receiver_name = "#" + self.receive_name_text.text()
        ADDR = (SERVER, PORT)
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(ADDR)
            self.status_label.setText("Connected To Successfully!")
            self.client_message_text.setDisabled(False)
            time.sleep(0.1)
            self.send_message(client_name)
            time.sleep(0.1)
            self.send_message(receiver_name)

            # Start Handling incoming messages from other client
            # Start a new thread for this Client
            thread = threading.Thread(target=self.handle_received_message)
            thread.start()
        except:
            raise Exception("Couldn't connect to server")


    def disconnect_server(self):
        self.send_message(DISCONNECT_MESSAGE)
        self.status_label.setText("Disconnect From Server!")
        self.client_message_text.setDisabled(True)


    def handle_received_message(self):
        connected = True
        while connected:
            received_message = self.client.recv(2048).decode(FORMAT)
            self.received_message_text.setText(received_message)


    def message_changed(self):
        message = self.client_message_text.text()
        self.send_message(message)
        self.client_message_text.clear()


    def send_message(self, msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)
        received_message = self.client.recv(2048).decode(FORMAT)
        self.server_message_text.setText(received_message)


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