import re
from datetime import timedelta

pattern = re.compile(
    r"^(?P<hours>\d*):?(?P<minutes>\d{1,2}):(?P<seconds>\d{2}).(?P<centiseconds>\d*)"
)


def parse_time(time_str):
    """
    Takes the time string from livesplit and converts to a timedelta

    :param time_str:
    :return:
    """
    match = pattern.match(time_str)
    hours = int(match['hours']) if match['hours'] else 0
    minutes = int(match['minutes'])
    seconds = int(match['seconds'])
    milliseconds = int(match['centiseconds']) * 10

    result = timedelta(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
    )

    return result
