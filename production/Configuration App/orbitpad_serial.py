import base64
import binascii
import json
import os
import threading
import time

import serial
from serial.tools import list_ports

KNOWN_VIDS = {0x239A, 0x2E8A}  
CHUNK_SIZE = 192  


class SerialManager:
    BAUD = 115200  

    def __init__(self, on_status_change=None, on_device_status=None):
        self.on_status_change = on_status_change
        self.on_device_status = on_device_status
        self._lock = threading.RLock()
        self._serial = None
        self._port = None
        self.last_status = None
        self.last_error = ''
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()

    @property
    def port(self):
        return self._port

    def _candidates(self):
        override = os.environ.get('ORBITPAD_PORT', '').strip()
        if override:
            return [override]
        possible = []
        for info in list_ports.comports():
            desc = ((info.description or '') + ' ' + (getattr(info, 'interface', '') or '')).lower()
            if info.vid in KNOWN_VIDS or any(word in desc for word in
                    ('circuitpython', 'pico', 'usb serial', 'board cdc', 'orbitpad')):
                priority = 0 if 'data' in desc else 1
                possible.append((priority, info.device))
        return [name for _, name in sorted(possible)]

    @staticmethod
    def _request_on_port(port, obj, timeout=1.8):
        port.write((json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8'))
        expected = obj.get('cmd')
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            raw = port.readline()
            if not raw:
                continue
            try:
                message = json.loads(raw.decode('utf-8'))
            except (UnicodeError, ValueError):
                continue  
            if isinstance(message, dict) and message.get('cmd') == expected:
                return message
        return None

    def _notify(self, connected, name=''):
        if self.on_status_change:
            self.on_status_change(connected, name)

    def _disconnect_locked(self, notify=True):
        was_open = self._serial is not None
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial, self._port, self.last_status = None, None, None
        if was_open and notify:
            self._notify(False, '')

    def _try_port(self, name):
        candidate = None
        try:
            candidate = serial.Serial(name, self.BAUD, timeout=0.25,
                                      write_timeout=0.75)
            candidate.dtr = True  
            time.sleep(0.12)
            candidate.reset_input_buffer()
            hello = self._request_on_port(candidate, {'cmd': 'ping'}, timeout=1.5)
            if (hello is None or hello.get('status') != 'pong'
                    or hello.get('device') != 'OrbitPad' or hello.get('protocol') != 1):
                candidate.close()
                return False
            with self._lock:
                self._serial = candidate
                self._port = name
                self.last_status = hello
            self._notify(True, name)
            if self.on_device_status:
                self.on_device_status(hello)
            print('[Serial] OrbitPad on', name)
            return True
        except (OSError, serial.SerialException) as exc:
            if candidate is not None:
                try:
                    candidate.close()
                except Exception:
                    pass
            self.last_error = str(exc)
            return False

    def _watch(self):
        while not self._stop.is_set():
            if not self.is_connected():
                for name in self._candidates():
                    if self._stop.is_set() or self.is_connected():
                        break
                    self._try_port(name)
            else:
                status = self.request({'cmd': 'get_status'}, timeout=1.6)
                if status and status.get('status') == 'ok':
                    self.last_status = status
                    if self.on_device_status:
                        self.on_device_status(status)
            self._stop.wait(2.0)

    def request(self, obj, timeout=2.0):
        with self._lock:
            if not self.is_connected():
                self.last_error = 'OrbitPad disconnected'
                return None
            try:
                reply = self._request_on_port(self._serial, obj, timeout=timeout)
                if reply is None:
                    raise TimeoutError('No acknowledgment for ' + str(obj.get('cmd')))
                if reply.get('status') == 'error':
                    self.last_error = str(reply.get('msg', 'Device error'))
                else:
                    self.last_error = ''
                return reply
            except (OSError, serial.SerialException, TimeoutError) as exc:
                self.last_error = str(exc)
                print('[Serial] Lost connection:', exc)
                self._disconnect_locked()
                return None

    def send(self, obj):
        
        reply = self.request(obj, timeout=7.0)
        return bool(reply and reply.get('status') in ('ok', 'pong'))

    def is_connected(self):
        return self._serial is not None and self._serial.is_open

    def upload_bytes(self, name, content, on_progress=None):
        
        if not isinstance(content, bytes) or not content:
            raise ValueError('No data for upload')
        with self._lock:  
            begin = self.request({
                'cmd': 'begin_upload', 'name': name, 'size': len(content),
                'crc32': binascii.crc32(content) & 0xFFFFFFFF,
            }, timeout=3.0)
            if not begin or begin.get('status') != 'ok':
                raise RuntimeError(self.last_error or 'Upload not accepted')
            try:
                for offset in range(0, len(content), CHUNK_SIZE):
                    chunk = content[offset:offset+CHUNK_SIZE]
                    ack = self.request({
                        'cmd': 'upload_chunk', 'offset': offset,
                        'data': base64.b64encode(chunk).decode('ascii'),
                    }, timeout=3.0)
                    if not ack or ack.get('status') != 'ok' or ack.get('received') != offset+len(chunk):
                        raise RuntimeError(self.last_error or 'Chunk not acknowledged')
                    if on_progress:
                        on_progress(offset+len(chunk), len(content))
                finish = self.request({'cmd':'end_upload'}, timeout=4.0)
                if not finish or finish.get('status') != 'ok' or finish.get('bytes') != len(content):
                    raise RuntimeError(self.last_error or 'Upload commit failed')
                return True
            except Exception:
                if self.is_connected():
                    self.request({'cmd':'abort_upload'}, timeout=1.0)
                raise

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2.5)
        with self._lock:
            self._disconnect_locked(notify=False)
