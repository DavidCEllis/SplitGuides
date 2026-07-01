import abc
import socket
import typing
import websocket

from ducktools.classbuilder.prefab import prefab, attribute


BUFFER_SIZE = 4096


class ConnectionTypeBase(abc.ABC):
    NAME: typing.ClassVar[str] = ""

    @abc.abstractmethod
    def connect(self) -> bool:
        ...

    @abc.abstractmethod
    def close(self) -> None:
        ...

    def closed_by_host(self) -> typing.NoReturn:
        self.close()
        raise ConnectionError("The connection has been closed by the host")

    @abc.abstractmethod
    def send(self, msg: bytes) -> None:
        ...

    @abc.abstractmethod
    def receive(self) -> bytes:
        ...


@prefab
class ConnectionTCP(ConnectionTypeBase):
    NAME: typing.ClassVar[str] = "TCP"

    server: str = "localhost"
    port: int = 16834
    timeout: int = 1
    sock: socket.socket | None = attribute(default=None, init=False, repr=False)

    def connect(self) -> bool:
        self.close()
        self.sock = socket.socket()
        try:
            self.sock.connect((self.server, self.port))
        except (ConnectionRefusedError, socket.gaierror):
            # gaierror is raised if it could not resolve hostname
            self.close()
            return False

        self.sock.settimeout(self.timeout)
        if self._ping(self.sock):
            return True
        else:
            self.close()
            return False

    @staticmethod
    def _ping(sock) -> bool:
        try:
            sock.send(b"ping\r\n")
            ping_resp = sock.recv(BUFFER_SIZE).decode("UTF-8").strip("\r\n")
        except (TimeoutError, ConnectionError):
            return False
        else:
            return ping_resp == "pong"

    def close(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, msg: bytes) -> None:
        if not self.sock:
            raise ConnectionError("The connection has not yet been established")

        try:
            self.sock.send(msg + b"\r\n")
        except ConnectionAbortedError:
            self.closed_by_host()

    def receive(self) -> bytes:
        if not self.sock:
            raise ConnectionError("The connection has not yet been established")

        data_received = b""
        try:
            data_received = self.sock.recv(BUFFER_SIZE)
        except socket.timeout:
            raise TimeoutError(
                "No response received from the server within "
                f"the timeout period ({self.timeout}s)"
            )
        except OSError:
            self.closed_by_host()

        if data_received == b"":
            self.closed_by_host()

        return data_received

@prefab
class ConnectionWS(ConnectionTypeBase):
    NAME: typing.ClassVar[str] = "WebSocket"

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
        except Exception:
            # TODO: More precise exception here - like for ConnectionTCP
            self.close()
            return False

    def close(self) -> None:
        if self.ws:
            self.ws.close()
            self.ws = None

    def send(self, msg: bytes) -> None:
        if not self.ws:
            raise ConnectionError("The connection has not yet been established")
        try:
            self.ws.send(msg) # no CRLF on Websocket
        except Exception:
            # TODO: More precise exception here
            self.closed_by_host()

    def receive(self) -> bytes:
        if not self.ws:
            raise ConnectionError("The connection has not yet been established")

        try:
            data_received = self.ws.recv()
        except Exception:
            # TODO: More precise exception here
            self.closed_by_host()

        if isinstance(data_received, str):
            # should always be string, encode to bytes for unified handling
            data_received = data_received.encode("UTF8")

        if data_received == b"":
            self.closed_by_host()

        return data_received
