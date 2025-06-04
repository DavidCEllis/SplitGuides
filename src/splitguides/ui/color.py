from PySide6.QtGui import QColor
import re

def rgba_to_qcolor(s: str):
    m = re.search(r"#(......)(..)", s)
    if m:
        return QColor("#" + m.group(2) + m.group(1))
    else:
        return QColor(s)

def qcolor_to_rgba(color: QColor):
    argb = color.name(QColor.HexArgb)
    m = re.search(r"#(..)(......)", argb)
    return "#" + m.group(2) + m.group(1)
