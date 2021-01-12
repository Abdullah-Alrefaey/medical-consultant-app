# Importing Packages
from PyQt5 import QtWidgets
import mainGUI as m
import sys
import socket
import selectors
import types
import traceback
import libclient

sel = selectors.DefaultSelector()


def create_request(action, value):
    if action == "search":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value),
        )
    else:
        return dict(
            type="binary/custom-client-binary-type",
            encoding="binary",
            content=bytes(action + value, encoding="utf-8"),
        )


def start_connection(host, port, request):
    addr = (host, port)
    print("starting connection to", addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = libclient.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)




class MedicalConsultant(m.Ui_MainWindow):

    def __init__(self, starterWindow):
        """
        Main loop of the UI
        :param mainWindow: QMainWindow Object
        """
        super(MedicalConsultant, self).setupUi(starterWindow)

        # self.client_message_text.setText("Hello")

        # Setup Connect Button
        self.connect_btn.clicked.connect(self.connect_server)

        self.client_message_text.returnPressed.connect(self.message_changed)


    def connect_server(self):
        print("Clicked Connect")
        host, port, action, value = self.host.text(), int(self.port.text()), self.action.text(), self.value.text()
        request = create_request(action, value)
        start_connection(host, port, request)
        print(host, port, action, value)

        try:
            while True:
                events = sel.select(timeout=1)
                for key, mask in events:
                    message = key.data
                    try:
                        message.process_events(mask)
                    except Exception:
                        print(
                            "main: error: exception for",
                            f"{message.addr}:\n{traceback.format_exc()}",
                        )
                        message.close()
                # Check for a socket being monitored to continue.
                if not sel.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            sel.close()


    def message_changed(self):
        message = self.client_message_text.text()
        self.client_message_text.clear()


def main():
    """
    the application startup functions
    :return:
    """
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = MedicalConsultant(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
