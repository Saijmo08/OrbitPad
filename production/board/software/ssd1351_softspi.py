import digitalio
import time

WIDTH = HEIGHT = 128
ROW_BYTES = 16  
_EMPTY_ROW = b'\x00' * ROW_BYTES
_RULE_ROW = b'\xff' * ROW_BYTES

_DIGITS = (
    (7, 5, 5, 5, 7), (2, 6, 2, 2, 7), (7, 1, 7, 4, 7),
    (7, 1, 7, 1, 7), (5, 5, 7, 1, 1), (7, 4, 7, 1, 7),
    (7, 4, 7, 5, 7), (7, 1, 1, 1, 1), (7, 5, 7, 5, 7),
    (7, 5, 7, 1, 7),
)

class _DirectSPI:
    def __init__(self, clock, mosi):
        self.clk = self.din = None
        try:
            self.clk = digitalio.DigitalInOut(clock)
            self.clk.switch_to_output(value=False)
            self.din = digitalio.DigitalInOut(mosi)
            self.din.switch_to_output(value=False)
            self.level = False
        except Exception:
            self.deinit()
            raise

    def write(self, data, start=0, end=None):
        din, clk = self.din, self.clk
        level = self.level
        if end is None:
            end = len(data)
        index = start
        while index < end:
            value = data[index]
            index += 1
            if value == 0 or value == 255:
                desired = value == 255
                if level != desired:
                    din.value = desired
                    level = desired
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
                clk.value = True
                clk.value = False
            else:
                mask = 0x80
                while mask:
                    desired = bool(value & mask)
                    if level != desired:
                        din.value = desired
                        level = desired
                    clk.value = True   
                    clk.value = False  
                    mask >>= 1
        self.level = level

    def deinit(self):
        for pin in (self.din, self.clk):
            if pin is not None:
                pin.deinit()
        self.din = self.clk = None


def _little(buf):
    result = 0
    for i, value in enumerate(buf):
        result |= value << (8 * i)
    return result


def _rgb565(color):
    r, g, b = color
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _set_pixel(line, x):
    line[x >> 3] |= 0x80 >> (x & 7)


def _digit_line(line, x, digit, scanline):
    bits = _DIGITS[digit][scanline]
    if bits & 4:
        _set_pixel(line, x)
    if bits & 2:
        _set_pixel(line, x + 1)
    if bits & 1:
        _set_pixel(line, x + 2)


class SSD1351SoftSPI:
    def __init__(self, clock, mosi, cs, dc, reset):
        self.spi = self.cs = self.dc = self.reset = None
        try:
            self.spi = _DirectSPI(clock, mosi)
            self.cs = digitalio.DigitalInOut(cs)
            self.cs.switch_to_output(value=True)
            self.dc = digitalio.DigitalInOut(dc)
            self.dc.switch_to_output(value=True)
            self.reset = digitalio.DigitalInOut(reset)
            self.reset.switch_to_output(value=True)
            self.reset.value = False
            time.sleep(0.02)
            self.reset.value = True
            time.sleep(0.05)
            self._init_display()
            self.set_color((255, 255, 255))
            self._expanded = bytearray(WIDTH * 2)  
            self._rows = None
            self._pos = WIDTH * 2
            self.rows_sent = 0
            self.drawing = False
        except Exception:
            for item in (self.spi, self.reset, self.dc, self.cs):
                if item is not None:
                    try:
                        item.deinit()
                    except Exception:
                        pass
            raise

    def _cmd(self, command, data=b''):
        self.cs.value = False
        try:
            self.dc.value = False
            self.spi.write(bytes((command,)))
            if data:
                self.dc.value = True
                self.spi.write(data)
        finally:
            self.cs.value = True

    def _init_display(self):
        for command, data in (
            (0xFD, b'\x12'), (0xFD, b'\xB1'), (0xAE, b''),
            (0xB2, b'\xA4\x00\x00'), (0xB3, b'\xF0'),
            (0xCA, b'\x7F'), (0xA2, b'\x00'), (0xB5, b'\x00'),
            (0xAB, b'\x01'), (0xB1, b'\x32'), (0xBE, b'\x05'),
            (0xA6, b''), (0xC1, b'\xC8\x80\xC8'), (0xC7, b'\x0F'),
            (0xB4, b'\xA0\xB5\x55'), (0xB6, b'\x01'),
            (0xA0, b'\x26'), (0xAF, b''),
        ):
            self._cmd(command, data)

    def set_color(self, rgb):
        
        if sum(rgb) < 24:  
            rgb = (255, 255, 255)
        ink = _rgb565(rgb)
        if getattr(self, '_ink', None) == ink:
            return  
        pixel_on = bytes((ink >> 8, ink & 0xFF))
        pixel_off = b'\x00\x00'
        
        
        self.lookup = tuple(b''.join(
            pixel_on if bits & (1 << shift) else pixel_off
            for shift in range(3, -1, -1)
        ) for bits in range(16))
        self._ink = ink

    def cancel(self):
        
        self.drawing = False
        self.cs.value = True
        if self._rows is not None:
            close = getattr(self._rows, 'close', None)
            if close is not None:
                close()
            self._rows = None
        self._pos = WIDTH * 2

    def _start_rows(self, rows):
        self.cancel()
        try:
            self._cmd(0x15, bytes((0, WIDTH - 1)))
            self._cmd(0x75, bytes((0, HEIGHT - 1)))
            self.cs.value = False
            self.dc.value = False
            self.spi.write(b'\x5c')  
            self.dc.value = True
            self._rows = iter(rows)
            self._pos = WIDTH * 2
            self.rows_sent = 0
            self.drawing = True
        except Exception:
            self.cancel()
            raise

    def tick(self, byte_budget=16):
        if not self.drawing:
            return False
        if byte_budget < 1:
            raise ValueError('byte_budget must be positive')
        try:
            if self._pos == WIDTH * 2:
                try:
                    row = next(self._rows)
                except StopIteration:
                    raise ValueError('Truncated 128-row OLED image')
                if len(row) != ROW_BYTES:
                    raise ValueError('Truncated BMP row')
                for n, value in enumerate(row):
                    pos = n * 16
                    self._expanded[pos:pos+8] = self.lookup[value >> 4]
                    self._expanded[pos+8:pos+16] = self.lookup[value & 15]
                self._pos = 0
                self.rows_sent += 1
            end = min(WIDTH * 2, self._pos + byte_budget)
            self.spi.write(self._expanded, self._pos, end)
            self._pos = end
            if self.rows_sent == HEIGHT and end == WIDTH * 2:
                self.cancel()
        except Exception:
            self.cancel()
            raise
        return self.drawing

    def _finish_sync(self):
        while self.tick(WIDTH * 2):
            pass

    def start_bmp(self, path):
        
        with open(path, 'rb') as f:
            head = f.read(54)
        if (len(head) != 54 or head[:2] != b'BM'
                or _little(head[18:22]) != WIDTH
                or _little(head[22:26]) != HEIGHT
                or _little(head[28:30]) != 1
                or _little(head[30:34]) != 0):
            raise ValueError('Expected uncompressed 128x128 1-bit BMP')
        start = _little(head[10:14])
        if start < 54:
            raise ValueError('Invalid BMP pixel offset')

        def rows():
            for y in range(HEIGHT - 1, -1, -1):
                with open(path, 'rb') as f:
                    f.seek(start + y * ROW_BYTES)
                    row = f.read(ROW_BYTES)
                yield row  
        self._start_rows(rows())

    def show_bmp(self, path):
        self.start_bmp(path)
        self._finish_sync()

    def start_placeholder(self, layer_index, layer_count):
        def rows():
            line = bytearray(ROW_BYTES)  
            for y in range(HEIGHT):
                line[:] = _EMPTY_ROW
                if 5 <= y < 10:
                    _digit_line(line, 102, (layer_index + 1) % 10, y - 5)
                    _digit_line(line, 116, layer_count % 10, y - 5)
                if y == 16:
                    line[:] = _RULE_ROW
                if 18 <= y <= 124:
                    tile_row = (y - 18) // 27
                    within = y - (18 + tile_row * 27)
                    if tile_row < 4 and within <= 25:
                        for col in range(3):
                            x = 1 + 42 * col
                            number = 1 + 4 * col + tile_row
                            if within == 0 or within == 25:
                                for xx in range(x, x + 41):
                                    _set_pixel(line, xx)
                            else:
                                _set_pixel(line, x)
                                _set_pixel(line, x + 40)
                            if 10 <= within < 15:
                                if number >= 10:
                                    _digit_line(line, x + 15, 1, within - 10)
                                    _digit_line(line, x + 20, number % 10,
                                                within - 10)
                                else:
                                    _digit_line(line, x + 19, number,
                                                within - 10)
                yield line
        self._start_rows(rows())

    def show_placeholder(self, layer_index, layer_count):
        self.start_placeholder(layer_index, layer_count)
        self._finish_sync()

    def deinit(self):
        self.cancel()
        for pin in (self.cs, self.dc, self.reset):
            pin.deinit()
        self.spi.deinit()
