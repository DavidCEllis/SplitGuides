from datetime import timedelta
from unittest.mock import MagicMock, call

import pytest

from splitguides.livesplit_client.messaging import LivesplitMessaging, parse_time

times = [
    ("15:32.34", timedelta(minutes=15, seconds=32, milliseconds=340)),
    ("1:10:46.91", timedelta(hours=1, minutes=10, seconds=46, milliseconds=910)),
    ("0:42.12", timedelta(seconds=42, milliseconds=120)),
    ("0:00.02", timedelta(milliseconds=20)),
]


@pytest.mark.parametrize("time_str, expected", times)
def test_parse_time(time_str, expected):
    assert parse_time(time_str) == expected


def test_connection():
    """
    Test the messager correctly calls connect and close on the connection
    """
    fake_connection = MagicMock()

    messager = LivesplitMessaging(fake_connection)

    messager.connect()
    fake_connection.connect.assert_called()

    messager.close()
    fake_connection.close.assert_called()


def test_send():
    """
    Test the send command itself
    """
    fake_connection = MagicMock()
    messager = LivesplitMessaging(fake_connection)

    messager.send("Test message")
    fake_connection.send.assert_called_with(b"Test message\r\n")


def test_send_only_messages():
    """
    test all of the message sending commands
    """
    fake_connection = MagicMock()
    messager = LivesplitMessaging(fake_connection)

    expected = [
        call(b"starttimer\r\n"),
        call(b"startorsplit\r\n"),
        call(b"split\r\n"),
        call(b"unsplit\r\n"),
        call(b"skipsplit\r\n"),
        call(b"pause\r\n"),
        call(b"resume\r\n"),
        call(b"reset\r\n"),
        call(b"initgametime\r\n"),
        call(b"setgametime 2\r\n"),
        call(b"setloadingtimes 12\r\n"),
        call(b"pausegametime\r\n"),
        call(b"unpausegametime\r\n"),
        call(b"setcomparison Personal Best\r\n"),
    ]

    messager.start_timer()
    messager.start_or_split()
    messager.split()
    messager.unsplit()
    messager.skip_split()
    messager.pause()
    messager.resume()
    messager.reset()
    messager.init_game_time()
    messager.set_game_time(2)
    messager.set_loading_times(12)
    messager.pause_game_time()
    messager.unpause_game_time()
    messager.set_comparison("Personal Best")

    fake_connection.send.assert_has_calls(expected)


def test_receive_text():
    fake_connection = MagicMock()
    fake_connection.receive.return_value = b"Response String\r\n"

    messager = LivesplitMessaging(fake_connection)
    response = messager.receive(datatype="text")

    assert response == "Response String"


def test_receive_time():
    fake_connection = MagicMock()
    fake_connection.receive.return_value = b"1:10:46.91\r\n"

    messager = LivesplitMessaging(fake_connection)
    response = messager.receive(datatype="time")

    assert response == timedelta(hours=1, minutes=10, seconds=46, milliseconds=910)


def test_receive_int():
    fake_connection = MagicMock()
    fake_connection.receive.return_value = b"12\r\n"

    messager = LivesplitMessaging(fake_connection)
    response = messager.receive(datatype="int")

    assert response == 12


def test_get_delta():
    fake_connection = MagicMock()

    messager = LivesplitMessaging(fake_connection)

    fake_connection.receive.return_value = b"+2\r\n"
    delta = messager.get_delta()

    fake_connection.send.assert_called_with(b"getdelta\r\n")
    fake_connection.receive.assert_called_once()
    assert delta == "+2"

    fake_connection.reset_mock()

    fake_connection.receive.return_value = b"-12\r\n"
    delta = messager.get_delta("Personal Best")

    fake_connection.send.assert_called_with(b"getdelta Personal Best\r\n")
    fake_connection.receive.assert_called_once()
    assert delta == "-12"


@pytest.mark.parametrize(
    "funcname, message",
    [
        ("get_last_split_time", b"getlastsplittime\r\n"),
        ("get_comparison_split_time", b"getcomparisonsplittime\r\n"),
        ("get_current_time", b"getcurrenttime\r\n"),
        ("get_best_possible_time", b"getbestpossibletime\r\n"),
        ("get_final_time", b"getfinaltime\r\n"),
    ],
)
def test_get_times(funcname, message):
    fake_connection = MagicMock()
    messager = LivesplitMessaging(fake_connection)

    fake_connection.receive.return_value = b"1:10:46.91\r\n"
    expected = timedelta(hours=1, minutes=10, seconds=46, milliseconds=910)

    result = getattr(messager, funcname)()
    assert result == expected

    fake_connection.send.assert_called_with(message)
    fake_connection.receive.assert_called_once()


@pytest.mark.parametrize(
    "funcname, message",
    [
        ("get_final_time", b"getfinaltime Personal Best\r\n"),
        ("get_predicted_time", b"getpredictedtime Personal Best\r\n"),
    ],
)
def test_get_times_pb(funcname, message):
    fake_connection = MagicMock()
    messager = LivesplitMessaging(fake_connection)

    fake_connection.receive.return_value = b"1:10:46.91\r\n"
    expected = timedelta(hours=1, minutes=10, seconds=46, milliseconds=910)

    result = getattr(messager, funcname)("Personal Best")
    assert result == expected

    fake_connection.send.assert_called_with(message)
    fake_connection.receive.assert_called_once()


def test_get_split_index():
    fake_connection = MagicMock()
    messager = LivesplitMessaging(fake_connection)

    fake_connection.receive.return_value = b"2\r\n"
    result = messager.get_split_index()

    assert result == 2
    fake_connection.send.assert_called_with(b"getsplitindex\r\n")
    fake_connection.receive.assert_called_once()


@pytest.mark.parametrize(
    "funcname, message",
    [
        ("get_current_split_name", b"getcurrentsplitname\r\n"),
        ("get_previous_split_name", b"getprevioussplitname\r\n"),
        ("get_current_timer_phase", b"getcurrenttimerphase\r\n"),
    ],
)
def test_get_names(funcname, message):
    fake_connection = MagicMock()
    messager = LivesplitMessaging(fake_connection)

    fake_connection.receive.return_value = b"Asylum Demon\r\n"
    expected = "Asylum Demon"

    result = getattr(messager, funcname)()
    assert result == expected

    fake_connection.send.assert_called_with(message)
    fake_connection.receive.assert_called_once()
