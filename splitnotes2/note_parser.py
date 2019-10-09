"""
Handle parsing a notes file into separate pages of notes.
"""


class Notes:
    """
    Class to handle splitnotes and formatting
    """
    def __init__(self, note_stream, separator='', formatter=None):
        """
        Note_stream should be an iterable object providing notes line by line

        :param note_stream: iterable object providing notes
        :param separator: The separator between split segments (default blank line)
        :param formatter: The formatter to tidy up the notes
        """
        self.formatter = formatter
        split_notes = []
        split = []
        for line in note_stream:
            line = line.rstrip()  # remove newlines
            if line.startswith('[') and line.endswith(']'):
                pass  # Ignore comment lines
            elif line == separator:
                # Split segment on separator
                split_notes.append("\n".join(split))
                split = []
            else:
                split.append(line)
        else:
            split_notes.append("\n".join(split))

        self.notes = split_notes

    @classmethod
    def from_file(cls, path, separator='', formatter=None):
        """
        Helper method to parse a set of notes read from a given file path.

        :param path: path to notes text file
        :param separator: The separator between split segments (default blank line)
        :param formatter: The formatter to tidy up the notes
        :return: Instance of Notes parsed from the provided file
        """
        with open(path, 'r') as f:
            notes = Notes(f, separator, formatter)
        return notes

    def render_split(self, idx):
        """
        Render the notes as text for HTML

        :param idx:
        :return: notes
        """
        raw_split = self.notes[idx]
        if self.formatter:
            result = self.formatter(raw_split)
        else:
            result = '<br/>\n'.join(raw_split.split('\n'))

        return result
