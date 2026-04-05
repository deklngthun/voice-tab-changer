import logging
import os
import subprocess
import sys

LOG_PATH = os.path.expanduser("~/.voicetabchanger/error.log")


def _get_error_logger() -> logging.Logger:
    logger = logging.getLogger("window_manager")
    if not logger.handlers:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        handler = logging.FileHandler(LOG_PATH)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
    return logger


if sys.platform == "darwin":
    import Quartz
    from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps

elif sys.platform == "win32":
    import win32gui
    import win32con


class WindowManager:
    def get_windows(self) -> list[dict]:
        if sys.platform == "darwin":
            return self._get_windows_macos()
        elif sys.platform == "win32":
            return self._get_windows_windows()
        return []

    def focus_window(self, window: dict) -> None:
        try:
            if sys.platform == "darwin":
                self._focus_macos(window)
            elif sys.platform == "win32":
                self._focus_windows(window)
        except Exception as e:
            _get_error_logger().error("Failed to focus window '%s': %s", window.get("title"), e)

    # --- macOS ---

    def _get_windows_macos(self) -> list[dict]:
        options = (
            Quartz.kCGWindowListOptionOnScreenOnly
            | Quartz.kCGWindowListExcludeDesktopElements
        )
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        windows = []
        for w in window_list:
            layer = w.get("kCGWindowLayer", -1)
            title = w.get("kCGWindowName", "") or ""
            owner = w.get("kCGWindowOwnerName", "") or ""
            if layer == 0 and (title or owner):
                display_title = f"{owner} — {title}" if title else owner
                windows.append({
                    "title": display_title,
                    "owner": owner,
                    "pid": w.get("kCGWindowOwnerPID"),
                    "raw": w,
                })
        return windows

    def _focus_macos(self, window: dict) -> None:
        pid = window.get("pid")
        if pid:
            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
            if app:
                app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                return
        # Fallback: AppleScript by owner name
        owner = window.get("owner", "")
        if owner:
            subprocess.run(
                ["osascript", "-e", f'tell application "{owner}" to activate'],
                capture_output=True,
            )

    # --- Windows ---

    def _get_windows_windows(self) -> list[dict]:
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append({"title": title, "hwnd": hwnd})

        win32gui.EnumWindows(callback, None)
        return windows

    def _focus_windows(self, window: dict) -> None:
        hwnd = window.get("hwnd")
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
