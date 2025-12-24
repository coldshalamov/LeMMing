"""
Auto-approve specific toast notifications by sending Alt+Enter when a toast
contains a target keyword (e.g., "antigravity", "claude code").

Uses a WinEvent hook on toast windows plus UIAutomation to read the toast text.
Requires Python 3.12+, keyboard, pywin32, comtypes.
Run:  py -3.12 scripts\\toast_alt_enter.py
"""
import ctypes
import ctypes.wintypes as wintypes
import keyboard
import win32api
import win32con
import win32gui
import comtypes.client

# Generate / load UIAutomation interfaces.
comtypes.client.GetModule("UIAutomationCore.dll")
import comtypes.gen.UIAutomationClient as uia  # noqa: E402


# Toast popups are CoreWindow instances hosted by ShellExperienceHost.exe.
TOAST_WINDOW_CLASS = "Windows.UI.Core.CoreWindow"

# Keywords to auto-approve.
KEYWORDS = ["antigravity"]
TARGET_WINDOW_HINT = "antigravity"  # substring to identify the client window title


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

automation = uia.CUIAutomation()
true_cond = automation.CreateTrueCondition()


def toast_text(hwnd: int) -> str:
    """Extract visible text from a toast window using UIAutomation."""
    try:
        element = automation.ElementFromHandle(hwnd)
        coll = element.FindAll(uia.TreeScope_Subtree, true_cond)
        parts = []
        for i in range(coll.Length):
            child = coll.GetElement(i)
            name = child.CurrentName
            if name:
                parts.append(name)
        return " ".join(parts)
    except Exception:
    return ""


def _restore_and_focus_window(title_hint: str) -> None:
    """Try to find the Antigravity window, restore it, and bring it to foreground."""
    matches = []

    def _enum_cb(h, _param):
        try:
            if not win32gui.IsWindowVisible(h):
                return
            title = win32gui.GetWindowText(h)
            if title and title_hint.lower() in title.lower():
                matches.append(h)
        except Exception:
            return

    win32gui.EnumWindows(_enum_cb, None)
    if not matches:
        return

    hwnd = matches[0]
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        # Fallback: force foreground by attaching thread inputs.
        try:
            fg = win32gui.GetForegroundWindow()
            ct = win32api.GetCurrentThreadId()
            wt = win32api.GetWindowThreadProcessId(hwnd)[0]
            ft = win32api.GetWindowThreadProcessId(fg)[0]
            user32 = ctypes.windll.user32
            user32.AttachThreadInput(ft, ct, True)
            user32.AttachThreadInput(wt, ct, True)
            win32gui.SetForegroundWindow(hwnd)
            user32.AttachThreadInput(ft, ct, False)
            user32.AttachThreadInput(wt, ct, False)
        except Exception:
            return


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
    if cls != TOAST_WINDOW_CLASS:
        return

    text = toast_text(hwnd).lower()
    if any(k in text for k in KEYWORDS):
        _restore_and_focus_window(TARGET_WINDOW_HINT)
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

    print(
        "Watching for toast windows containing any of: "
        + ", ".join(KEYWORDS)
        + " ; will press Alt+Enter on match."
    )
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    user32.UnhookWinEvent(hook)
    ole32.CoUninitialize()


if __name__ == "__main__":
    main()
