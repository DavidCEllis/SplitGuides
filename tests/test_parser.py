import pytest
from io import StringIO

from splitnotes2.note_parser import Notes

notes_base = [
    "This is the first split",
    "[Split 1]",
    "There is some text here",
    "[ignore this]",
    "",
    "[Split 2]",
    "This is the second split",
    "Second Split Continued",
    "",
    "Third Split"
]

delimiter = "<split>"

notes_blank_delimiter = '\n'.join(notes_base)
notes_split_delimiter = '\n'.join(item if item != "" else delimiter for item in notes_base)


@pytest.mark.parametrize('separator, notes',
                         [("", notes_blank_delimiter), (delimiter, notes_split_delimiter)])
def test_parse(separator, notes):
    note_file = StringIO(notes)
    notes = Notes(note_file, separator)

    assert len(notes.notes) == 3
    assert notes.notes[0] == '\n'.join([notes_base[0], notes_base[2]])
    assert notes.notes[1] == '\n'.join(notes_base[6:8])
    assert notes.notes[2] == '\n'.join([notes_base[-1]])


def test_render():
    note_file = StringIO(notes_blank_delimiter)
    notes = Notes(note_file)

    expected = "This is the first split<br/>\nThere is some text here"

    assert notes.render_split(0) == expected
