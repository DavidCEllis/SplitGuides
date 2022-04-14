"""
Handle parsing a notes file into separate pages of notes.
"""
import os
from pathlib import Path

import bleach
import markdown


PERMITTED_TAGS = [
    "br",
    "del",
    "ins",
    "mark",
    "small",
    "sub",
    "sup",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "div",
    "img",
    "video",
    "source",
]

PERMITTED_ATTRIBUTES = {
    "*": ["class", "style"],
    "img": ["src", "alt", "width", "height"],
    "video": [
        "autoplay",
        "controls",
        "height",
        "loop",
        "muted",
        "poster",
        "src",
        "width",
    ],
    "source": ["src", "type"],
}


PERMITTED_STYLES = [
    "background-color",
    "color",
    "font-family",
    "font-size",
    "font-weight",
    "text-align",
]


class Notes:
    """
    Class to handle splitnotes and formatting

    Processing order is:
      Input -> Strip Comment lines (delimited by [ ])
            -> Split by separator
            -> Store
            [Render Call]
            -> Process
            -> Sanitize
            -> Render

    """

    def __init__(self, note_stream, separator="", *, preprocessor=None):
        """
        Note_stream should be an iterable object providing notes line by line

        :param note_stream: iterable object providing notes
        :param separator: The separator between split segments (default blank line)
        :param preprocessor: Tool if there is preprocessing to do on the notes
                             This should be determined by the file extension
        """
        if isinstance(note_stream, str):
            raise TypeError(
                "Expected file-like object for note_stream, but received string. "
                "Use Notes.from_file for paths."
            )
        elif isinstance(note_stream, os.PathLike):
            raise TypeError(
                "Expected file-like object for note_stream, but received path-like object. "
                "Use Notes.from_file for paths."
            )

        self.preprocessor = preprocessor
        self.separator = separator

        self.notes = []
        self.get_notes(note_stream)
        self.safe_mode = True
        self.cleaner = get_cleaner(
            PERMITTED_TAGS, PERMITTED_ATTRIBUTES, PERMITTED_STYLES
        )

    def get_notes(self, note_stream):
        """
        Parse the note stream and obtain the text to be rendered.

        :param note_stream: iterable containing notes by line
        """
        split_notes = []
        split = []
        for line in note_stream:
            line = line.rstrip()  # remove newlines
            if line.startswith("[") and line.endswith("]"):
                pass  # Ignore comment lines
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
    def from_file(cls, path, separator=""):
        """
        Helper method to parse a set of notes read from a given file path.

        :param path: path to notes text file
        :param separator: The separator between split segments (default blank line)
        :return: Instance of Notes parsed from the provided file
        """
        path = Path(path)
        if path.suffix == ".txt":
            preprocessor = TextProcessor()
        elif path.suffix == ".md":
            preprocessor = MarkdownProcessor()
        else:
            preprocessor = None

        with open(path, "r", encoding="utf-8") as f:
            notes = Notes(f, separator, preprocessor=preprocessor)
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

        if start >= end:
            result = ["<h1>End of Splits</h1>"]
        else:
            for idx in range(start, end):
                raw_split = self.notes[idx]
                if self.preprocessor:
                    split = self.preprocessor.process(raw_split)
                else:
                    split = raw_split
                result.append(split)

        # If in safe mode clean the HTML of unsafe data
        if self.safe_mode:
            result = [self.cleaner.clean(html) for html in result]

        return result


def get_cleaner(extra_tags, extra_attributes, extra_styles):
    """
    Get a HTML cleaner to remove dangerous tags

    This handles the external 'bleach' library.
    :param extra_tags:
    :param extra_attributes:
    :param extra_styles:
    :return:
    """
    valid_tags = bleach.sanitizer.ALLOWED_TAGS.copy()
    valid_tags.extend(extra_tags)
    valid_attributes = bleach.sanitizer.ALLOWED_ATTRIBUTES.copy()
    valid_attributes.update(extra_attributes)
    valid_styles = bleach.sanitizer.ALLOWED_STYLES.copy()
    valid_styles.extend(extra_styles)

    cleaner = bleach.sanitizer.Cleaner(
        tags=valid_tags, attributes=PERMITTED_ATTRIBUTES, styles=PERMITTED_STYLES
    )
    return cleaner


class TextProcessor:
    def __init__(self, *, continue_char="\\"):
        """
        Create a basic text processor

        :param continue_char: Character used to indicate a <br> tag should not be added
        """
        self.continue_char = continue_char

    def process(self, raw_text):
        """
        Basic processing for raw text, add breaks for newlines.
        Don't add a break if the line ends with the continuation char but remove the char

        :param raw_text: Basic split text
        :return: Text with <br> inserted for new lines
        """
        split_parts = (
            item[:-1] if item.endswith(self.continue_char) else f"{item}<br>"
            for item in raw_text.split("\n")
        )

        return "\n".join(split_parts)


class MarkdownProcessor:
    default_extensions = ["nl2br", "sane_lists", "tables"]

    def __init__(self, *, extensions=None):
        """
        Create a markdown processor using the markdown extension
        By default this uses the extensions for sane lists, tables and new line to break

        :param extensions: List of specific extensions, if not defined use defailts
        """
        self.extensions = (
            extensions if extensions is not None else self.default_extensions
        )

        self.formatter = markdown.Markdown(extensions=self.extensions)

    def process(self, raw_text):
        """
        Convert the raw MarkDown input into HTML
        :param raw_text: Markdown input as a string
        :return: processed HTML as a string
        """
        processed_text = self.formatter.convert(raw_text)
        self.formatter.reset()
        return processed_text
