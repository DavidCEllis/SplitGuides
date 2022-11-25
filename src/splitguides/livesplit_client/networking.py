# COMPILE_PREFABS
"""
Socket based connection model
"""
import socket

from prefab_classes import prefab, attribute

BUFFER_SIZE = 4096


@prefab(compile_prefab=True)
class LivesplitConnection:
    server = attribute(default="localhost")
    port = attribute(default=16834)
    timeout = attribute(default=1)
    sock = attribute(default=None, init=False, repr=False)

    def connect(self):
        """
        Attempt to connect to the livesplit server
        :return: True if connected, otherwise False
        """
        self.sock = socket.socket()
        try:
            self.sock.connect((self.server, self.port))
        except ConnectionRefusedError:
            self.sock.close()
            self.sock = None
            return False
        except socket.gaierror:
            # Could not resolve hostname
            self.sock.close()
            self.sock = None
            return False
        else:
            self.sock.settimeout(self.timeout)
            return True

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, msg):
        """
        Send a message to the livesplit server - connect if not already connected.
        If the connection is aborted (ie: if livesplit server has been closed)
        raise a ConnectionAbortedError

        :param msg: bytes message to send (should end with "\r\n")
        :return:
        """
        if not self.sock:
            self.connect()
        try:
            self.sock.send(msg)
        except ConnectionAbortedError:
            self.sock.close()
            self.sock = None
            raise ConnectionAbortedError("The connection has been closed by the host")

    def receive(self):
        """
        Attempt to receive a message from the livesplit server
        raise ConnectionError if the connection has been terminated.

        :return: bytes received from the server
        """
        if not self.sock:
            self.connect()
        try:
            data_received = self.sock.recv(BUFFER_SIZE)
        except socket.timeout:
            raise TimeoutError(
                "No response received from the server within "
                f"the timeout period ({self.timeout}s)"
            )
        except OSError:
            self.sock.close()
            self.sock = None
            raise ConnectionError("The connection has been closed by the host")

        if data_received == b"":
            self.sock.close()
            self.sock = None
            raise ConnectionError("The connection has been closed by the host")

        return data_received
