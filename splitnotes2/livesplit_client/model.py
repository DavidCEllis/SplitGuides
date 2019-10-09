"""
Handle livesplit
"""
from ..util import parse_time


class LivesplitHandler:
    def __init__(self, connection):
        self.connection = connection

    def send(self, message):
        m = message.encode('UTF8')
        self.connection.send(m + b'\r\n')

    def recieve(self, datatype="text"):
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
        """
        self.send(f"setcomparison {comparison}")

    def get_delta(self, comparison=None):
        if comparison:
            self.send(f"getdelta {comparison}")
        else:
            self.send(f"getdelta")

        return self.recieve()

    def get_last_split_time(self):
        self.send("getlastsplittime")
        return self.recieve("time")

    def get_comparison_split_time(self):
        self.send("getcomparisonsplittime")
        return self.recieve("time")

    def get_current_time(self):
        self.send("getcurrenttime")
        return self.recieve("time")

    def get_final_time(self, comparison=None):
        if comparison:
            self.send(f"getfinaltime {comparison}")
        else:
            self.send("getfinaltime")
        return self.recieve("time")

    def get_predicted_time(self, comparison):
        self.send(f"getpredictedtime {comparison}")
        return self.recieve("time")

    def get_best_possible_time(self):
        self.send("getbestpossibletime")
        return self.recieve("time")

    def get_split_index(self):
        self.send("getsplitindex")
        return self.recieve("int")

    def get_current_split_name(self):
        self.send("getcurrentsplitname")
        return self.recieve()

    def get_previous_split_name(self):
        self.send("getprevioussplitname")
        return self.recieve()

    def get_current_timer_phase(self):
        self.send("getcurrenttimerphase")
        return self.recieve()