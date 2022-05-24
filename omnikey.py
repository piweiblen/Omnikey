import pyWinhook as pyHook
import pythoncom
from pywinusb import hid
from funky import *


def act(action):
    # preform action tuple
    # action: tuple(func, *args)
    if action is not None:
        action[0](*action[1:])


class PseudoEvent:

    def __init__(self, key):
        self.Key = key
        self.Injected = False


class Remap:

    def __init__(self, name, mapping, meta, func_map):
        self.name = name
        self.mapping = dict()
        self.always_on_dict = dict()
        self.meta = meta
        # convert file syntax into action tuples
        for keys in mapping:
            value = mapping[keys]
            if value is None:
                continue
            if type(keys) == str:
                keys = (keys,)
            keys = tuple(k.lower() for k in keys)
            if ("release",) + keys not in mapping:
                if type(value) == str:
                    self.mapping[keys] = (press_key, value)
                    self.mapping[("release",) + keys] = (release_key, value)
                    continue
                if value[0] == "extended":
                    self.mapping[keys] = (extended_press, value[1])
                    self.mapping[("release",) + keys] = (extended_release, value[1])
                    continue
            self.mapping[keys] = (func_map[value[0]],) + value[1:]
        if "default" in meta:
            self.active = meta["default"]
        else:
            self.active = False
        if "toggle" in meta:
            self.mapping[meta["toggle"]] = (self.toggle, self.name)
            self.always_on_dict[meta["toggle"]] = (self.toggle, self.name)
        if 'pre' in meta:
            self.pre_act = (func_map[meta['pre'][0]],) + meta['pre'][1:]
        else:
            self.pre_act = None
        if 'post' in meta:
            self.post_act = (func_map[meta['post'][0]],) + meta['post'][1:]
        else:
            self.post_act = None

    def do_action(self, key, pressed, is_release):
        if self.active:
            maps = self.mapping
        else:
            maps = self.always_on_dict
        for keys in tuple(self.always_on_dict) + tuple(maps.keys()):
            if (keys[0] == "release") != is_release:
                continue
            if keys[-1] != key:
                continue
            if keys[0] == "release":
                prereqs = keys[1:-1]
            else:
                prereqs = keys[:-1]
            passes = True
            for p in prereqs:
                if p.startswith("~"):
                    if p[1:] in pressed:
                        passes = False
                        break
                else:
                    if p not in pressed:
                        passes = False
                        break
            if passes:
                act(self.pre_act)
                act(maps[keys])
                act(self.post_act)
                return True
        return False

    def toggle(self, map_name):
        if self.name == map_name:
            if self.active:
                print(self.name, 'remap stopped')
            else:
                print(self.name, 'remap running')
            self.active = not self.active


def end_pump():
    ctypes.windll.user32.PostQuitMessage(0)


class AllMaps:

    def __init__(self):
        self.terminate = False
        self.all_maps = []
        self.rapids = Rapid()
        self.tex = Latex()
        func_map = {"press": press_key,
                    "release": release_key,
                    "extended press": extended_press,
                    "extended release": extended_release,
                    "modify keys": modify_keys,
                    "paste insert": paste_insert,
                    "hit key": hit_key,
                    "hit keys": hit_keys,
                    "rapid left": self.rapids.rapid_l_click,
                    "rapid right": self.rapids.rapid_r_click,
                    "rapid hit": self.rapids.rapid_hit,
                    "tex 5": self.tex.latex_f5,
                    "tex 8": self.tex.latex_f8_down,
                    "tex 8 up": self.tex.latex_f8_up,
                    "temp macro": temp_macro}
        for file in os.listdir(os.path.join(BASE_PATH, "remaps")):
            map_name = file[:file.rfind('.')]
            mapping = fetch_dict(os.path.join(BASE_PATH, "remaps", file))
            if os.path.exists(os.path.join(BASE_PATH, "remap meta", file)):
                map_meta = fetch_dict(os.path.join("remap meta", file))
            else:
                map_meta = dict()
            self.all_maps.append(Remap(map_name, mapping, map_meta, func_map))
        self.pressed_keys = set()
        self.cur_hid = b''
        self.omni_press = b'rE0 r73'
        self.omni_release = b'rE0 rF0 r73'
        self.usb_hid_list = []

    def on_key_down(self, event):
        if self.terminate:
            end_pump()
        key = event.Key.lower()
        send = True
        if not event.Injected:  # let's not be tracking our own trail
            for m in self.all_maps:
                if m.do_action(key, self.pressed_keys, False):
                    send = False
        self.pressed_keys.add(key)
        return send

    def on_key_up(self, event):
        if self.terminate:
            end_pump()
        key = event.Key.lower()
        send = True
        if not event.Injected:  # let's not be tracking our own trail
            for m in self.all_maps:
                if m.do_action(key, self.pressed_keys, True):
                    send = False
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        return send

    def console_input(self):
        while 1:
            totog = input()
            if totog == 'usb':
                self.start_omni_hid()
                print("usb refreshed")
            if totog == 'test':
                press_key('Capital')
                time.sleep(0.1)
                release_key('Capital')
                time.sleep(1)
                press_key('Capital')
                time.sleep(0.1)
                release_key('Capital')
            if totog == 'exit':
                self.terminate = True
                break
            for m in self.all_maps:
                m.toggle(totog)

    def listen(self, data):
        new = bytearray(data).strip(b'\x00')
        old_len = len(self.cur_hid)
        cutoff = 0
        self.cur_hid += new
        for f in range(len(new)):
            if self.cur_hid[old_len+f+1-len(self.omni_press):old_len+f+1] == self.omni_press:
                self.on_key_down(PseudoEvent("omni"))
                cutoff = old_len + f
            if self.cur_hid[old_len+f+1-len(self.omni_release):old_len+f+1] == self.omni_release:
                self.on_key_up(PseudoEvent("omni"))
                cutoff = old_len + f
            if self.cur_hid[old_len + f] == b'\n':
                cutoff = old_len + f
        self.cur_hid = self.cur_hid[cutoff:]

    def start_omni_hid(self):
        name = "Soarer's Keyboard Converter"
        for usb in self.usb_hid_list:
            usb.close()
        self.usb_hid_list = []
        all_devices = hid.HidDeviceFilter().get_devices()
        none_found = True
        for device in all_devices:
            if name in str(device):
                self.usb_hid_list.append(device)
                device.open()
                device.set_raw_data_handler(self.listen)
                none_found = False
        if none_found:
            print('Keyboard usb device not found')


def main():
    map_class = AllMaps()

    # start up the mode input thread
    text = Thread(target=map_class.console_input)
    text.start()

    # hid listen thread to hack the omni key into existence
    map_class.start_omni_hid()

    # hook the board, yo
    hm = pyHook.HookManager()  # get the hook
    hm.KeyDown = map_class.on_key_down  # assign function to key down events
    hm.KeyUp = map_class.on_key_up  # assign function to key up events
    hm.HookKeyboard()  # set the hook
    print('Keyboard remap initialized')
    pythoncom.PumpMessages()  # wait forever
    print('Keyboard remap exited')


if __name__ == '__main__':
    main()
