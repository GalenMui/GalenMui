from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import sys

OUT = Path(sys.argv[1])
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 680, 348
FPS, SECONDS = 12, 5.5

FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
regular = FONT_DIR / 'DejaVuSans.ttf'
bold = FONT_DIR / 'DejaVuSans-Bold.ttf'

if not regular.exists():
    FONT_DIR = Path('/usr/share/fonts/truetype/liberation2')
    regular = FONT_DIR / 'LiberationSans-Regular.ttf'
    bold = FONT_DIR / 'LiberationSans-Bold.ttf'

fonts = {
    'name': ImageFont.truetype(str(bold), 55),
    'label': ImageFont.truetype(str(bold), 23),
    'small': ImageFont.truetype(str(regular), 24),
    'tiny': ImageFont.truetype(str(regular), 19),
}

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)

def opacity(t, begin):
    fade_in = smooth((t-begin)/0.48)
    fade_out = 1-smooth((t-4.75)/0.55)
    return fade_in * fade_out

def layer_text(img, xy, label, font, color, alpha, dy=0):
    if alpha <= 0:
        return
    layer = Image.new('RGBA', (W,H))
    dr = ImageDraw.Draw(layer)
    dr.text(
        (xy[0], xy[1]+dy),
        label,
        font=font,
        fill=(*color, round(255*alpha))
    )
    img.alpha_composite(layer)

def frame_at(t):
    im = Image.new('RGBA', (W,H), (12,17,28,255))
    d = ImageDraw.Draw(im)

    # Dark rounded window
    d.rounded_rectangle(
        (2,2,W-3,H-3),
        radius=24,
        outline=(58,69,93,255),
        width=2
    )
    d.line((36,65,W-36,65), fill=(48,62,84), width=2)

    # Window controls
    for i, col in enumerate([
        (245,107,117),
        (255,198,87),
        (87,209,145)
    ]):
        d.ellipse(
            (34+i*24,29,45+i*24,40),
            fill=col
        )

    d.text(
        (126,25),
        'galen / about',
        font=fonts['tiny'],
        fill=(143,160,185)
    )

    # Moving accent indicator
    d.rounded_rectangle(
        (530,31,641,38),
        radius=4,
        fill=(31,47,65)
    )

    k = (math.sin(2*math.pi*t/SECONDS-math.pi/2)+1)/2

    if k > 0:
        d.rounded_rectangle(
            (530,31,530+int(111*k),38),
            radius=4,
            fill=(94,196,245)
        )

    # Animated name
    a = opacity(t, 0.35)
    layer_text(
        im, (35,90), 'GALEN MUI',
        fonts['name'],
        (242,247,255),
        a,
        round(15*(1-a))
    )

    # Animated interest labels
    labels = [
        (164, 1.08, 'ASIC DESIGN', (191,147,255)),
        (210, 1.68, 'COMPUTER ARCHITECTURE', (125,213,243))
    ]

    for top, start, label, rgb in labels:
        a = opacity(t, start)
        shift = round(16*(1-a))

        layer = Image.new('RGBA', (W,H))
        dd = ImageDraw.Draw(layer)

        dd.rounded_rectangle(
            (35,top+shift,645,top+37+shift),
            radius=8,
            fill=(24,37,56,round(230*a))
        )

        dd.rectangle(
            (35,top+6+shift,39,top+31+shift),
            fill=(*rgb,round(255*a))
        )

        dd.text(
            (54,top+3+shift),
            label,
            font=fonts['label'],
            fill=(*rgb,round(255*a))
        )

        im.alpha_composite(layer)

    # Skills
    a = opacity(t, 2.34)
    layer_text(
        im,
        (36,277),
        'RTL  /  SystemVerilog  /  VLSI',
        fonts['small'],
        (198,210,229),
        a,
        round(12*(1-a))
    )

    # Education
    a = opacity(t, 2.67)
    layer_text(
        im,
        (36,315),
        'M.S.E. ECE  ·  UNIVERSITY OF MICHIGAN',
        fonts['tiny'],
        (130,148,171),
        a,
        round(8*(1-a))
    )

    return im.convert('RGB')

# Stable palette keeps colors consistent between frames
reference = frame_at(3.2).quantize(colors=128)

frames = []

for index in range(round(FPS*SECONDS)):
    image = frame_at(index/FPS)
    frames.append(
        image.quantize(
            palette=reference,
            dither=Image.Dither.NONE
        )
    )

frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=round(1000/FPS),
    loop=0,
    optimize=True,
    disposal=2
)

print(f'Generated {OUT}')
