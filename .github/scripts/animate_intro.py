from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

OUT = Path(sys.argv[1])
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 680, 320
FPS = 12
FRAMES = 72

BG = (244, 243, 237)
INK = (24, 28, 32)
GREY = (82, 88, 93)
BORDER = (193, 196, 199)
ORANGE = (241, 95, 35)

FONT_DIR = Path(".github/fonts")

def make_text(content, filename, desired_size, max_width, rgb):
    size = desired_size

    while True:
        font = ImageFont.truetype(str(FONT_DIR / filename), size)
        bbox = font.getbbox(content)
        width = bbox[2] - bbox[0]

        if width <= max_width or size <= 12:
            break

        size -= 1

    height = bbox[3] - bbox[1]
    layer = Image.new("RGBA", (width + 2, height + 2))

    ImageDraw.Draw(layer).text(
        (-bbox[0], -bbox[1]),
        content,
        font=font,
        fill=(*rgb, 255),
    )

    return layer

name = make_text(
    "GALEN MUI",
    "IBMPlexSansCondensed-Regular.ttf",
    37, 560, GREY
)

headline = make_text(
    "ASIC DESIGN",
    "IBMPlexSansCondensed-Bold.ttf",
    100, 552, INK
)

subtitle = make_text(
    "COMPUTER ARCHITECTURE • DSP",
    "IBMPlexMono-Regular.ttf",
    30, 552, GREY
)

layers = [name, headline, subtitle]

# Fixed, nonoverlapping text locations
positions = [
    (70, 64),
    (70, 110),
    (70, 213),
]

assert positions[0][1] + name.height + 8 < positions[1][1]
assert positions[1][1] + headline.height + 12 < positions[2][1]
assert positions[2][1] + subtitle.height < H - 20

for (x, y), layer in zip(positions, layers):
    assert x + layer.width < W - 35

def smooth(v):
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)

def visible(t, start, end):
    # Begin with a complete, readable frame.
    if t < 1.65:
        return 1.0

    # Wipe text away before the next reveal.
    if t < 2.02:
        return 1.0 - smooth((t - 1.65) / 0.37)

    return smooth((t - start) / (end - start))

def render(t):
    im = Image.new("RGBA", (W, H), (*BG, 255))
    d = ImageDraw.Draw(im)

    d.rounded_rectangle(
        (2, 2, W - 3, H - 3),
        radius=15,
        outline=(*BORDER, 255),
        width=2,
    )

    d.rectangle(
        (46, 110, 54, 190),
        fill=(*ORANGE, 255),
    )

    schedules = [
        (2.13, 2.65),
        (2.42, 3.30),
        (3.13, 4.00),
    ]

    for layer, pos, schedule in zip(layers, positions, schedules):
        progress = visible(t, *schedule)

        if progress > 0:
            width = max(1, int(layer.width * progress))
            part = layer.crop((0, 0, width, layer.height))
            im.alpha_composite(part, pos)

    return im.convert("RGB")

images = [
    render(i / FPS)
    for i in range(FRAMES)
]

reference = images[0].quantize(colors=128, dither=0)

frames = [
    im.quantize(palette=reference, dither=0)
    for im in images
]

frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=round(1000 / FPS),
    loop=0,
    optimize=True,
    disposal=2,
)

print(f"Generated {OUT}")
