from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

OUT = Path(sys.argv[1])
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 680, 320
FPS, SECONDS = 12, 6

BG = (244, 243, 237)
INK = (34, 42, 48)
MUTED = (86, 99, 111)
BORDER = (207, 211, 211)
BLUE = (102, 122, 143)
LIGHT_BLUE = (179, 195, 207)

FONT_DIR = Path(".github/fonts")

def text_layer(value, filename, preferred_size, max_width, color):
    size = preferred_size

    while size >= 15:
        font = ImageFont.truetype(str(FONT_DIR / filename), size)
        left, top, right, bottom = font.getbbox(value)

        if right - left <= max_width:
            break

        size -= 1

    width, height = right - left, bottom - top
    layer = Image.new("RGBA", (width + 2, height + 2))

    ImageDraw.Draw(layer).text(
        (-left + 1, -top + 1),
        value,
        font=font,
        fill=(*color, 255)
    )

    return layer

name = text_layer(
    "GALEN MUI",
    "IBMPlexSansCondensed-Regular.ttf",
    34, 545, MUTED
)

headline = text_layer(
    "ASIC DESIGN",
    "IBMPlexSansCondensed-Bold.ttf",
    78, 555, INK
)

subtitle = text_layer(
    "Computer Architecture • DSP",
    "IBMPlexMono-Regular.ttf",
    27, 560, MUTED
)

items = [
    (name, (58, 67), (1.65, 2.16)),
    (headline, (58, 120), (2.05, 2.86)),
    (subtitle, (58, 233), (2.96, 3.66)),
]

# Check that text regions do not overlap
assert 67 + name.height + 15 < 120
assert 120 + headline.height + 14 < 203
assert 233 + subtitle.height < H - 35
assert all(x + layer.width < W - 35
           for layer, (x, _), _ in items)

def smooth(v):
    v = max(0.0, min(1.0, v))
    return v * v * (3 - 2 * v)

def progress(t, start, end):
    # Display the completed card first
    if t < 1.05:
        return 1.0

    # Clear it smoothly before replaying
    if t < 1.42:
        return 1.0 - smooth((t - 1.05) / 0.37)

    return smooth((t - start) / (end - start))

def draw_frame(t):
    img = Image.new("RGBA", (W, H), (*BG, 255))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        (2, 2, W - 3, H - 3),
        radius=13,
        outline=(*BORDER, 255),
        width=2
    )

    # Two small blue blocks slide into place
    squares = progress(t, 1.55, 2.20)

    if squares > 0:
        offset = round((1 - squares) * 22)

        d.rectangle(
            (589 + offset, 69, 601 + offset, 81),
            fill=(*BLUE, 255)
        )

        d.rectangle(
            (609 + offset, 59, 632 + offset, 82),
            fill=(*LIGHT_BLUE, 255)
        )

    # Short underline expands horizontally
    line = progress(t, 2.60, 3.16)

    if line > 0:
        d.rectangle(
            (58, 204, 58 + round(112 * line), 209),
            fill=(*BLUE, 255)
        )

        if line > 0.70:
            d.rectangle(
                (177, 204,
                 177 + round(27 * smooth((line - .70) / .30)),
                 209),
                fill=(*LIGHT_BLUE, 255)
            )

    # Reveal each line of text independently
    for layer, (x, y), (start, end) in items:
        visible = progress(t, start, end)

        if visible > 0:
            width = max(1, round(layer.width * visible))
            part = layer.crop(
                (0, 0, width, layer.height)
            )
            img.alpha_composite(part, (x, y))

    return img.convert("RGB")

raw_frames = [
    draw_frame(i / FPS)
    for i in range(FPS * SECONDS)
]

# Stable GIF palette, compatible with older Pillow
reference = raw_frames[0].quantize(colors=128, dither=0)

frames = [
    im.quantize(palette=reference, dither=0)
    for im in raw_frames
]

frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=round(1000 / FPS),
    loop=0,
    optimize=True,
    disposal=2
)

print(f"Generated {OUT}: {W}x{H}")
