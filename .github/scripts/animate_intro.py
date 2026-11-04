from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import sys

OUT = Path(sys.argv[1])
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 680, 320
FPS = 10
SECONDS = 4.8
TOTAL_FRAMES = int(FPS * SECONDS)

BG = (244, 243, 237, 255)
INK = (20, 23, 26, 255)
SUBTLE = (110, 114, 118, 255)
LINE = (188, 191, 194, 255)
ACCENT = (240, 93, 35, 255)

FONT_DIR = Path(".github/fonts")
plex_bold = FONT_DIR / "IBMPlexSansCondensed-Bold.ttf"
plex_regular = FONT_DIR / "IBMPlexSansCondensed-Regular.ttf"
mono_regular = FONT_DIR / "IBMPlexMono-Regular.ttf"
mono_medium = FONT_DIR / "IBMPlexMono-Medium.ttf"

fonts = {
    "title": ImageFont.truetype(str(plex_bold), 72),
    "name": ImageFont.truetype(str(plex_regular), 34),
    "subtitle": ImageFont.truetype(str(mono_medium), 30),
    "small": ImageFont.truetype(str(mono_regular), 18),
    "tiny": ImageFont.truetype(str(mono_regular), 14),
}

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def segment(t, start, end):
    return smooth((t - start) / (end - start))

def text_image(text, font, color):
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=color)
    return img

def paste_reveal(base, layer, xy, reveal=1.0, alpha=1.0, y_offset=0):
    if reveal <= 0 or alpha <= 0:
        return
    reveal = max(0.0, min(1.0, reveal))
    alpha = max(0.0, min(1.0, alpha))
    w = max(1, int(layer.width * reveal))
    crop = layer.crop((0, 0, w, layer.height))
    if alpha < 1.0:
        crop = crop.copy()
        crop.putalpha(crop.getchannel("A").point(lambda p: int(p * alpha)))
    base.alpha_composite(crop, (xy[0], xy[1] + y_offset))

def draw_static_scaffold(img):
    d = ImageDraw.Draw(img)

    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=14, outline=LINE, width=2)
    d.line((38, 48, W - 30, 48), fill=LINE, width=1)
    d.line((38, 85, W - 30, 85), fill=LINE, width=1)
    d.line((38, 265, W - 30, 265), fill=LINE, width=1)
    d.line((505, 18, 505, H - 24), fill=LINE, width=1)

    # small top-left crosshair
    d.line((20, 24, 34, 24), fill=SUBTLE, width=1)
    d.line((27, 17, 27, 31), fill=SUBTLE, width=1)
    d.ellipse((21, 18, 33, 30), outline=SUBTLE, width=1)

    # small bottom-right crosshair
    d.line((W - 46, H - 24, W - 18, H - 24), fill=SUBTLE, width=1)
    d.line((W - 32, H - 38, W - 32, H - 10), fill=SUBTLE, width=1)

    # labels that remain visible from frame 1
    d.text((44, 20), "01 / 02", font=fonts["tiny"], fill=SUBTLE)
    d.text((W - 103, 20), "PROFILE", font=fonts["tiny"], fill=SUBTLE)

def draw_full_state():
    im = Image.new("RGBA", (W, H), BG)
    draw_static_scaffold(im)
    d = ImageDraw.Draw(im)

    # left accent bar
    d.rectangle((58, 114, 66, 208), fill=ACCENT)

    # static text so frame 1 already looks good
    d.text((86, 95), "GALEN MUI", font=fonts["name"], fill=INK)
    d.text((86, 118), "ASIC DESIGN", font=fonts["title"], fill=INK)
    d.text((89, 210), "COMPUTER ARCHITECTURE", font=fonts["subtitle"], fill=INK)
    d.text((44, 276), "RTL / SystemVerilog / VLSI", font=fonts["small"], fill=SUBTLE)

    # right-side detail
    d.text((530, 96), "focus", font=fonts["tiny"], fill=SUBTLE)
    d.text((530, 120), "digital hardware", font=fonts["small"], fill=INK)
    d.text((530, 152), "design from RTL", font=fonts["small"], fill=INK)
    d.text((530, 184), "to silicon", font=fonts["small"], fill=INK)

    return im

STATIC = draw_full_state()

name_layer = text_image("GALEN MUI", fonts["name"], INK)
title_layer = text_image("ASIC DESIGN", fonts["title"], INK)
subtitle_layer = text_image("COMPUTER ARCHITECTURE", fonts["subtitle"], INK)
footer_layer = text_image("RTL / SystemVerilog / VLSI", fonts["small"], SUBTLE)
focus1 = text_image("focus", fonts["tiny"], SUBTLE)
focus2 = text_image("digital hardware", fonts["small"], INK)
focus3 = text_image("design from RTL", fonts["small"], INK)
focus4 = text_image("to silicon", fonts["small"], INK)

def frame_at(index):
    t = index / FPS

    # First second: just hold the nice still frame
    if t < 0.9:
        return STATIC.copy()

    # Then restart the reveal sequence from a minimal scaffold
    local = t - 0.9
    im = Image.new("RGBA", (W, H), BG)
    draw_static_scaffold(im)
    d = ImageDraw.Draw(im)

    # accent bar animates in
    bar = segment(local, 0.10, 0.45)
    if bar > 0:
        h = int(94 * bar)
        d.rectangle((58, 208 - h, 66, 208), fill=ACCENT)

    # name
    n = segment(local, 0.18, 0.62)
    paste_reveal(im, name_layer, (86, 95), reveal=n, alpha=n, y_offset=round(10 * (1 - n)))

    # title
    tt = segment(local, 0.52, 1.12)
    paste_reveal(im, title_layer, (86, 118), reveal=tt, alpha=tt, y_offset=round(14 * (1 - tt)))

    # subtitle
    st = segment(local, 1.10, 1.72)
    paste_reveal(im, subtitle_layer, (89, 210), reveal=st, alpha=st, y_offset=round(8 * (1 - st)))

    # footer
    ft = segment(local, 1.55, 2.05)
    paste_reveal(im, footer_layer, (44, 276), reveal=ft, alpha=ft, y_offset=round(6 * (1 - ft)))

    # right-side details
    r1 = segment(local, 1.35, 1.75)
    r2 = segment(local, 1.50, 1.95)
    r3 = segment(local, 1.65, 2.10)
    r4 = segment(local, 1.80, 2.25)

    paste_reveal(im, focus1, (530, 96), reveal=r1, alpha=r1)
    paste_reveal(im, focus2, (530, 120), reveal=r2, alpha=r2)
    paste_reveal(im, focus3, (530, 152), reveal=r3, alpha=r3)
    paste_reveal(im, focus4, (530, 184), reveal=r4, alpha=r4)

    # subtle scanning line during hold
    hold = segment(local, 2.25, 3.50)
    if hold > 0:
        scan_x = int(38 + (W - 80) * ((math.sin((local - 2.1) * 1.8) + 1) / 2))
        d.line((scan_x, 56, scan_x, 78), fill=(220, 222, 225, int(150 * hold)), width=1)

    return im

# Build frames
frames_rgba = [frame_at(i) for i in range(TOTAL_FRAMES)]

# Stable palette
reference = STATIC.convert("RGB").quantize(colors=128, dither=0)
frames = [
    f.convert("RGB").quantize(palette=reference, dither=0)
    for f in frames_rgba
]

durations = []
for i in range(TOTAL_FRAMES):
    if i < int(0.9 * FPS):
        durations.append(120)  # longer hold on opening still
    else:
        durations.append(int(1000 / FPS))

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
