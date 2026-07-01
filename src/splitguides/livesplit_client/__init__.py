import re
import socket
import time
import websocket
import sys
if sys.platform == "win32":
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

class ConnectionPipe(ConnectionTypeBase):
    # pipe is Windows and localhost only, localhost setting is not checked
    handle = None

    def connect(self) -> bool:
        if sys.platform != "win32":
            raise NotImplementedError('ConnectionPipe class only on Windows') 
        self.close()
        try:
            self.handle = win32file.CreateFile(
                r'\\.\pipe\livesplit',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res = win32pipe.SetNamedPipeHandleState(self.handle, win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_NOWAIT, None, None)
            if res == 0: # errored
                self.handle = None
                return False
        except pywintypes.error as e:
            self.handle = None
            if e.args[0] != 2: # 2 is unable to find the file -> don't spam the console with that
                print('Pipe error: ' + str(e))
            return False
        return True
    
    def close(self) -> None:
        if sys.platform != "win32":
            raise NotImplementedError('ConnectionPipe class only on Windows') 
        if self.handle:
            win32file.CloseHandle(self.handle)
            self.handle = None
    
    def send(self, msg: bytes) -> None:
        if sys.platform != "win32":
            raise NotImplementedError('ConnectionPipe class only on Windows') 
        try:
            win32file.WriteFile(self.handle, msg + b"\r\n")
        except Exception as e:
            win32file.CloseHandle(self.handle)
            self.handle = None
            raise ConnectionError("Pipe sending error: " + str(e))

    def receive(self) -> bytes:
        if sys.platform != "win32":
            raise NotImplementedError('ConnectionPipe class only on Windows') 
        try:
            # wait a bit for data to arrive, the ReadFile would stall otherwise
            time.sleep(0.05)
            data_received = win32file.ReadFile(self.handle, BUFFER_SIZE)
            # this is returned as tuple, only pass the data onwards
            data_received = data_received[1]
        except Exception as e:
            win32file.CloseHandle(self.handle)
            self.handle = None
            raise ConnectionError("Pipe broken: " + str(e))
        return data_received

CONNECTIONTYPE_PIPE=0
CONNECTIONTYPE_TCP=1
CONNECTIONTYPE_WS=2

STABLE_RETRY=10

class LivesplitConnection(Prefab):
    """
    Livesplit connection model supporting Named Pipe (Windows-only), TCP and Websocket connections
    """
    server: str = "localhost"
    port: int = 16834

    stable_type : int = attribute(default=-1, init=False, repr=False)
    stable_retry : int = attribute(default=0, init=False, repr=False)
    next_attempt_idx : int = attribute(default=0, init=False, repr=False)
    connection_obj : ConnectionTypeBase | None = attribute(default=None, init=False, repr=False)
    list_connection_types : list = attribute(default=[], init=False, repr=False)

    def _get_valid_list(self):
        if sys.platform != "win32":
            self.list_connection_types = [CONNECTIONTYPE_TCP, CONNECTIONTYPE_WS]
            return
        # these hostnames will try the Named Pipe on Windows along with the other types
        loopback_hosts = ["localhost", "127.0.0.1", "::1"]
        if self.server.lower() in loopback_hosts:
            self.list_connection_types = [CONNECTIONTYPE_PIPE, CONNECTIONTYPE_TCP, CONNECTIONTYPE_WS]
        else:
            self.list_connection_types = [CONNECTIONTYPE_TCP, CONNECTIONTYPE_WS]
    
    def is_connected(self) -> bool:
        return (bool)(self.connection_obj)
    
    def get_connection_friendly_name(self) -> str:
        if self.connection_obj:
            if self.stable_type == CONNECTIONTYPE_PIPE:
                status = "Named Pipe"
            elif self.stable_type == CONNECTIONTYPE_TCP:
                status = "TCP"
            elif self.stable_type == CONNECTIONTYPE_WS:
                status = "Websocket"
            else:
                status = ""
        else:
            status = ""
        return status

    def connect(self) -> bool:
        """
        Attempt to connect to the livesplit server
        :return: True if connected, otherwise False
        """
        if len(self.list_connection_types) == 0:
            # post init to fill the valid connections once
            self._get_valid_list()

        self.close()

        if self.stable_type >= 0:
            cur_type : int = self.stable_type
        else:
            cur_type : int = self.list_connection_types[self.next_attempt_idx]
        
        if cur_type == CONNECTIONTYPE_PIPE:
            self.connection_obj = ConnectionPipe()
        elif cur_type == CONNECTIONTYPE_TCP:
            self.connection_obj = ConnectionTCP(self.server, self.port)
        elif cur_type == CONNECTIONTYPE_WS:
            self.connection_obj = ConnectionWS(self.server, self.port)
        else: # out of range, logic error
            raise Exception('logic error')
        
        connection_successful = self.connection_obj.connect()

        if connection_successful:
            if self.stable_type >= 0:
                # restablished after connection drop
                self.stable_retry = 0
            else:
                # connected after searching
                self.stable_type = cur_type
                self.stable_retry = 0
        else:
            self.connection_obj = None
            if self.stable_type >= 0:
                # try to reconnect on that method
                self.stable_retry += 1
                if self.stable_retry >= STABLE_RETRY:
                    # give up on the stable index
                    self.stable_type = -1
                    self.next_attempt_idx = 0
            else:
                # try next method
                self.next_attempt_idx = (self.next_attempt_idx + 1) % len(self.list_connection_types)
        return connection_successful

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
        if not self.is_connected():
            return
        
        self.connection_obj.send(msg)

    def receive(self) -> bytes:
        """
        Attempt to receive a message from the livesplit server
        raise ConnectionError if the connection has been terminated.

        :return: bytes or string received from the server
        """
        if not self.is_connected():
            return b""
        
        return self.connection_obj.receive()

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
        port: int = 16834
) -> LivesplitMessaging:
    return LivesplitMessaging(connection=LivesplitConnection(server, port))
