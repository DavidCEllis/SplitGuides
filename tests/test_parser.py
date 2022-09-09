import pytest
from io import StringIO
from pathlib import Path

from unittest.mock import patch, mock_open

from splitguides.note_parser import Notes, TextProcessor

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
    "Third Split",
]

delimiter = "<split>"

notes_blank_delimiter = "\n".join(notes_base)
notes_split_delimiter = "\n".join(
    item if item != "" else delimiter for item in notes_base
)


def assert_notes_match(notes):
    assert len(notes.notes) == 3
    assert notes.notes[0] == "\n".join([notes_base[0], notes_base[2]])
    assert notes.notes[1] == "\n".join(notes_base[6:8])
    assert notes.notes[2] == "\n".join([notes_base[-1]])


@pytest.mark.parametrize(
    "separator, notes",
    [("", notes_blank_delimiter), (delimiter, notes_split_delimiter)],
)
def test_parse(separator, notes):
    note_file = StringIO(notes)
    preprocessor = TextProcessor()
    notes = Notes(note_file, separator, preprocessor=preprocessor)
    assert_notes_match(notes)


def test_render():
    # Basic renderer test
    note_file = StringIO(notes_blank_delimiter)
    preprocessor = TextProcessor()
    notes = Notes(note_file, preprocessor=preprocessor)

    expected = "This is the first split<br>\nThere is some text here<br>"

    assert notes.render_splits(0, 1)[0] == expected


@pytest.mark.parametrize(
    "safe_mode, expected",
    [
        (True, "&lt;script&gt;Escape these tags&lt;/script&gt;"),
        (False, "<script>Escape these tags</script>"),
    ],
)
def test_render_safe(safe_mode, expected):
    # Test notes are being scrubbed for script tags correctly.
    unsafe_note = "<script>Escape these tags</script>"
    notes = Notes(StringIO(unsafe_note))

    notes.safe_mode = safe_mode

    result = notes.render_splits(0, 1)
    assert result[0] == expected


def test_ignore_blank():
    notes_modified = notes_base.copy()
    notes_modified.insert(4, "")  # insert an extra blank so there's a double

    note_file = StringIO("\n".join(notes_modified))
    preprocessor = TextProcessor()
    notes = Notes(note_file, preprocessor=preprocessor)

    assert_notes_match(notes)


def test_from_file():
    pth = Path("path/to/notes.txt")
    m = mock_open(read_data=notes_blank_delimiter)
    with patch("builtins.open", m):
        notes = Notes.from_file(pth)

    m.assert_called_once_with(pth, "r", encoding="utf-8")

    # Check the correct preprocessor is chosen
    assert isinstance(notes.preprocessor, TextProcessor)

    assert_notes_match(notes)
