from pathlib import Path
from io import BytesIO
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw
import cairosvg
import math
import re
import sys

OUT = Path(sys.argv[1])
OUT.parent.mkdir(parents=True, exist_ok=True)

# Exact same URL currently used by the README.
SOURCE = (
    "https://github-stats-extended.vercel.app/api/top-langs/"
    "?username=GalenMui"
    "&layout=compact"
    "&size_weight=0"
    "&count_weight=1"
    "&langs_count=6"
    "&custom_title=Languages%20by%20repo%20count"
    "&title_color=5b35b1"
    "&hide_border=true"
)

request = Request(
    SOURCE,
    headers={"User-Agent": "GalenMui-profile-animation"}
)

with urlopen(request, timeout=45) as response:
    svg = response.read()

if b"<svg" not in svg[:4000]:
    raise RuntimeError("Stats API did not return a valid SVG")

# Rasterize the original SVG, preserving its design.
png = cairosvg.svg2png(
    bytestring=svg,
    output_width=680
)

original = Image.open(BytesIO(png)).convert("RGBA")
full = Image.new("RGB", original.size, "white")
full.paste(original, mask=original.getchannel("A"))

W, H = full.size

# Keep the title always visible.
title_height = round(H * 0.34)

FPS = 12
DURATION = 5.5
TOTAL = round(FPS * DURATION)

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def frame(t):
    # Hold the original chart at the beginning.
    if t < 1.0:
        return full.copy()

    # Hide chart contents briefly before restarting.
    if t < 1.25:
        fraction = 1 - smooth((t - 1.0) / .25)
    else:
        # Reveal the existing chart horizontally.
        fraction = smooth((t - 1.25) / 1.5)

    if fraction >= 1:
        return full.copy()

    output = full.copy()
    draw = ImageDraw.Draw(output)

    draw.rectangle(
        (0, title_height, W, H),
        fill="white"
    )

    width = round(W * fraction)

    if width > 0:
        portion = full.crop(
            (0, title_height, width, H)
        )
        output.paste(portion, (0, title_height))

    return output

images = [
    frame(i / FPS)
    for i in range(TOTAL)
]

reference = full.quantize(colors=255, dither=0)

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
    disposal=2,
    optimize=True
)

print(f"Generated {OUT}")

# Switch to the GIF only after generation succeeds.
readme = Path("README.md")
text = readme.read_text()

text = re.sub(
    r'<img src="https://github-stats-extended'
    r'\.vercel\.app/api/top-langs/[^"]+"'
    r' width="340" alt="Languages by repo count" />',
    '<img src="assets/languages.gif" width="340" '
    'alt="Languages by repo count" />',
    text
)

readme.write_text(text)
