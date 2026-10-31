import binascii
import json
import os
import supervisor
import usb_cdc
import storage
import board
import digitalio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners.keypad import MatrixScanner
from kmk.modules import Module
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys

try:
    from kmk.extensions.rgb import RGB, AnimationModes
except ImportError:
    try:
        from kmk.extensions.RGB import RGB, AnimationModes
    except ImportError:
        RGB = None
        AnimationModes = None
        print('RGB disabled: install neopixel and adafruit_pixelbuf libraries')

CONFIG_FILE = '/orbitpad_config.csv'
COLOR_FILE = '/orbitpad_color.json'
PROFILE_FILE = '/orbitpad_profile.json'  
SCREENS_DIR = '/screens'




OLED_ENABLED = False
NUM_KEYS = 12
MAX_PROFILES = 12
MAX_LAYERS = 4
LED_MAX_CHANNEL = 30  



ROW_PINS = (board.GP1, board.GP0, board.GP3, board.GP2)
COL_PINS = (board.GP8, board.GP7, board.GP6)
LAYER_BUTTON = board.GP9
ENCODER_PINS = (
    (board.GP10, board.GP11, board.GP20, False, 4),
    (board.GP13, board.GP14, board.GP12, False, 4),
)
RGB_PIN = board.GP19



OLED_SCK = board.GP18
OLED_MOSI = board.GP16
OLED_CS = board.GP17
OLED_DC = board.GP22
OLED_RST = board.GP21


media = MediaKeys()
SPECIAL = {
    'enter': KC.ENTER, 'return': KC.ENTER, 'esc': KC.ESC,
    'escape': KC.ESC, 'tab': KC.TAB, 'space': KC.SPACE,
    'backspace': KC.BSPC, 'delete': KC.DEL, 'home': KC.HOME,
    'end': KC.END, 'pageup': KC.PGUP, 'pagedown': KC.PGDN,
    'up': KC.UP, 'down': KC.DOWN, 'left': KC.LEFT, 'right': KC.RIGHT,
    'mute': KC.MUTE, 'volu': KC.VOLU, 'vold': KC.VOLD,
    'play': KC.MPLY, 'next': KC.MNXT, 'prev': KC.MPRV,
}
MODIFIERS = {'ctrl': KC.LCTRL, 'control': KC.LCTRL,
             'shift': KC.LSHIFT, 'alt': KC.LALT,
             'win': KC.LGUI, 'cmd': KC.LGUI, 'super': KC.LGUI}


def csv_rows(f):
    
    row, field = [], []
    quoted = False
    quote_pending = False
    while True:
        data = f.read(128)
        if not data:
            break
        for ch in data:
            if quoted:
                if quote_pending:
                    if ch == '"':
                        field.append('"')
                        quote_pending = False
                        continue
                    quoted = False
                    quote_pending = False
                    
                elif ch == '"':
                    quote_pending = True
                    continue
                else:
                    field.append(ch)
                    continue
            if ch == '"' and not field:
                quoted = True
            elif ch == ',':
                row.append(''.join(field))
                field = []
            elif ch == '\n':
                row.append(''.join(field))
                field = []
                if len(row) >= 6:
                    yield row
                row = []
            elif ch != '\r':
                field.append(ch)
    if quoted and not quote_pending:
        raise ValueError('Unclosed CSV quote')
    if field or row:
        row.append(''.join(field))
        if len(row) >= 6:
            yield row


def read_index(path=None):
    
    if path is None:
        path = CONFIG_FILE
    result = {}
    with open(path, 'r', encoding='utf-8') as f:
        for n, row in enumerate(csv_rows(f)):
            if n == 0:
                if [x.strip().lstrip('\ufeff') for x in row[:6]] != [
                    'profile', 'layer', 'key', 'icon', 'title', 'shortcut'
                ]:
                    raise ValueError('CSV columns must be profile,layer,key,icon,title,shortcut')
                continue
            profile, layer = row[0].strip(), row[1].strip()
            if not profile or not layer:
                continue
            if profile not in result:
                if len(result) >= MAX_PROFILES:
                    raise ValueError('Too many profiles')
                result[profile] = []
            if layer not in result[profile]:
                if len(result[profile]) >= MAX_LAYERS:
                    raise ValueError('Too many layers in ' + profile)
                result[profile].append(layer)
    if not result:
        raise ValueError('No profiles in CSV')
    return result


def profile_keys(profile, layer_names, path=None):
    if path is None:
        path = CONFIG_FILE
    result = [[{'icon': '', 'title': '', 'shortcut': ''} for _ in range(NUM_KEYS)]
              for _ in layer_names]
    with open(path, 'r', encoding='utf-8') as f:
        for row in csv_rows(f):
            if row[0] != profile or row[1] not in layer_names:
                continue
            try:
                idx = int(row[2]) - 1
            except ValueError:
                continue
            if 0 <= idx < NUM_KEYS:
                result[layer_names.index(row[1])][idx] = {
                    'icon': row[3], 'title': row[4], 'shortcut': row[5]
                }
    return result


def shortcut_to_keycode(text):
    if not isinstance(text, str) or not text.strip():
        return KC.NO
    text = text.strip()
    if text.lower() == 'layer_next':
        return KC.NO
    parts = [p.strip().lower() for p in text.split('+')]
    if len(parts) > 5 or any(not part for part in parts):
        return KC.NO
    if len(parts) > 1 and any(part not in MODIFIERS for part in parts[:-1]):
        return KC.NO
    name = parts[-1]
    try:
        if name in SPECIAL:
            key = SPECIAL[name]
        elif len(name) == 1 and 'a' <= name <= 'z':
            key = KC[name.upper()]
        elif len(name) == 1 and name.isdigit():
            key = KC['N' + name]
        else:
            key = KC[name.upper()]
        if key is None:
            return KC.NO
        for mod in reversed(parts[:-1]):
            key = MODIFIERS[mod](key)
        return key
    except (KeyError, AttributeError, ValueError, TypeError):
        return KC.NO


def load_saved_profile(index):

    try:
        with open(PROFILE_FILE, 'r') as f:
            profile = json.load(f)['profile']
        if isinstance(profile, str) and profile in index:
            return profile
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return next(iter(index))


def save_selected_profile(profile):
    if not writable():
        raise ValueError('Cannot save profile in GP15 maintenance mode')
    temp = PROFILE_FILE + '.new'
    try:
        with open(temp, 'w') as f:
            json.dump({'profile': profile}, f)
        replace_file(temp, PROFILE_FILE)
    except Exception:
        try:
            os.remove(temp)
        except OSError:
            pass
        raise


def load_saved_color():
    try:
        with open(COLOR_FILE, 'r') as f:
            rgb = json.load(f)['rgb']
        if isinstance(rgb, list) and len(rgb) == 3 and all(
            type(x) is int and 0 <= x <= 255 for x in rgb
        ):
            return tuple(rgb)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return (79, 142, 247)


def writable():
    try:
        return not storage.getmount('/').readonly
    except Exception:
        return False


def make_screen_name(pidx, lidx):
    return '{}/p{}l{}.bmp'.format(SCREENS_DIR, pidx, lidx)


def file_for_upload(name):
    if name == 'config':
        return CONFIG_FILE, 65536
    if not isinstance(name, str) or not name.startswith('screen:'):
        raise ValueError('Unknown upload name')
    parts = name.split(':')
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        raise ValueError('Bad screen identifier')
    pidx, lidx = int(parts[1]), int(parts[2])
    if not 0 <= pidx < MAX_PROFILES or not 0 <= lidx < MAX_LAYERS:
        raise ValueError('Screen index out of range')
    return make_screen_name(pidx, lidx), 4096  


def replace_file(tmp, target):
    
    backup = target + '.bak'
    try:
        os.remove(backup)
    except OSError:
        pass
    moved_old = False
    try:
        try:
            os.rename(target, backup)
            moved_old = True
        except OSError:
            pass  
        os.rename(tmp, target)
    except Exception:
        if moved_old:
            os.rename(backup, target)
        raise
    if moved_old:
        try:
            os.remove(backup)
        except OSError:
            pass


def repair_config_after_power_loss():
    
    def recover(target):
        try:
            os.stat(target)
        except OSError:
            try:
                os.rename(target + '.bak', target)
            except OSError:
                pass
    recover(CONFIG_FILE)
    recover(COLOR_FILE)
    recover(PROFILE_FILE)
    try:
        for entry in os.listdir(SCREENS_DIR):
            if entry.endswith('.bmp.bak'):
                recover(SCREENS_DIR + '/' + entry[:-4])
    except OSError:
        pass


class OrbitPadModule(Module):
    def __init__(self, encoder, rgb, index):
        self.encoder = encoder
        self.rgb = rgb
        self.index = index
        self.profile = load_saved_profile(index)
        self.layers = index[self.profile]
        try:
            self.keys = profile_keys(self.profile, self.layers)
        except (OSError, ValueError):
            self.keys = [[{'icon': '', 'title': '', 'shortcut': ''}
                          for _ in range(NUM_KEYS)] for _ in self.layers]
        self.color = load_saved_color()
        self.last_layer = -1
        self.key_presses = 0
        self.last_key = None
        self.last_key_shortcut = ''
        self.layer_button_presses = 0
        self.button = None
        self.button_was_pressed = False
        self.last_button_ms = -250
        self.port = None
        self.rx = bytearray()
        self.rx_drop = False
        self.oled = None
        self.screen_asset = False
        self.upload = None

    def update_keymap(self, keyboard):
        keyboard.keymap = [
            [shortcut_to_keycode(k['shortcut']) for k in layer]
            for layer in self.keys
        ]
        
        self.encoder.map = [(
            (KC.VOLD, KC.VOLU, KC.MUTE),
            (KC.MPRV, KC.MNXT, KC.MPLY),
        ) for _ in self.layers]

    def current_layer(self, keyboard):
        li = keyboard.active_layers[0]
        return self.layers[li] if 0 <= li < len(self.layers) else self.layers[0]

    def activate_profile(self, keyboard, name, layer=None):
        if name not in self.index:
            raise ValueError('Unknown profile: ' + str(name))
        self.profile = name
        self.layers = self.index[name]
        self.keys = profile_keys(name, self.layers)
        self.update_keymap(keyboard)
        if layer not in self.layers:
            layer = self.layers[0]
        keyboard.active_layers[:] = [self.layers.index(layer)]

        
        try:
            self.show_screen(keyboard)
            self.show_color()
        except Exception as exc:
            print('VISUAL ERROR:', repr(exc))
        self.last_layer = keyboard.active_layers[0]

    def reload_config(self, keyboard):
        new_index = read_index()
        old_profile = self.profile
        old_layer = self.current_layer(keyboard)
        self.index = new_index
        self.activate_profile(keyboard, old_profile if old_profile in new_index else
                              next(iter(new_index)), old_layer)

    def during_bootup(self, keyboard):
        self.button = digitalio.DigitalInOut(LAYER_BUTTON)
        self.button.switch_to_input(pull=digitalio.Pull.UP)
        self.port = usb_cdc.data
        if self.port is not None:
            self.port.timeout = 0
            self.port.write_timeout = 0.25
        if OLED_ENABLED:
            try:
                self.setup_oled()
            except Exception as exc:
                print('OLED NOT READY:', repr(exc))
                self.oled = None
        self.last_layer = -1

    def setup_oled(self):
        used = ROW_PINS + COL_PINS + (LAYER_BUTTON, RGB_PIN, board.GP15)
        for pins in ENCODER_PINS:
            used += pins[:3]
        pins = (OLED_SCK, OLED_MOSI, OLED_CS, OLED_DC, OLED_RST)
        if len(set(pins)) != 5 or any(pin in used for pin in pins):
            raise ValueError('OLED pins collide with matrix/encoders/RGB/maintenance button')
        from ssd1351_softspi import SSD1351SoftSPI
        self.oled = SSD1351SoftSPI(OLED_SCK, OLED_MOSI, OLED_CS,
                                   OLED_DC, OLED_RST)

    def show_screen(self, keyboard):
        if self.oled is None:
            return
        pidx = list(self.index).index(self.profile)
        lidx = keyboard.active_layers[0]
        path = make_screen_name(pidx, lidx)
        self.oled.set_color(self.color)
        try:
            self.oled.start_bmp(path)
            self.screen_asset = True
        except Exception as exc:
            print('SCREEN (using numbered fallback):', path, repr(exc))
            self.screen_asset = False
            self.oled.start_placeholder(lidx, len(self.layers))

    def show_color(self):
        if self.rgb is None or self.rgb.pixels is None:
            return
        scaled = tuple(c * LED_MAX_CHANNEL // 255 for c in self.color)
        self.rgb.animation_mode = AnimationModes.STATIC_STANDBY
        self.rgb.set_rgb_fill(scaled)
        self.rgb.show()

    def status(self, keyboard, state='ok', cmd='get_status'):
        return {
            'status': state, 'cmd': cmd, 'device': 'OrbitPad', 'protocol': 1,
            'profile': self.profile, 'layer': self.current_layer(keyboard),
            'profiles': list(self.index), 'layers': self.layers,
            'writable': writable(),
            'display': self.oled is not None,
            'screen_asset': self.screen_asset,
            'screen_drawing': bool(getattr(self.oled, 'drawing', False)),
            'screen_rows': getattr(self.oled, 'rows_sent', 0),
            'rgb': self.rgb is not None and self.rgb.pixels is not None,
            'encoders': len(self.encoder.encoders),
            'key_presses': self.key_presses,
            'last_key': self.last_key,
            'last_key_shortcut': self.last_key_shortcut,
            'layer_button_presses': self.layer_button_presses,
            'color': self.color,
        }

    def send(self, obj):
        try:
            if self.port is not None and self.port.connected:
                self.port.write((json.dumps(obj) + '\n').encode('utf-8'))
        except Exception as exc:
            print('USB DATA SEND ERROR:', repr(exc))

    def ok(self, cmd, **values):
        message = {'status': 'ok', 'cmd': cmd}
        message.update(values)
        self.send(message)

    def fail(self, cmd, message):
        self.send({'status': 'error', 'cmd': cmd, 'msg': str(message)[:120]})

    def abort_upload(self):
        if self.upload is None:
            return
        session = self.upload
        self.upload = None
        try:
            session['file'].close()
        except Exception:
            pass
        try:
            os.remove(session['tmp'])
        except OSError:
            pass

    def begin_upload(self, msg):
        if not writable():
            raise ValueError('Maintenance mode: drive visible, filesystem read-only to firmware')
        name = msg.get('name')
        target, limit = file_for_upload(name)
        size, crc = msg.get('size'), msg.get('crc32')
        if type(size) is not int or type(crc) is not int or not 0 < size <= limit:
            raise ValueError('Bad size/CRC32')
        self.abort_upload()
        if name != 'config':
            try:
                os.mkdir(SCREENS_DIR)
            except OSError:
                pass  
        tmp = target + '.new'
        f = open(tmp, 'wb')
        self.upload = {'file': f, 'tmp': tmp, 'target': target, 'name': name,
                       'size': size, 'expected_crc': crc & 0xFFFFFFFF,
                       'crc': 0, 'received': 0}
        self.ok('begin_upload', name=name)

    def upload_chunk(self, msg):
        if self.upload is None:
            raise ValueError('No upload in progress')
        seq = msg.get('offset')
        data = msg.get('data')
        if type(seq) is not int or seq != self.upload['received']:
            raise ValueError('Wrong chunk offset')
        if not isinstance(data, str) or len(data) > 400:
            raise ValueError('Bad base64 chunk')
        raw = binascii.a2b_base64(data)
        if not raw or len(raw) > 192 or seq + len(raw) > self.upload['size']:
            raise ValueError('Chunk size incorrect')
        f = self.upload['file']
        f.write(raw)
        self.upload['crc'] = binascii.crc32(raw, self.upload['crc']) & 0xFFFFFFFF
        self.upload['received'] += len(raw)
        self.ok('upload_chunk', received=self.upload['received'])

    def end_upload(self):
        if self.upload is None:
            raise ValueError('No upload in progress')
        session = self.upload
        if session['received'] != session['size'] or session['crc'] != session['expected_crc']:
            self.abort_upload()
            raise ValueError('Upload size/CRC32 mismatch')
        session['file'].close()
        self.upload = None
        try:
            if session['name'] == 'config':
                read_index(session['tmp'])  
            else:
                with open(session['tmp'], 'rb') as f:
                    hdr = f.read(54)
                start = int.from_bytes(hdr[10:14], 'little')
                if (len(hdr) != 54 or hdr[:2] != b'BM'
                        or int.from_bytes(hdr[18:22], 'little') != 128
                        or int.from_bytes(hdr[22:26], 'little') != 128
                        or int.from_bytes(hdr[28:30], 'little') != 1
                        or int.from_bytes(hdr[30:34], 'little') != 0
                        or start < 54 or start + 2048 > session['size']):
                    raise ValueError('Expected uncompressed 128x128 1-bit BMP')
            replace_file(session['tmp'], session['target'])
            self.ok('end_upload', name=session['name'], bytes=session['received'])
        except Exception:
            try:
                os.remove(session['tmp'])
            except OSError:
                pass
            raise

    def set_color(self, msg, keyboard):
        color = tuple(msg.get(k) for k in ('r', 'g', 'b'))
        if any(type(x) is not int or x < 0 or x > 255 for x in color):
            raise ValueError('r/g/b must be 0..255')
        if msg.get('persist') and not writable():
            raise ValueError('Cannot save color in maintenance mode')
        self.color = color
        self.show_color()
        if msg.get('persist'):
            temp = COLOR_FILE + '.new'
            try:
                with open(temp, 'w') as f:
                    json.dump({'rgb': list(color)}, f)
                replace_file(temp, COLOR_FILE)
            except Exception:
                try:
                    os.remove(temp)
                except OSError:
                    pass
                raise
        if self.oled is not None:
            self.show_screen(keyboard)
        self.ok('set_color', color=self.color)

    def handle_line(self, line, keyboard):
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                raise ValueError('Expected JSON object')
        except (ValueError, TypeError) as exc:
            self.fail('?', exc)
            return
        cmd = msg.get('cmd', '')
        try:
            if cmd == 'ping':
                self.send(self.status(keyboard, 'pong', 'ping'))
            elif cmd == 'get_status':
                self.send(self.status(keyboard))
            elif cmd == 'set_profile':
                persist = msg.get('persist', False)
                if type(persist) is not bool:
                    raise ValueError('persist must be true or false')
                if persist and not writable():
                    raise ValueError('Cannot save profile in GP15 maintenance mode')
                self.activate_profile(keyboard, msg.get('profile'), msg.get('layer'))
                if persist:
                    save_selected_profile(self.profile)
                self.send(self.status(keyboard, 'ok', 'set_profile'))
            elif cmd == 'reload':
                self.reload_config(keyboard)
                self.send(self.status(keyboard, 'ok', 'reload'))
            elif cmd == 'set_color':
                self.set_color(msg, keyboard)
            elif cmd == 'begin_upload':
                self.begin_upload(msg)
            elif cmd == 'upload_chunk':
                self.upload_chunk(msg)
            elif cmd == 'end_upload':
                self.end_upload()
            elif cmd == 'abort_upload':
                self.abort_upload()
                self.ok('abort_upload')
            else:
                raise ValueError('Unknown command')
        except Exception as exc:
            self.fail(cmd, repr(exc))

    def poll_serial(self, keyboard):
        if self.port is None:
            return
        try:
            waiting = self.port.in_waiting
            raw = self.port.read(min(waiting, 128)) if waiting else None
            if not raw:
                return
            for byte in raw:
                if byte == 10:  
                    if self.rx and not self.rx_drop:
                        try:
                            self.handle_line(bytes(self.rx).decode('utf-8'), keyboard)
                        except UnicodeError:
                            self.fail('?', 'Invalid UTF-8')
                    self.rx = bytearray()
                    self.rx_drop = False
                elif byte != 13 and not self.rx_drop:
                    if len(self.rx) < 768:
                        self.rx.append(byte)
                    else:
                        self.rx = bytearray()
                        self.rx_drop = True
                        self.fail('?', 'Line too long')
        except Exception as exc:
            print('USB DATA READ ERROR:', repr(exc))
            

    def before_matrix_scan(self, keyboard):
        self.poll_serial(keyboard)
        pressed = not self.button.value
        now = supervisor.ticks_ms()
        if pressed and not self.button_was_pressed and ((now - self.last_button_ms) & 0x1FFFFFFF) >= 180:
            self.layer_button_presses += 1  
            if len(self.layers) > 1:
                keyboard.active_layers[:] = [(keyboard.active_layers[0] + 1) % len(self.layers)]
            self.last_button_ms = now
        self.button_was_pressed = pressed
        if self.last_layer != keyboard.active_layers[0]:
            self.last_layer = keyboard.active_layers[0]
            try:
                self.show_screen(keyboard)
                self.show_color()
            except Exception as exc:
                print('VISUAL ERROR:', repr(exc))
        if self.oled is not None and self.oled.drawing:
            try:
                self.oled.tick()  
            except Exception as exc:
                print('SCREEN STREAM ERROR:', repr(exc))
                was_asset = self.screen_asset
                self.screen_asset = False
                
                
                if was_asset:
                    try:
                        self.oled.start_placeholder(keyboard.active_layers[0],
                                                    len(self.layers))
                    except Exception as fallback_exc:
                        print('SCREEN FALLBACK ERROR:', repr(fallback_exc))

    def after_matrix_scan(self, keyboard):
        return

    def process_key(self, keyboard, key, is_pressed, int_coord):


        
        if is_pressed and int_coord is not None:
            self.key_presses += 1
            try:
                self.last_key = keyboard.coord_mapping.index(int_coord) + 1
                layer = keyboard.active_layers[0]
                self.last_key_shortcut = self.keys[layer][self.last_key - 1]['shortcut']
            except (ValueError, IndexError, TypeError):
                self.last_key = None
                self.last_key_shortcut = ''
        return key

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return

    def deinit(self, keyboard):
        self.abort_upload()
        if self.button is not None:
            self.button.deinit()
        if self.oled is not None:
            self.oled.deinit()


repair_config_after_power_loss()
try:
    index = read_index()
except (OSError, ValueError) as exc:
    print('CONFIG ERROR:', repr(exc), 'using empty Default layer')
    index = {'Default': ['Default']}

keyboard = KMKKeyboard()
keyboard.matrix = MatrixScanner(
    column_pins=COL_PINS, row_pins=ROW_PINS, columns_to_anodes=True
)



keyboard.coord_mapping = tuple(row * len(COL_PINS) + col
                               for col in range(len(COL_PINS))
                               for row in range(len(ROW_PINS)))
keyboard.modules.append(Layers())
encoder = EncoderHandler()
keyboard.modules.append(encoder)
encoder.pins = ENCODER_PINS
keyboard.extensions.append(media)

rgb = None
if RGB is not None:
    rgb = RGB(pixel_pin=RGB_PIN, num_pixels=12, val_limit=LED_MAX_CHANNEL,
              val_default=18, rgb_order=(1, 0, 2),
              animation_mode=AnimationModes.STATIC_STANDBY)
    keyboard.extensions.append(rgb)

runtime = OrbitPadModule(encoder, rgb, index)
keyboard.modules.append(runtime)
runtime.update_keymap(keyboard)



supervisor.runtime.autoreload = False

if __name__ == '__main__':
    keyboard.go()
