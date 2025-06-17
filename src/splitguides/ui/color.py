"""
Helper functions for converting between different colour formats
"""


from PySide6.QtGui import QColor


def rgba_to_qcolor(s: str) -> QColor:
    """
    Convert #rrggbbaa colour to a QColor object

    QColor is used in the settings colour picker dialog

    :param s: Colour as #rrggbbaa string
    :return: QColor
    """
    if len(s) == 9 and s[0] == "#":
        rgb, a = s[1:7], s[7:9]
        return QColor(f"#{a}{rgb}")
    else:
        return QColor(s)


def qcolor_to_rgba(color: QColor) -> str:
    """
    Convert QColor back to an #rrggbbaa string

    Used in the settings dialog

    :param color: QColor object
    :return: Colour as #rrggbbaa string
    """
    argb = color.name(QColor.NameFormat.HexArgb)
    a, rgb = argb[1:3], argb[3:9]
    return f"#{rgb}{a}"


def rgba_to_qss(s: str) -> str:
    """
    Convert hex #rrggbbaa string to a format used in Qt's own style sheets

    This is used for the background of the notes widget itself.

    :param s: Colour as #rrggbbaa string
    :return: Colour as 'rgba(r, g, b, a) string
    """
    c = rgba_to_qcolor(s)
    r, g, b, a = c.red(), c.green(), c.blue(), c.alpha()
    return f"rgba({r}, {g}, {b}, {a})"
