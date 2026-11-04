from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

OUT = Path(sys.argv[1])
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 680, 320
FPS = 10
SECONDS = 4.8
TOTAL = int(FPS * SECONDS)

BG = (244, 243, 237, 255)
INK = (24, 28, 32, 255)
MUTED = (108, 112, 118, 255)
LINE = (193, 196, 199, 255)
ACCENT = (241, 95, 35, 255)

FONT_DIR = Path(".github/fonts")
title_font = ImageFont.truetype(str(FONT_DIR / "IBMPlexSansCondensed-Bold.ttf"), 66)
name_font = ImageFont.truetype(str(FONT_DIR / "IBMPlexSansCondensed-Regular.ttf"), 30)
sub_font = ImageFont.truetype(str(FONT_DIR / "IBMPlexMono-Medium.ttf"), 25)
small_font = ImageFont.truetype(str(FONT_DIR / "IBMPlexMono-Regular.ttf"), 18)
tiny_font = ImageFont.truetype(str(FONT_DIR / "IBMPlexMono-Regular.ttf"), 13)

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def seg(t, a, b):
    return smooth((t - a) / (b - a))

def text_img(text, font, color):
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=color)
    return img

def paste_reveal(base, layer, xy, reveal=1.0, alpha=1.0, y_shift=0):
    if reveal <= 0 or alpha <= 0:
        return
    reveal = max(0.0, min(1.0, reveal))
    alpha = max(0.0, min(1.0, alpha))
    w = max(1, int(layer.width * reveal))
    crop = layer.crop((0, 0, w, layer.height))
    if alpha < 1.0:
        crop = crop.copy()
        crop.putalpha(crop.getchannel("A").point(lambda p: int(p * alpha)))
    base.alpha_composite(crop, (xy[0], xy[1] + y_shift))

def draw_scaffold(img):
    d = ImageDraw.Draw(img)

    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=14, outline=LINE, width=2)
    d.line((40, 48, W - 30, 48), fill=LINE, width=1)
    d.line((40, 85, W - 30, 85), fill=LINE, width=1)
    d.line((40, 266, W - 30, 266), fill=LINE, width=1)
    d.line((505, 15, 505, H - 24), fill=LINE, width=1)

    # top-left crosshair
    d.line((20, 24, 34, 24), fill=MUTED, width=1)
    d.line((27, 17, 27, 31), fill=MUTED, width=1)
    d.ellipse((21, 18, 33, 30), outline=MUTED, width=1)

    # bottom-right crosshair
    d.line((W - 46, H - 24, W - 18, H - 24), fill=MUTED, width=1)
    d.line((W - 32, H - 38, W - 32, H - 10), fill=MUTED, width=1)

    d.text((45, 20), "01 / 02", font=tiny_font, fill=MUTED)
    d.text((W - 97, 20), "PROFILE", font=tiny_font, fill=MUTED)

def build_full():
    im = Image.new("RGBA", (W, H), BG)
    draw_scaffold(im)
    d = ImageDraw.Draw(im)

    d.rectangle((58, 110, 66, 205), fill=ACCENT)

    d.text((86, 92), "GALEN MUI", font=name_font, fill=INK)
    d.text((86, 112), "ASIC DESIGN", font=title_font, fill=INK)
    d.text((89, 206), "COMPUTER ARCHITECTURE", font=sub_font, fill=(70, 74, 79, 255))
    d.text((44, 278), "RTL / SystemVerilog / VLSI", font=small_font, fill=MUTED)

    return im

STATIC = build_full()

name_layer = text_img("GALEN MUI", name_font, INK)
title_layer = text_img("ASIC DESIGN", title_font, INK)
sub_layer = text_img("COMPUTER ARCHITECTURE", sub_font, (70, 74, 79, 255))
foot_layer = text_img("RTL / SystemVerilog / VLSI", small_font, MUTED)

def frame(i):
    t = i / FPS

    # hold nice still frame first
    if t < 1.0:
        return STATIC.copy()

    t -= 1.0

    im = Image.new("RGBA", (W, H), BG)
    draw_scaffold(im)
    d = ImageDraw.Draw(im)

    bar = seg(t, 0.05, 0.35)
    if bar > 0:
        h = int(95 * bar)
        d.rectangle((58, 205 - h, 66, 205), fill=ACCENT)

    n = seg(t, 0.15, 0.55)
    paste_reveal(im, name_layer, (86, 92), reveal=n, alpha=n, y_shift=round(8 * (1 - n)))

    ti = seg(t, 0.45, 1.05)
    paste_reveal(im, title_layer, (86, 112), reveal=ti, alpha=ti, y_shift=round(12 * (1 - ti)))

    su = seg(t, 1.08, 1.60)
    paste_reveal(im, sub_layer, (89, 206), reveal=su, alpha=su, y_shift=round(6 * (1 - su)))

    fo = seg(t, 1.45, 1.95)
    paste_reveal(im, foot_layer, (44, 278), reveal=fo, alpha=fo, y_shift=round(4 * (1 - fo)))

    # subtle moving registration tick while holding
    hold = seg(t, 1.95, 3.30)
    if hold > 0:
        x = int(518 + 105 * ((t - 1.95) / 1.35))
        x = max(518, min(W - 44, x))
        d.line((x, 58, x, 80), fill=(168, 171, 174, int(190 * hold)), width=1)

    return im

frames_rgba = [frame(i) for i in range(TOTAL)]
reference = STATIC.convert("RGB").quantize(colors=128, dither=0)
frames = [f.convert("RGB").quantize(palette=reference, dither=0) for f in frames_rgba]

durations = []
for i in range(TOTAL):
    durations.append(130 if i < FPS else int(1000 / FPS))

frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=durations,
    loop=0,
    optimize=False,
    disposal=2,
)

print(f"Generated {OUT}")
