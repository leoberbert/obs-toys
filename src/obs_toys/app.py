from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw  # noqa: E402

from .ui import MainWindow


class ObsToysApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="io.github.leoberbert.obs_toys")

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = MainWindow(self)
        window.present()


def main() -> int:
    app = ObsToysApplication()
    return app.run([])
