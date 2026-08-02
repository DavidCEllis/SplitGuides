import socket
from unittest.mock import patch, MagicMock

import pytest

from splitguides.livesplit_client.connection_shared import ConnectionTCP, BUFFER_SIZE


def test_init():
    connection = ConnectionTCP(server="hostname", port=12, timeout=2)
    assert connection.server == "hostname"
    assert connection.port == 12
    assert connection.timeout == 2
    assert connection.sock is None


def test_connect():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        connection = ConnectionTCP(server="host", port=12, timeout=2)
        response = connection.connect()

        mock_socket.assert_called_once()
        mock_sock.connect.assert_called_with(("host", 12))
        mock_sock.settimeout.assert_called_with(2)

        mock_ping.assert_called_once()
        mock_ping.assert_called_with(mock_sock)

        assert response is True

def test_failed_connect():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        mock_sock.connect.side_effect = ConnectionRefusedError("Should be handled")
        connection = ConnectionTCP()

        response = connection.connect()

        assert response is False

def test_connected_to_websocket():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.recv.side_effect = TimeoutError("Timeout on TCP connection to Websocket")

        connection = ConnectionTCP(server="host", port=12, timeout=2)
        response = connection.connect()

        mock_socket.assert_called_once()
        mock_sock.connect.assert_called_with(("host", 12))

        assert response is False

def test_close():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        connection = ConnectionTCP()
        connection.connect()

        connection.close()

        mock_sock.close.assert_called_once()
        assert connection.sock is None

        mock_sock.reset_mock()
        connection.close()
        mock_sock.close.assert_not_called()


def test_send():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        connection = ConnectionTCP()

        connection.connect()

        connection.send(b"test message")

        mock_socket.assert_called_once()
        mock_sock.connect.assert_called_with(("localhost", 16834))
        mock_sock.send.assert_called_with(b"test message\r\n")


def test_send_fail():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.send.side_effect = ConnectionError("Should be caught")

        mock_ping.return_value = True

        connection = ConnectionTCP()

        with pytest.raises(ConnectionError):
            connection.send(b"test message")

        assert connection.sock is None


def test_receive():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        mock_sock.recv.return_value = b"returned data"

        connection = ConnectionTCP()

        connection.connect()

        result = connection.receive()

        assert result == b"returned data"

        mock_sock.recv.assert_called_with(BUFFER_SIZE)


def test_receive_empty():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        mock_sock.recv.return_value = b""

        connection = ConnectionTCP()

        with pytest.raises(ConnectionError):
            connection.receive()

        assert connection.sock is None


def test_receive_timeout():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        mock_sock.recv.side_effect = socket.timeout()

        connection = ConnectionTCP()
        connection.connect()

        with pytest.raises(TimeoutError):
            connection.receive()

        mock_sock.close.assert_not_called()
        assert connection.sock == mock_sock


def test_receive_oserror():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        mock_sock.recv.side_effect = OSError("Confusing windows message.")

        connection = ConnectionTCP()
        connection.connect()

        with pytest.raises(ConnectionError):
            connection.receive()

        mock_sock.close.assert_called_once()
        assert connection.sock is None

def test_receive_server_closed():
    with patch("socket.socket") as mock_socket, patch("splitguides.livesplit_client.connection_shared.ConnectionTCP._ping") as mock_ping:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_ping.return_value = True

        mock_sock.recv.return_value = b""

        connection = ConnectionTCP()
        connection.connect()

        with pytest.raises(ConnectionError):
            connection.receive()

        mock_sock.close.assert_called_once()
        assert connection.sock is None
