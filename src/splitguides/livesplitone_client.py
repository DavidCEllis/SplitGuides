import json
from websockets.sync.client import connect, ClientConnection
from datetime import timedelta
import typing

from ducktools.classbuilder.prefab import Prefab, attribute

from .livesplit_client import BUFFER_SIZE, parse_time

class LivesplitoneConnection(Prefab):
    """
    Socket based livesplit one connection model
    """
    timer: str = "LiveSplitOne"
    server: str = "localhost"
    port: int = 16834
    timeout: int = 1
    sock: ClientConnection | None = attribute(default=None, init=False, repr=False)

    def connect(self) -> bool:
        """
        Attempt to connect to the livesplit one server
        :return: True if connected, otherwise False
        """
        self.sock = connect(f"ws://{self.server}:{self.port}")
        return True

    def close(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, msg: bytes) -> None:
        """
        Send a message to the livesplit one server - connect if not already connected.
        If the connection is aborted (ie: if livesplit one server has been closed)
        raise a ConnectionAbortedError

        :param msg: bytes message to send (should end with "\r\n")
        :return:
        """
        if not self.sock:
            self.connect()
        
        if self.sock:  # Check again in case connection failed
            try:
                self.sock.send(msg)
            except ConnectionAbortedError:
                self.sock.close()
                self.sock = None
                raise ConnectionAbortedError("The connection has been closed by the host")

    def receive(self) -> bytes:
        """
        Attempt to receive a message from the livesplit one server
        raise ConnectionError if the connection has been terminated.

        :return: bytes received from the server
        """
        if not self.sock:
            self.connect()
        
        if self.sock:
            try:
                data_received = self.sock.recv(BUFFER_SIZE, False)
            except OSError:
                self.sock.close()
                self.sock = None
                raise ConnectionError("The connection has been closed by the host")

            if data_received == b"":
                self.sock.close()
                self.sock = None
                raise ConnectionError("The connection has been closed by the host")

            return data_received
        
        return b""


class LivesplitoneMessaging(Prefab):
    connection: LivesplitoneConnection

    def connect(self) -> bool:
        return self.connection.connect()

    def close(self) -> None:
        self.connection.close()

    def send(self, message) -> None:
        m = json.dumps(message).encode("UTF8")
        self.connection.send(m + b"\r\n")

    @typing.overload
    def receive(self, datatype: typing.Literal["time"]) -> timedelta: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["int"]) -> int: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["state"]) -> dict: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["text"] = "text") -> str: ...

    def receive(self, datatype="text"):
        result = self.connection.receive()
        result = result.strip().decode("UTF8")
        result = json.loads(result)["success"]
        if datatype == "time":
            result = parse_time(result["string"])
        elif datatype == "int":
            return int(result["string"])
        elif datatype == "state":
            return result

        return result

    def start_timer(self) -> None:
        """
        Start the timer
        """
        self.send({ "command": "start" })

    def start_or_split(self) -> None:
        """
        Start the timer or split a running timer
        """
        self.send({ "command": "splitOrStart" })

    def split(self) -> None:
        """
        Split
        """
        self.send({ "command": "split" })

    def unsplit(self) -> None:
        """
        Undo the previous split
        """
        self.send({ "command": "undoSplit" })

    def skip_split(self) -> None:
        """
        Skip the current split
        """
        self.send({ "command": "skipSplit" })

    def pause(self) -> None:
        """
        Pause the timer
        """
        self.send({ "command": "pause" })

    def resume(self) -> None:
        """
        Resume a paused timer
        """
        self.send({ "command": "resume" })

    def reset(self) -> None:
        """
        Reset the timer
        """
        self.send({ "command": "reset" })

    def init_game_time(self) -> None:
        """
        Activate the game timer
        """
        self.send({ "command": "initializeGameTime" })

    def set_game_time(self, t: str) -> None:
        """
        Set the game timer
        :param t:
        :return:
        """
        self.send({ "command": "setGameTime", "time": t })

    def set_loading_times(self, t: str) -> None:
        """

        :param t:
        """
        self.send({ "command": "setLoadingTimes", "time": t })

    def pause_game_time(self) -> None:
        """
        Pause the game timer
        """
        self.send({ "command": "pauseGameTime" })

    def unpause_game_time(self) -> None:
        """
        Unpause the game timer
        """
        self.send({ "command": "resumeGameTime" })

    def set_comparison(self, comparison) -> None:
        """
        Change the comparison method

        :param comparison: Time to compare against eg 'Personal Best' or 'Best Segments'
        """
        self.send({ "command": "setCurrentComparison", "comparison": comparison })

    def get_last_split_time(self) -> timedelta:
        self.send({ "command": "getCurrentRunSplitTime" })
        return self.receive("time")

    def get_comparison_split_time(self) -> timedelta:
        self.send({ "command": "getComparisonTime" })
        return self.receive("time")

    def get_current_time(self) -> timedelta:
        self.send({ "command": "getCurrentTime" })
        return self.receive("time")

    def get_split_index(self) -> int:
        self.send({ "command": "getCurrentState" })
        s = self.receive("state")
        match s["state"]:
            case "Running" | "Paused":
                return s["index"]
            case _:
                return -1

    def get_current_split_name(self) -> str:
        self.send({ "command": "getSegmentName" })
        return self.receive()

    def get_previous_split_name(self) -> str:
        self.send({ "command": "getSegmentName",  "index": -1, "relative": True })
        return self.receive()

    def get_current_timer_phase(self) -> str:
        self.send({ "command": "getCurrentState" })
        return self.receive("state")["state"]


def get_livesplitone_client(
        server: str = "localhost",
        port: int = 16834,
        timeout: int = 1
) -> LivesplitoneMessaging:
    return LivesplitoneMessaging(connection=LivesplitoneConnection(server, port, timeout))
