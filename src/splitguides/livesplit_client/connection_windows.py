import sys

if sys.platform != "win32":
    raise ImportError("'connection_windows.py' is not supported on platforms other than Windows")

import time

import pywintypes
import win32file
import win32pipe


from .connection_shared import ConnectionTypeBase


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
