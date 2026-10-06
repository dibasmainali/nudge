"""Make sure only one Nudge runs per user. A second launch just asks the first to show itself."""
import getpass

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def _default_name() -> str:
    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    return f"nudge-single-instance-{user}"


class SingleInstance(QObject):
    """Usage:  guard = SingleInstance(); if not guard.become_primary(): sys.exit(0)"""

    activated = Signal()      # another launch tried to start -> bring the window forward

    def __init__(self, name: str | None = None, parent=None):
        super().__init__(parent)
        self._name = name or _default_name()
        self._server: QLocalServer | None = None

    def become_primary(self) -> bool:
        """True if we are the first instance; False if one is already running (it gets notified)."""
        probe = QLocalSocket()
        probe.connectToServer(self._name)
        if probe.waitForConnected(300):
            probe.write(b"show")
            probe.waitForBytesWritten(300)
            probe.disconnectFromServer()
            return False

        QLocalServer.removeServer(self._name)     # clear a stale socket left by a crash
        server = QLocalServer(self)
        server.setSocketOptions(QLocalServer.UserAccessOption)
        if not server.listen(self._name):
            print(f"[nudge] warning: single-instance lock unavailable ({server.errorString()})")
        server.newConnection.connect(self._on_connection)
        self._server = server
        return True

    def _on_connection(self) -> None:
        while self._server and self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            sock.disconnected.connect(sock.deleteLater)
            self.activated.emit()
