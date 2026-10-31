import csv
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

W = H = 128
BUNDLED_FONT = Path(__file__).parent / 'fonts' / 'DejaVuSans.ttf'


def get_font(size, path=None):
    for name in (path, BUNDLED_FONT, 'DejaVuSans.ttf', 'Arial.ttf'):
        if name:
            try:
                return ImageFont.truetype(str(name), size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_HEADER = get_font(8)
FONT_ICON = get_font(13)
FONT_SMALL = get_font(7)


def text_fit(draw, text, font, width):
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    while text and draw.textbbox((0, 0), text, font=font)[2] > width:
        text = text[:-1]
    return text


def draw_icon(draw, icon, cx, cy, font):
    
    white = 1
    if icon in ('▲', '⬆'):
        draw.polygon((cx, cy-7, cx-8, cy+6, cx+8, cy+6), fill=white)
    elif icon == '⏵':
        draw.polygon((cx-7, cy-7, cx+8, cy, cx-7, cy+7), fill=white)
    elif icon == '⏸':
        draw.rectangle((cx-6, cy-7, cx-2, cy+7), fill=white)
        draw.rectangle((cx+2, cy-7, cx+6, cy+7), fill=white)
    elif icon == '⏹':
        draw.rectangle((cx-7, cy-7, cx+7, cy+7), fill=white)
    elif icon == '⏭':
        draw.polygon((cx-10, cy-7, cx-1, cy, cx-10, cy+7), fill=white)
        draw.polygon((cx-1, cy-7, cx+8, cy, cx-1, cy+7), fill=white)
        draw.rectangle((cx+9, cy-7, cx+11, cy+7), fill=white)
    elif icon == '⏮':
        draw.rectangle((cx-11, cy-7, cx-9, cy+7), fill=white)
        draw.polygon((cx-8, cy, cx+1, cy-7, cx+1, cy+7), fill=white)
        draw.polygon((cx+1, cy, cx+10, cy-7, cx+10, cy+7), fill=white)
    elif icon == '✂':
        draw.ellipse((cx-9, cy+2, cx-3, cy+8), outline=white, width=2)
        draw.ellipse((cx+3, cy+2, cx+9, cy+8), outline=white, width=2)
        draw.line((cx-5, cy+2, cx+8, cy-8), fill=white, width=2)
        draw.line((cx+5, cy+2, cx-8, cy-8), fill=white, width=2)
    elif icon in ('⬅', '⬇', '➡'):
        if icon == '⬅':
            draw.polygon((cx-8,cy, cx+8,cy-7, cx+8,cy+7), fill=white)
        elif icon == '➡':
            draw.polygon((cx+8,cy, cx-8,cy-7, cx-8,cy+7), fill=white)
        else:
            draw.polygon((cx,cy+8, cx-8,cy-7, cx+8,cy-7), fill=white)
    else:
        displayed = text_fit(draw, icon or '·', font, 33)
        box = draw.textbbox((0, 0), displayed, font=font)
        draw.text((cx - (box[2]-box[0])//2, cy - 7), displayed,
                  font=font, fill=white)


def make_screen(profile, layer, keys, layer_index, layer_total, project_dir=None):
    image = Image.new('1', (W, H), 0)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 15, 127, 16), fill=1)
    heading = text_fit(d, '{} / {}'.format(profile, layer), FONT_HEADER, 98)
    d.text((3, 2), heading, font=FONT_HEADER, fill=1)
    counter = '{}/{}'.format(layer_index + 1, layer_total)
    d.text((106, 2), counter, font=FONT_HEADER, fill=1)
    for index in range(12):
        key = keys[index] if index < len(keys) else {}
        col, row = divmod(index, 4)  
        x, y = 1 + 42*col, 18 + 27*row
        d.rectangle((x, y, x+40, y+25), outline=1, width=1)
        icon = str(key.get('icon') or str(index + 1))
        icon_path = (Path(project_dir) / icon) if project_dir and icon else None
        if icon_path is not None and icon_path.is_file() and icon_path.suffix.lower() in ('.png','.jpg','.jpeg','.bmp'):
            with Image.open(icon_path) as original:
                small = ImageOps.contain(original.convert('L'), (17, 15)).convert('1')
            image.paste(small, (x + (41-small.width)//2, y + 2))
        else:
            draw_icon(d, icon, x+20, y+9, FONT_ICON)
        title = text_fit(d, key.get('title', ''), FONT_SMALL, 37)
        box = d.textbbox((0, 0), title, font=FONT_SMALL)
        d.text((x+20-(box[2]-box[0])//2, y+17), title, font=FONT_SMALL, fill=1)
    stream = io.BytesIO()
    image.save(stream, format='BMP')
    return stream.getvalue(), image


def render_all(data, project_dir=None):
    
    for pi, (profile, layers) in enumerate(data.items()):
        for li, (layer, keys) in enumerate(layers.items()):
            blob, image = make_screen(profile, layer, keys, li, len(layers), project_dir)
            yield 'screen:{}:{}'.format(pi, li), blob, image


def read_csv_for_preview(path):
    data = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            keys = data.setdefault(row['profile'], {}).setdefault(row['layer'],
                    [{'icon':'','title':'','shortcut':''} for _ in range(12)])
            try:
                idx = int(row['key']) - 1
            except (ValueError, TypeError):
                continue
            if 0 <= idx < 12:
                keys[idx] = {k:row.get(k,'') for k in ('icon','title','shortcut')}
    return data


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    data = read_csv_for_preview(root / 'orbitpad_config.csv')
    out = root / 'previews'
    out.mkdir(exist_ok=True)
    for name, blob, image in render_all(data, root):
        path = out / (name.replace(':','_') + '.png')
        image.resize((512,512), Image.Resampling.NEAREST).save(path)
        print(path.name, 'BMP bytes:', len(blob))
