from pathlib import Path
from PIL import Image, ImageSequence
import sys

path = Path(sys.argv[1])

# Smaller fish, bigger swimming circle
FISH_SCALE = 0.52
SWIM_RADIUS = 1.60
PADDING = 46

placed = []
bounds_all = None

with Image.open(path) as gif:
    w, h = gif.size
    default_duration = gif.info.get("duration", 67)

    for frame in ImageSequence.Iterator(gif):
        rgba = frame.convert("RGBA")
        box = rgba.getchannel("A").getbbox()
        if box is None:
            continue

        fish = rgba.crop(box)
        fish = fish.resize(
            (
                max(1, round(fish.width * FISH_SCALE)),
                max(1, round(fish.height * FISH_SCALE)),
            ),
            Image.Resampling.NEAREST,
        )

        cx = w / 2 + ((box[0] + box[2]) / 2 - w / 2) * SWIM_RADIUS
        cy = h / 2 + ((box[1] + box[3]) / 2 - h / 2) * SWIM_RADIUS

        x = round(cx - fish.width / 2)
        y = round(cy - fish.height / 2)

        placed.append((fish, x, y, frame.info.get("duration", default_duration)))
        current = (x, y, x + fish.width, y + fish.height)

        if bounds_all is None:
            bounds_all = current
        else:
            bounds_all = (
                min(bounds_all[0], current[0]),
                min(bounds_all[1], current[1]),
                max(bounds_all[2], current[2]),
                max(bounds_all[3], current[3]),
            )

if not placed:
    raise SystemExit("No visible koi frames found")

x0, y0, x1, y1 = bounds_all

side = max(x1 - x0, y1 - y0) + 2 * PADDING
left = round((x0 + x1 - side) / 2)
top = round((y0 + y1 - side) / 2)

frames = []
durations = []

for fish, x, y, duration in placed:
    canvas = Image.new("RGBA", (side, side))
    canvas.paste(fish, (x - left, y - top))

    colors = sorted({
        color[:3]
        for _, color in canvas.getcolors(side * side)
        if color[3] != 0
    })

    if len(colors) > 255:
        raise SystemExit("Too many GIF colors")

    lookup = {color: index + 1 for index, color in enumerate(colors)}

    indexed = Image.new("P", (side, side))
    palette = [0, 0, 0]
    palette += [value for color in colors for value in color]
    palette += [0] * (768 - len(palette))

    indexed.putpalette(palette)
    indexed.putdata([
        lookup[pixel[:3]] if pixel[3] else 0
        for pixel in canvas.getdata()
    ])
    indexed.info["transparency"] = 0

    frames.append(indexed)
    durations.append(duration)

frames[0].save(
    path,
    save_all=True,
    append_images=frames[1:],
    loop=0,
    duration=durations,
    disposal=2,
    transparency=0,
    optimize=False,
)

print(f"Resized koi: {w}x{h} -> {side}x{side}")
