"""
Handle parsing a notes file into separate pages of notes.
"""


class SecurityError(Exception):
    pass


class Notes:
    """
    Class to handle splitnotes and formatting
    """

    def __init__(self, note_stream, separator="", preprocessor=None):
        """
        Note_stream should be an iterable object providing notes line by line

        :param note_stream: iterable object providing notes
        :param separator: The separator between split segments (default blank line)
        :param preprocessor: Tool if there is preprocessing to do on the notes
        """
        self.preprocessor = preprocessor
        self.separator = separator

        self.notes = []
        self.get_notes(note_stream)

    def get_notes(self, note_stream, safe_mode=True):
        split_notes = []
        split = []
        for line in note_stream:
            line = line.rstrip()  # remove newlines
            if line.startswith("[") and line.endswith("]"):
                pass  # Ignore comment lines
            elif "<script" in line and safe_mode is True:
                raise SecurityError("Script tags are not allowed in safe mode.")
            elif line == self.separator:
                # If the split is empty and the separator is blank
                # Ignore the break
                if not (split or self.separator):
                    continue
                # Split segment on separator
                split_notes.append("\n".join(split))
                split = []
            else:
                split.append(line)
        else:
            split_notes.append("\n".join(split))

        self.notes = split_notes

    @classmethod
    def from_file(cls, path, separator="", formatter=None):
        """
        Helper method to parse a set of notes read from a given file path.

        :param path: path to notes text file
        :param separator: The separator between split segments (default blank line)
        :param formatter: The formatter to tidy up the notes
        :return: Instance of Notes parsed from the provided file
        """
        with open(path, "r") as f:
            notes = Notes(f, separator, formatter)
        return notes

    def render_splits(self, start, end):
        """
        Render the notes as a list of text items for HTML

        :param start: Split index to start rendering
        :param end: Split index to end rendering
        :return: notes
        """
        start = max(start, 0)
        end = min(end, len(self.notes))

        result = []

        for idx in range(start, end):
            raw_split = self.notes[idx]
            if self.preprocessor:  # pragma: nocover
                split = self.preprocessor(raw_split)
            else:
                split_parts = (
                    item[:-1] if item.endswith("\\") else f"{item}<br>"
                    for item in raw_split.split("\n")
                )

                split = "\n".join(split_parts)
            result.append(split)

        return result
