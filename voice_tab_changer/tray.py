from typing import Callable

import pystray
from PIL import Image, ImageDraw

import config as _config


def _make_icon(listening: bool) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (74, 144, 217, 255))
    draw = ImageDraw.Draw(img)
    # Draw a bold white "V"
    margin = 8
    mid_x = size // 2
    bottom_y = size - margin
    top_y = margin
    draw.line([(margin, top_y), (mid_x, bottom_y)], fill="white", width=7)
    draw.line([(mid_x, bottom_y), (size - margin, top_y)], fill="white", width=7)
    return img


class TrayApp:
    def __init__(self, cfg: dict, on_toggle: Callable[[bool], None]) -> None:
        self._cfg = cfg
        self._on_toggle = on_toggle
        self._listening = True
        self._icon: pystray.Icon | None = None

    def _status_text(self) -> str:
        return "Listening" if self._listening else "Off"

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: f"Status: {self._status_text()}",
                lambda icon, item: None,
                enabled=False,
            ),
            pystray.MenuItem("Toggle", self._toggle),
            pystray.MenuItem("Edit Config", self._edit_config),
            pystray.MenuItem("Quit", self._quit),
        )

    def _toggle(self, icon: pystray.Icon, item) -> None:
        self._listening = not self._listening
        self._on_toggle(self._listening)
        icon.icon = _make_icon(self._listening)
        icon.title = f"Voice Tab Changer — {self._status_text()}"

    def _edit_config(self, icon: pystray.Icon, item) -> None:
        _config.open_config_in_editor()

    def _quit(self, icon: pystray.Icon, item) -> None:
        icon.stop()

    def update_status(self, listening: bool) -> None:
        self._listening = listening
        if self._icon:
            self._icon.icon = _make_icon(listening)
            self._icon.title = f"Voice Tab Changer — {self._status_text()}"

    def run(self) -> None:
        self._icon = pystray.Icon(
            name="VoiceTabChanger",
            icon=_make_icon(self._listening),
            title=f"Voice Tab Changer — {self._status_text()}",
            menu=self._build_menu(),
        )
        self._icon.run()
