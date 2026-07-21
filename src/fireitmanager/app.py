"""Application entry point for FireIT Manager."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from fireitmanager.ui.main_window import FireITMainWindow


def main() -> int:
    """Create and launch the application window."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = FireITMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
