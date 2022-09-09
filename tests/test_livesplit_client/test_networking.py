import socket
from unittest.mock import patch, MagicMock

import pytest

from splitguides.livesplit_client.networking import LivesplitConnection, BUFFER_SIZE


def test_init():
    connection = LivesplitConnection(server="hostname", port=12, timeout=2)
    assert connection.server == "hostname"
    assert connection.port == 12
    assert connection.timeout == 2
    assert connection.sock is None


def test_connect():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        connection = LivesplitConnection(server="host", port=12, timeout=2)
        response = connection.connect()

        mock_socket.assert_called_once()
        mock_sock.connect.assert_called_with(("host", 12))
        mock_sock.settimeout.assert_called_with(2)

        assert response is True


def test_failed_connect():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_sock.connect.side_effect = ConnectionRefusedError("Should be handled")
        connection = LivesplitConnection()

        response = connection.connect()

        assert response is False


def test_close():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        connection = LivesplitConnection()
        connection.connect()

        connection.close()

        mock_sock.close.assert_called_once()
        assert connection.sock is None

        mock_sock.reset_mock()
        connection.close()
        mock_sock.close.assert_not_called()


@pytest.mark.parametrize("connect_first", [True, False])
def test_send(connect_first):
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        connection = LivesplitConnection()

        if connect_first:
            connection.connect()

        connection.send(b"test message")

        mock_socket.assert_called_once()
        mock_sock.connect.assert_called_with(("localhost", 16834))
        mock_sock.send.assert_called_with(b"test message")


def test_send_fail():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.send.side_effect = ConnectionAbortedError("Should be caught")

        connection = LivesplitConnection()

        with pytest.raises(ConnectionAbortedError):
            connection.send(b"test message")

        mock_sock.send.assert_called_with(b"test message")

        mock_sock.close.assert_called_once()
        assert connection.sock is None


@pytest.mark.parametrize("connect_first", [True, False])
def test_receive(connect_first):
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_sock.recv.return_value = b"returned data"

        connection = LivesplitConnection()

        if connect_first:
            connection.connect()

        result = connection.receive()

        assert result == b"returned data"

        mock_sock.recv.assert_called_with(BUFFER_SIZE)


def test_receive_empty():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_sock.recv.return_value = b""

        connection = LivesplitConnection()

        with pytest.raises(ConnectionError):
            connection.receive()

        mock_sock.close.assert_called_once()
        assert connection.sock is None


def test_receive_timeout():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_sock.recv.side_effect = socket.timeout()

        connection = LivesplitConnection()

        with pytest.raises(TimeoutError):
            connection.receive()

        mock_sock.close.assert_not_called()
        assert connection.sock == mock_sock


def test_receive_oserror():
    with patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        mock_sock.recv.side_effect = OSError("Confusing windows message.")

        connection = LivesplitConnection()

        with pytest.raises(ConnectionError):
            connection.receive()

        mock_sock.close.assert_called_once()
        assert connection.sock is None
