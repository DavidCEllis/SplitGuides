import re
import socket
import time
import websocket
import win32pipe, win32file, pywintypes
from datetime import timedelta
import typing

from ducktools.classbuilder.prefab import Prefab, attribute

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
    Socket based livesplit connection model
    """
    server: str = attribute(default="localhost", init=True)
    port: int = attribute(default=16834, init=True)
    connectionType: int = attribute(default=1, init=True) # 0: named pipe, 1: TCP, 2: websocket
    timeout: int = attribute(default=1, init=True)
    sockTCP: socket.socket | None = attribute(default=None, init=False, repr=False)
    sockWS: websocket.WebSocketApp | None = attribute(default=None, init=False, repr=False)
    handlePipe = attribute(default=None, init=False, repr=False)

    def connect(self) -> bool:
        """
        Attempt to connect to the livesplit server
        :return: True if connected, otherwise False
        """
        self.close()
        
        if self.connectionType == 1:
            self.sockTCP = socket.socket()
            try:
                self.sockTCP.connect((self.server, self.port))
                self.sockTCP.settimeout(self.timeout)
                self.sockTCP.send(b"ping\r\n")
                ping_resp = self.sockTCP.recv(BUFFER_SIZE).decode("UTF-8").strip("\r\n")
                return (ping_resp == "pong")
            except ConnectionRefusedError:
                self.sockTCP.close()
                self.sockTCP = None
                return False
            except socket.gaierror:
                # Could not resolve hostname
                self.sockTCP.close()
                self.sockTCP = None
                return False
        elif self.connectionType == 2:
            self.sockWS = websocket.WebSocket()
            try:
                self.sockWS.connect(f"ws://{self.server}:{self.port}/livesplit", origin="SplitGuides", timeout=10)
            except Exception as e:
                self.sockWS.close()
                self.sockWS = None
                return False
            else:
                return True
        else:
            try:
                self.handlePipe = win32file.CreateFile(
                    r'\\.\pipe\livesplit',
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                res = win32pipe.SetNamedPipeHandleState(self.handlePipe, win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_NOWAIT, None, None)
                if res == 0: # errored
                    self.handlePipe = None
                    return False
            except pywintypes.error as e:
                self.handlePipe = None
                print('Pipe error: ' + e.args[2])
                return False
            else:
                return True

    def ensureConnected(self) -> bool:
        if self.connectionType == 1:
            if not self.sockTCP:
                return self.connect()
            else:
                return True
        elif self.connectionType == 2:
            if not self.sockWS:
                return self.connect()
            else:
                return True
        else:
            if not self.handlePipe:
                return self.connect()
            else:
                return True

    def close(self) -> None:
        if self.sockTCP:
            self.sockTCP.close()
            self.sockTCP = None
        if self.sockWS:
            self.sockWS.close()
            self.sockWS = None
        if self.handlePipe:
            win32file.CloseHandle(self.handlePipe)
            self.handlePipe = None

    def send(self, msg: bytes) -> None:
        """
        Send a message to the livesplit server - connect if not already connected.
        If the connection is aborted (ie: if livesplit server has been closed)
        raise a ConnectionAbortedError

        :param msg: bytes message to send
        :return:
        """
        if not self.ensureConnected():
            return
        
        if self.connectionType == 1:
            try:
                self.sockTCP.send(msg + b"\r\n")
            except:
                self.sockTCP.close()
                self.sockTCP = None
                raise ConnectionAbortedError("The connection has been closed by the host")
        elif self.connectionType == 2:
            try:
                self.sockWS.send(msg) #no CRLF on WS
            except Exception as e:
                self.sockWS.close()
                self.sockWS = None
                raise ConnectionAbortedError("The connection has been closed by the host")
        else:
            try:
                win32file.WriteFile(self.handlePipe, msg + b"\r\n")
            except Exception as e:
                print("pipe sending error: " + str(e))
                win32file.CloseHandle(self.handlePipe)
                self.handlePipe = None
                raise ConnectionAbortedError("Pipe broken")

    def receive(self) -> typing.Union[bytes, str]:
        """
        Attempt to receive a message from the livesplit server
        raise ConnectionError if the connection has been terminated.

        :return: bytes or string received from the server
        """
        if not self.ensureConnected():
            return b""
        
        data_received = b""
        if self.connectionType == 1:
            try:
                data_received = self.sockTCP.recv(BUFFER_SIZE)
            except socket.timeout:
                raise TimeoutError(
                    "No response received from the server within "
                    f"the timeout period ({self.timeout}s)"
                )
            except OSError:
                self.sockTCP.close()
                self.sockTCP = None
                raise ConnectionError("The connection has been closed by the host")

            if data_received == b"":
                self.sockTCP.close()
                self.sockTCP = None
                raise ConnectionError("The connection has been closed by the host")

            return data_received
        elif self.connectionType == 2:
            try:
                data_received : bytes = self.sockWS.recv()
            except Exception as e:
                self.sockWS.close()
                self.sockWS = None
                raise ConnectionAbortedError("The connection has been closed by the host")
            return data_received
        else:
            time.sleep(0.05)
            try:
                data_received = win32file.ReadFile(self.handlePipe, BUFFER_SIZE)
                # this is returned as tuple, only pass the data onwards
                data_received = data_received[1]
            except Exception as e:
                win32file.CloseHandle(self.handlePipe)
                self.handlePipe = None
                raise ConnectionAbortedError("Pipe broken")
            return data_received
        
        return b""

class LivesplitMessaging(Prefab):
    connection: LivesplitConnection

    def connect(self) -> bool:
        return self.connection.connect()

    def close(self) -> None:
        self.connection.close()

    def send(self, message) -> None:
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
        if isinstance(result, bytes):
            result = result.decode("UTF8").strip()
        else: #str
            result = result.strip()

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
        connectionType: int = 1,
        timeout: int = 1
) -> LivesplitMessaging:
    return LivesplitMessaging(connection=LivesplitConnection(server, port, connectionType, timeout))
