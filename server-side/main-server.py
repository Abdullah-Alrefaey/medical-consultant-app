# Importing Packages
from PyQt5 import QtWidgets
import ServerGUI as m
import sys
import socket
import selectors
import types
import traceback
import libserver

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    message = libserver.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)


class MedicalConsultantServer(m.Ui_MainWindow):

    def __init__(self, starterWindow):
        """
        Main loop of the UI
        :param mainWindow: QMainWindow Object
        """
        super(MedicalConsultantServer, self).setupUi(starterWindow)

        # Setup Start Server Button
        self.start_btn.clicked.connect(self.start_server)

        self.server_message_text.returnPressed.connect(self.message_changed)


    def start_server(self):
        print("Clicked Connect")
        host, port = self.host.text(), int(self.port.text())
        message = self.client_message_text.text()
        print(host, port)

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
        message = self.server_message_text.text()
        self.server_message_text.clear()


def main():
    """
    the application startup functions
    :return:
    """
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = MedicalConsultantServer(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
