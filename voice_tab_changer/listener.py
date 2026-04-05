import threading
from typing import Callable, Optional

from pynput import keyboard


def _parse_hotkey(hotkey_str: str) -> set:
    """Parse 'ctrl+shift+space' into a set of pynput Key/KeyCode objects."""
    mapping = {
        "ctrl": keyboard.Key.ctrl,
        "shift": keyboard.Key.shift,
        "alt": keyboard.Key.alt,
        "cmd": keyboard.Key.cmd,
        "space": keyboard.Key.space,
        "enter": keyboard.Key.enter,
        "tab": keyboard.Key.tab,
        "esc": keyboard.Key.esc,
        "backspace": keyboard.Key.backspace,
        "delete": keyboard.Key.delete,
        "up": keyboard.Key.up,
        "down": keyboard.Key.down,
        "left": keyboard.Key.left,
        "right": keyboard.Key.right,
        "f1": keyboard.Key.f1,
        "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5,
        "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7,
        "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11,
        "f12": keyboard.Key.f12,
    }
    parts = hotkey_str.lower().split("+")
    keys = set()
    for part in parts:
        part = part.strip()
        if part in mapping:
            keys.add(mapping[part])
        elif len(part) == 1:
            keys.add(keyboard.KeyCode.from_char(part))
    return keys


class HotkeyListener:
    def __init__(
        self,
        cfg: dict,
        on_press_callback: Callable[[], None],
        on_release_callback: Callable[[], None],
    ) -> None:
        self._combo = _parse_hotkey(cfg.get("hotkey", "ctrl+shift+space"))
        self._on_press = on_press_callback
        self._on_release = on_release_callback
        self._pressed: set = set()
        self._active = False  # True while the combo is held
        self._listener: Optional[keyboard.Listener] = None

    def _canonical(self, key) -> object:
        """Normalize modifier keys to their generic form."""
        modifiers = {
            keyboard.Key.ctrl_l: keyboard.Key.ctrl,
            keyboard.Key.ctrl_r: keyboard.Key.ctrl,
            keyboard.Key.shift_l: keyboard.Key.shift,
            keyboard.Key.shift_r: keyboard.Key.shift,
            keyboard.Key.alt_l: keyboard.Key.alt,
            keyboard.Key.alt_r: keyboard.Key.alt,
            keyboard.Key.cmd_l: keyboard.Key.cmd,
            keyboard.Key.cmd_r: keyboard.Key.cmd,
        }
        return modifiers.get(key, key)

    def _on_key_press(self, key) -> None:
        self._pressed.add(self._canonical(key))
        if not self._active and self._combo.issubset(self._pressed):
            self._active = True
            threading.Thread(target=self._on_press, daemon=True).start()

    def _on_key_release(self, key) -> None:
        canonical = self._canonical(key)
        if canonical in self._combo and self._active:
            self._active = False
            threading.Thread(target=self._on_release, daemon=True).start()
        self._pressed.discard(canonical)

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
