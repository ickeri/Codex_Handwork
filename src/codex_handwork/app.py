import sys

from PySide6.QtWidgets import QApplication

from codex_handwork.gui import CopyWindow, build_window_icon


def run() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(build_window_icon())
    window = CopyWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
