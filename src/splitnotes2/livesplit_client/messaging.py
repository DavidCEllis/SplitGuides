"""
Handle livesplit
"""
import re
from datetime import timedelta


class LivesplitMessaging:
    def __init__(self, connection):
        self.connection = connection

    def connect(self):
        return self.connection.connect()

    def close(self):
        self.connection.close()

    def send(self, message):
        m = message.encode('UTF8')
        self.connection.send(m + b'\r\n')

    def receive(self, datatype="text"):
        result = self.connection.receive()
        result = result.strip().decode('UTF8')
        if datatype == "time":
            result = parse_time(result)
        elif datatype == "int":
            return int(result)

        return result

    def start_timer(self):
        """
        Start the timer
        """
        self.send("starttimer")

    def start_or_split(self):
        """
        Start the timer or split a running timer
        """
        self.send("startorsplit")

    def split(self):
        """
        Split
        """
        self.send("split")

    def unsplit(self):
        """
        Undo the previous split
        """
        self.send("unsplit")

    def skip_split(self):
        """
        Skip the current split
        """
        self.send("skipsplit")

    def pause(self):
        """
        Pause the timer
        """
        self.send("pause")

    def resume(self):
        """
        Resume a paused timer
        """
        self.send("resume")

    def reset(self):
        """
        Reset the timer
        """
        self.send("reset")

    def init_game_time(self):
        """
        Activate the game timer
        """
        self.send("initgametime")

    def set_game_time(self, t):
        """
        Set the game timer
        :param t:
        :return:
        """
        self.send(f"setgametime {t}")

    def set_loading_times(self, t):
        """

        :param t:
        """
        self.send(f"setloadingtimes {t}")

    def pause_game_time(self):
        """
        Pause the game timer
        """
        self.send("pausegametime")

    def unpause_game_time(self):
        """
        Unpause the game timer
        """
        self.send("unpausegametime")

    def set_comparison(self, comparison):
        """
        Change the comparison method

        :param comparison: Time to compare against eg 'Personal Best' or 'Best Segments'
        """
        self.send(f"setcomparison {comparison}")

    def get_delta(self, comparison=None):
        if comparison:
            self.send(f"getdelta {comparison}")
        else:
            self.send(f"getdelta")

        return self.receive()

    def get_last_split_time(self):
        self.send("getlastsplittime")
        return self.receive("time")

    def get_comparison_split_time(self):
        self.send("getcomparisonsplittime")
        return self.receive("time")

    def get_current_time(self):
        self.send("getcurrenttime")
        return self.receive("time")

    def get_final_time(self, comparison=None):
        if comparison:
            self.send(f"getfinaltime {comparison}")
        else:
            self.send("getfinaltime")
        return self.receive("time")

    def get_predicted_time(self, comparison):
        self.send(f"getpredictedtime {comparison}")
        return self.receive("time")

    def get_best_possible_time(self):
        self.send("getbestpossibletime")
        return self.receive("time")

    def get_split_index(self):
        self.send("getsplitindex")
        return self.receive("int")

    def get_current_split_name(self):
        self.send("getcurrentsplitname")
        return self.receive()

    def get_previous_split_name(self):
        self.send("getprevioussplitname")
        return self.receive()

    def get_current_timer_phase(self):
        self.send("getcurrenttimerphase")
        return self.receive()


pattern = re.compile(
    r"^(?:(?P<hours>\d*):)?(?P<minutes>\d{1,2}):(?P<seconds>\d{2}).(?P<centiseconds>\d*)"
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
