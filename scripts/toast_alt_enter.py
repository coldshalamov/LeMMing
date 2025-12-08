"""
Send Alt+Enter whenever a toast popup window appears.
This uses a WinEvent hook on the toast window class instead of the WinRT API
because `UserNotificationListener.get_current()` is unavailable on this setup.
Requires Python 3.12+, keyboard, pywin32.
Run:  py -3.12 scripts\\toast_alt_enter.py
"""
import ctypes
import ctypes.wintypes as wintypes
import keyboard
import win32con
import win32gui


# Toast popups are CoreWindow instances hosted by ShellExperienceHost.exe
TOAST_WINDOW_CLASS = "Windows.UI.Core.CoreWindow"


WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.HWND,
    wintypes.LONG,
    wintypes.LONG,
    wintypes.DWORD,
    wintypes.DWORD,
)


def _win_event_callback(
    hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime
):
    # Ignore child events and invalid handles.
    if hwnd == 0 or idObject != 0:
        return
    try:
        cls = win32gui.GetClassName(hwnd)
    except Exception:
        return
    if cls == TOAST_WINDOW_CLASS:
        keyboard.send("alt+enter")


def main() -> None:
    user32 = ctypes.windll.user32
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize(0)

    proc = WinEventProcType(_win_event_callback)
    hook = user32.SetWinEventHook(
        win32con.EVENT_OBJECT_SHOW,
        win32con.EVENT_OBJECT_SHOW,
        0,
        proc,
        0,
        0,
        win32con.WINEVENT_OUTOFCONTEXT | win32con.WINEVENT_SKIPOWNPROCESS,
    )
    if hook == 0:
        print("Failed to set WinEvent hook.")
        return

    print("Watching for toast windows; will press Alt+Enter on arrival.")
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    user32.UnhookWinEvent(hook)
    ole32.CoUninitialize()


if __name__ == "__main__":
    main()
