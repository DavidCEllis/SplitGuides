import re
import sys

from datetime import timedelta
import typing

from ducktools.classbuilder.prefab import Prefab, attribute

from .connection_shared import (
    ConnectionTypeBase,
    ConnectionTCP,
    ConnectionWS
)

CONNECTION_TYPES: tuple[type[ConnectionTypeBase], ...]

if sys.platform == "win32":
    from .connection_windows import ConnectionPipe
    CONNECTION_TYPES = (ConnectionPipe, ConnectionTCP, ConnectionWS)
else:
    CONNECTION_TYPES = (ConnectionTCP, ConnectionWS)

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
    if match is None:
        raise RuntimeError("String time from livesplit did not match expected pattern")

    hours = int(match["hours"]) if match["hours"] else 0
    minutes = int(match["minutes"])
    seconds = int(match["seconds"])
    milliseconds = int(match["centiseconds"]) * 10

    result = timedelta(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
    )

    return result


class LivesplitConnection(Prefab):
    """
    Livesplit connection model supporting Named Pipe (Windows-only), TCP and Websocket connections
    """
    server: str = "localhost"
    port: int = 16834

    # Make it possible to replace the possible connection types for testing, but see the actual type for debugging
    connection_obj: ConnectionTypeBase | None = attribute(default=None, init=False)
    connection_types: tuple[type[ConnectionTypeBase], ...] = attribute(default=CONNECTION_TYPES, repr=False)

    def is_connected(self) -> bool:
        return bool(self.connection_obj)

    def get_connection_friendly_name(self) -> str:
        if self.connection_obj:
            status = self.connection_obj.NAME
        else:
            status = ""
        return status

    def connect(self) -> bool:
        """
        Attempt to connect to the livesplit server
        :return: True if connected, otherwise False
        """
        self.close()

        for connection_type in self.connection_types:
            # Try each connection type in succession, accept the first successful connection type
            connection = connection_type(self.server, self.port)
            connection_success = connection.connect()
            if connection_success:
                self.connection_obj = connection
                break
        else:
            connection_success = False

        return connection_success

    def close(self) -> None:
        if self.connection_obj:
            self.connection_obj.close()
            self.connection_obj = None

    def send(self, msg: bytes) -> None:
        """
        Send a message to the livesplit server - connect if not already connected.
        If the connection is aborted (ie: if livesplit server has been closed)
        raise a ConnectionAbortedError

        :param msg: bytes message to send
        :return:
        """
        if self.connection_obj:
            self.connection_obj.send(msg)

    def receive(self) -> bytes:
        """
        Attempt to receive a message from the livesplit server
        raise ConnectionError if the connection has been terminated.

        :return: bytes or string received from the server
        """
        if self.connection_obj:
            return self.connection_obj.receive()
        else:
            return b""


class LivesplitMessaging(Prefab):
    connection: LivesplitConnection

    def connect(self) -> bool:
        return self.connection.connect()

    def close(self) -> None:
        self.connection.close()

    def send(self, message: str) -> None:
        m = message.encode("UTF8")
        self.connection.send(m)

    @typing.overload
    def receive(self, datatype: typing.Literal["time"]) -> timedelta: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["int"]) -> int: ...
    @typing.overload
    def receive(self, datatype: typing.Literal["text"] = "text") -> str: ...

    def receive(self, datatype="text"):
        result = self.connection.receive()
        result = result.decode("UTF8").strip()

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
            self.send("getdelta")

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
        port: int = 16834
) -> LivesplitMessaging:
    return LivesplitMessaging(connection=LivesplitConnection(server, port))
