from PySide6.QtGui import QColor
import re

def rgba_to_qcolor(s: str):
    if len(s) == 9 and s[0] == "#":
        rgb, a = s[1:7], s[7:9]
        return QColor(f"#{a}{rgb}")
    else:
        return QColor(s)

def qcolor_to_rgba(color: QColor):
    argb = color.name(QColor.HexArgb)
    a, rgb = argb[1:3], argb[3:9]
    return f"#{rgb}{a}"
