from threading import Thread
import pyperclip
from winput import *


def modify_keys(mods, keys):
    # hit one or multiple keys with one or more modifiers
    if type(mods) == str:
        mods = [mods]
    if type(keys) == str:
        keys = [keys]
    mods = [m.lower() for m in mods]
    keys = [k.lower() for k in keys]
    for mod in mods:
        press_key(mod)
    hit_keys(keys)
    for mod in mods:
        release_key(mod)


def paste_insert(s):
    temp = pyperclip.paste()
    pyperclip.copy(s)
    modify_keys('ctrl', 'v')
    pyperclip.copy(temp)


class Rapid:

    def __init__(self):
        self.l_click = False
        self.r_click = False
        self.keys = set()

    def rapid_l_click(self):
        while self.l_click:
            time.sleep(0.017)
            left_click_down()
            time.sleep(0.017)
            left_click_up()

    def toggle_l_click(self):
        if self.l_click:
            self.l_click = False
        else:
            self.l_click = True
            newt = Thread(target=self.rapid_l_click)
            newt.start()

    def rapid_r_click(self):
        while self.r_click:
            time.sleep(0.017)
            right_click_down()
            time.sleep(0.017)
            right_click_up()

    def toggle_r_click(self):
        if self.r_click:
            self.r_click = False
        else:
            self.r_click = True
            newt = Thread(target=self.rapid_r_click)
            newt.start()

    def rapid_hit(self, key):
        while key in self.keys:
            time.sleep(0.017)
            press_key(key)
            time.sleep(0.017)
            release_key(key)

    def toggle(self, key):
        if key in self.keys:
            self.keys.remove(key)
        else:
            self.keys.add(key)
            newt = Thread(target=self.rapid_hit, args=(key,))
            newt.start()


class Latex:

    def __init__(self):
        self.l_right = False

    def latex_f8_down(self):
        if self.l_right:
            return None
        self.l_right = True

        def aux():
            modify_keys('Lcontrol', 'm')
            while self.l_right:
                time.sleep(0.02)
            hit_keys('right')

        newt = Thread(target=aux)
        newt.start()

    def latex_f8_up(self):
        self.l_right = False

    def latex_f5(self):
        modify_keys('Lcontrol', 'm')
        modify_keys('alt', 'm')
        hit_keys(('t', 'a'))


def temp_macro():
    move_mouse(2500, 300)
    left_click_down(0.02)
    left_click_up()
    modify_keys('Lcontrol', ('n', 'v', 's'))
