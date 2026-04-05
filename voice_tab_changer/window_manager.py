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
    from AppKit import NSWorkspace, NSApplicationActivationPolicyRegular

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

    def focus_window(self, window: dict, maximize: bool = False) -> None:
        try:
            if sys.platform == "darwin":
                self._focus_macos(window, maximize)
            elif sys.platform == "win32":
                self._focus_windows(window, maximize)
        except Exception as e:
            _get_error_logger().error("Failed to focus window '%s': %s", window.get("title"), e)

    # --- macOS ---

    def _get_windows_macos(self) -> list[dict]:
        apps = NSWorkspace.sharedWorkspace().runningApplications()
        seen_pids = set()
        windows = []
        for app in apps:
            if app.activationPolicy() != NSApplicationActivationPolicyRegular:
                continue
            pid = app.processIdentifier()
            if pid in seen_pids:
                continue
            seen_pids.add(pid)
            name = app.localizedName() or ""
            if name:
                windows.append({
                    "title": name,
                    "owner": name,
                    "pid": pid,
                })
        return windows

    def _focus_macos(self, window: dict, maximize: bool = False) -> None:
        pid = window.get("pid")
        owner = window.get("owner", "")

        fullscreen_block = ""
        if maximize:
            fullscreen_block = f"""
                tell process "{owner}"
                    set value of attribute "AXFullScreen" of window 1 to true
                end tell"""

        if pid:
            script = f'''
                tell application "System Events"
                    set frontmost of first process whose unix id is {pid} to true
                    {fullscreen_block}
                end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return
            _get_error_logger().error(
                "System Events focus failed for pid %s: %s", pid, result.stderr.strip()
            )
        # Fallback: activate by app name
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

    def _focus_windows(self, window: dict, maximize: bool = False) -> None:
        hwnd = window.get("hwnd")
        if hwnd:
            cmd = win32con.SW_MAXIMIZE if maximize else win32con.SW_RESTORE
            win32gui.ShowWindow(hwnd, cmd)
            win32gui.SetForegroundWindow(hwnd)
