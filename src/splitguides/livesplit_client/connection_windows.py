import sys

if sys.platform != "win32":
    raise ImportError("'connection_windows.py' is not supported on platforms other than Windows")

import time
import typing

import pywintypes
import win32file
import win32pipe


from ducktools.classbuilder.prefab import prefab, attribute

from .connection_shared import BUFFER_SIZE, ConnectionTypeBase

# These all refer to the local machine and are used to decide if named pipes should be checked
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
LIVESPLIT_PIPE = r'\\.\pipe\livesplit'

@prefab
class ConnectionPipe(ConnectionTypeBase):
    NAME: typing.ClassVar[str] = "Named Pipe"

    # Not sure if there's a good type for `handle`
    handle: typing.Any | None = attribute(default=None, init=False, repr=False)

    def connect(self) -> bool:
        self.close()

        if self.server not in LOOPBACK_HOSTS:
            return False

        try:
            self.handle = win32file.CreateFile(
                LIVESPLIT_PIPE,
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
        if self.handle:
            win32file.CloseHandle(self.handle)
            self.handle = None

    def send(self, msg: bytes) -> None:
        if not self.handle:
            raise ConnectionError("The connection has not yet been established")

        try:
            win32file.WriteFile(self.handle, msg + b"\r\n")
        except Exception as e:
            win32file.CloseHandle(self.handle)
            self.handle = None
            raise ConnectionError("Pipe sending error: " + str(e))

    def receive(self) -> bytes:
        if not self.handle:
            raise ConnectionError("The connection has not yet been established")

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

        return data_received.encode("UTF8")
