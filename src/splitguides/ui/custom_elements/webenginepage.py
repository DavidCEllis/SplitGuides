"""
Replace the standard QWebEnginePage with one that launches links in the user's default browser
"""
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QDesktopServices


class ExtLinkWebEnginePage(QWebEnginePage):
    """
    QWebEnginePage that launches links in an external browser
    """

    def acceptNavigationRequest(self, url, _type, is_mainframe):
        # Launch external browser for clicking links, otherwise do default behaviour
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, _type, is_mainframe)
