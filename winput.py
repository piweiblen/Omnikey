"""windows input using ctypes"""

import ctypes
from ctypes import wintypes
import win32con
import win32api
import time
import os

BASE_PATH = r"C:\Users\Peter\Documents\PycharmProjects\OmniKeyboard\\"

user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008
MAPVK_VK_TO_VSC = 0
VK_TAB  = 0x09
VK_MENU = 0x12
MK_LBUTTON = 0x0001
MK_MBUTTON = 0x0010
MK_RBUTTON = 0x0002

# C struct definitions
wintypes.ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))


LPINPUT = ctypes.POINTER(INPUT)


def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args


user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT,  # nInputs
                             LPINPUT,        # pInputs
                             ctypes.c_int)   # cbSize


def fetch_dict(name):
    file = open(os.path.join(BASE_PATH, name))
    ret_val = eval(file.read())
    file.close()
    return ret_val


keycodes = fetch_dict("data\\keycodes.txt")


def press_key(key, delay=0):
    x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=keycodes[key]))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    time.sleep(delay)


def release_key(key, delay=0):
    x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=keycodes[key], dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    time.sleep(delay)


def extended_press(key, delay=0):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=keycodes[key], dwFlags=KEYEVENTF_EXTENDEDKEY))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    time.sleep(delay)


def extended_release(key, delay=0):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=keycodes[key], dwFlags=KEYEVENTF_KEYUP+KEYEVENTF_EXTENDEDKEY))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    time.sleep(delay)


def move_mouse(x_pos, y_pos, delay=0):
    win32api.SetCursorPos((x_pos, y_pos))
    time.sleep(delay)


def left_click_down(delay=0):
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(delay)


def left_click_up(delay=0):
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(delay)


def right_click_down(delay=0):
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
    time.sleep(delay)


def right_click_up(delay=0):
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
    time.sleep(delay)


def hit_key(key, delay=0.016):
    press_key(key)
    time.sleep(delay)
    release_key(key)
    time.sleep(delay)


def hit_keys(keys, delay=0.016):
    for key in keys:
        press_key(key)
        time.sleep(delay)
        release_key(key)
        time.sleep(delay)
