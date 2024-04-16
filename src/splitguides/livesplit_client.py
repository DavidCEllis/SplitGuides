import re
import socket
from datetime import timedelta
import typing

from ducktools.classbuilder.prefab import prefab, attribute, SlotFields

BUFFER_SIZE = 4096


pattern = re.compile(
    r"^(?:(?P<hours>\d*):)?(?P<minutes>\d{1,2}):(?P<seconds>\d{2}).(?P<centiseconds>\d*)"
)


def parse_time(time_str: str) -> timedelta:
    """
    Takes the time string from livesplit and converts to a timedelta

    :param time_str:
    :return:
    """
    match = pattern.match(time_str)
    hours = int(match["hours"]) if match["hours"] else 0
    minutes = int(match["minutes"])
    seconds = int(match["seconds"])
    milliseconds = int(match["centiseconds"]) * 10

    result = timedelta(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
    )

    return result


@prefab
class LivesplitConnection:
    """
    Socket based livesplit connection model
    """
    __slots__ = SlotFields(
        server=attribute(default="localhost"),
        port=attribute(default=16834),
        timeout=attribute(default=1),
        sock=attribute(default=None, init=False, repr=False),
    )
    server: str
    port: int
    timeout: int
    sock: socket.socket | None

    def connect(self) -> bool:
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

    def close(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, msg: bytes) -> None:
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

    def receive(self) -> bytes:
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


_receive_types = typing.Literal["text", "time", "int"]


@prefab
class LivesplitMessaging:
    __slots__ = SlotFields(connection=attribute())
    connection: LivesplitConnection

    def connect(self) -> bool:
        return self.connection.connect()

    def close(self) -> None:
        self.connection.close()

    def send(self, message) -> None:
        m = message.encode("UTF8")
        self.connection.send(m + b"\r\n")

    @typing.overload
    def receive(self, datatype: typing.Literal["time"]) -> timedelta: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["int"]) -> int: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["text"] = "text") -> str: ...

    def receive(self, datatype="text"):
        result = self.connection.receive()
        result = result.strip().decode("UTF8")
        if datatype == "time":
            result = parse_time(result)
        elif datatype == "int":
            return int(result)

        return result

    def start_timer(self) -> None:
        """
        Start the timer
        """
        self.send("starttimer")

    def start_or_split(self) -> None:
        """
        Start the timer or split a running timer
        """
        self.send("startorsplit")

    def split(self) -> None:
        """
        Split
        """
        self.send("split")

    def unsplit(self) -> None:
        """
        Undo the previous split
        """
        self.send("unsplit")

    def skip_split(self) -> None:
        """
        Skip the current split
        """
        self.send("skipsplit")

    def pause(self) -> None:
        """
        Pause the timer
        """
        self.send("pause")

    def resume(self) -> None:
        """
        Resume a paused timer
        """
        self.send("resume")

    def reset(self) -> None:
        """
        Reset the timer
        """
        self.send("reset")

    def init_game_time(self) -> None:
        """
        Activate the game timer
        """
        self.send("initgametime")

    def set_game_time(self, t: str) -> None:
        """
        Set the game timer
        :param t:
        :return:
        """
        self.send(f"setgametime {t}")

    def set_loading_times(self, t: str) -> None:
        """

        :param t:
        """
        self.send(f"setloadingtimes {t}")

    def pause_game_time(self) -> None:
        """
        Pause the game timer
        """
        self.send("pausegametime")

    def unpause_game_time(self) -> None:
        """
        Unpause the game timer
        """
        self.send("unpausegametime")

    def set_comparison(self, comparison) -> None:
        """
        Change the comparison method

        :param comparison: Time to compare against eg 'Personal Best' or 'Best Segments'
        """
        self.send(f"setcomparison {comparison}")

    def get_delta(self, comparison=None) -> str:
        if comparison:
            self.send(f"getdelta {comparison}")
        else:
            self.send(f"getdelta")

        return self.receive()

    def get_last_split_time(self) -> timedelta:
        self.send("getlastsplittime")
        return self.receive("time")

    def get_comparison_split_time(self) -> timedelta:
        self.send("getcomparisonsplittime")
        return self.receive("time")

    def get_current_time(self) -> timedelta:
        self.send("getcurrenttime")
        return self.receive("time")

    def get_final_time(self, comparison=None) -> timedelta:
        if comparison:
            self.send(f"getfinaltime {comparison}")
        else:
            self.send("getfinaltime")
        return self.receive("time")

    def get_predicted_time(self, comparison) -> timedelta:
        self.send(f"getpredictedtime {comparison}")
        return self.receive("time")

    def get_best_possible_time(self) -> timedelta:
        self.send("getbestpossibletime")
        return self.receive("time")

    def get_split_index(self) -> int:
        self.send("getsplitindex")
        return self.receive("int")

    def get_current_split_name(self) -> str:
        self.send("getcurrentsplitname")
        return self.receive()

    def get_previous_split_name(self) -> str:
        self.send("getprevioussplitname")
        return self.receive()

    def get_current_timer_phase(self) -> str:
        self.send("getcurrenttimerphase")
        return self.receive()


def get_client(
        server: str = "localhost",
        port: int = 16834,
        timeout: int = 1
) -> LivesplitMessaging:
    return LivesplitMessaging(connection=LivesplitConnection(server, port, timeout))
