import socket
import websocket

from ducktools.classbuilder.prefab import Prefab, attribute


BUFFER_SIZE = 4096


class ConnectionTypeBase:
    def connect(self) -> bool:
        return False

    def close(self) -> None:
        return

    def send(self, msg: bytes) -> None:
        return

    def receive(self) -> bytes:
        return b""

class ConnectionTCP(ConnectionTypeBase, Prefab):
    server: str = "localhost"
    port: int = 16834
    timeout: int = 1
    sock: socket.socket | None = attribute(default=None, init=False, repr=False)

    def connect(self) -> bool:
        self.close()
        self.sock = socket.socket()
        try:
            self.sock.connect((self.server, self.port))
            self.sock.settimeout(self.timeout)
            # We need to ping the connection to make sure we are connected to a TCP server,
            # the Websocket server also allows this socket connection
            self.sock.send(b"ping\r\n")
            ping_resp = self.sock.recv(BUFFER_SIZE).decode("UTF-8").strip("\r\n")
            return (ping_resp == "pong")
        except TimeoutError:
            self.sock.close()
            self.sock = None
            return False
        except ConnectionRefusedError:
            self.sock.close()
            self.sock = None
            return False
        except socket.gaierror:
            # Could not resolve hostname
            self.sock.close()
            self.sock = None
            return False

    def close(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, msg: bytes) -> None:
        try:
            self.sock.send(msg + b"\r\n")
        except:
            self.sock.close()
            self.sock = None
            raise ConnectionError("The connection has been closed by the host")

    def receive(self) -> bytes:
        data_received = b""
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

class ConnectionWS(ConnectionTypeBase, Prefab):
    server: str = "localhost"
    port: int = 16834
    timeout: int = 4  # 1 second not enough to establish a connection
    ws: websocket.WebSocket | None = attribute(default=None, init=False, repr=False)

    def connect(self) -> bool:
        self.close()
        self.ws = websocket.WebSocket()
        try:
            self.ws.connect(f"ws://{self.server}:{self.port}/livesplit", origin="SplitGuides", timeout=self.timeout)
            return True
        except Exception as e:
            self.ws.close()
            self.ws = None
            return False

    def close(self) -> None:
        if self.ws:
            self.ws.close()
            self.ws = None

    def send(self, msg: bytes) -> None:
        try:
            self.ws.send(msg) # no CRLF on Websocket
        except Exception as e:
            self.ws.close()
            self.ws = None
            raise ConnectionError("The connection has been closed by the host")

    def receive(self) -> bytes:
        try:
            data_received : bytes = self.ws.recv()
        except Exception as e:
            self.ws.close()
            self.ws = None
            raise ConnectionError("The connection has been closed by the host")
        if isinstance(data_received, str):
            # should always be string, encode to bytes for unified handling
            data_received = data_received.encode("UTF8")
        if data_received == b"":
            self.ws.close()
            self.ws = None
            raise ConnectionError("The connection has been closed by the host")
        return data_received
