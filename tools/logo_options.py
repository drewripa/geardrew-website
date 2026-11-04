"""Simplified GearDrew logos for small sizes (favicon, header, app icons).

Same idea as make_logo.py (half metal gear + plank D) with far fewer, bigger voxels. Each option is
rendered natively at 16, 32 and 64 px tall (no scaling), so what you see is what the icon gets.

    python tools/logo_options.py OUT_DIR     # writes OUT_DIR/<option>-<size>.png and OUT_DIR/sheet.png
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

from make_logo import render

OPTIONS = {
    # name: gear radius, tooth length, teeth round a full circle, axle bore, raised hub radius (0 = none),
    #       D stem width, bowl thickness, plank height (0 = one solid piece), camera
    "A-simple": dict(R=10, tooth=3, teeth=10, bore=3, hub=5.5, stem=3, bowl=4.5, plank=3, view=(-0.34, 1, -0.3)),
    "B-chunky": dict(R=7, tooth=3, teeth=6, bore=2, hub=0, stem=2, bowl=3, plank=3, view=(-0.34, 1, -0.3)),
    "C-front": dict(R=10, tooth=3, teeth=10, bore=3, hub=5.5, stem=3, bowl=4.5, plank=3, view=(-0.16, 1, -0.14)),
    "D-icon": dict(R=7, tooth=3, teeth=6, bore=2, hub=0, stem=2, bowl=3, plank=0, view=(-0.16, 1, -0.14)),
}
METAL = np.array([172, 180, 194])
WOOD = np.array([196, 124, 58])


def build(R, tooth, teeth, bore, hub, stem, bowl, plank, **_):
    rng = random.Random(3)
    tip = R + tooth
    n = 2 * math.ceil(tip) + 4
    X, Y, Z = n, 7, n
    O = n // 2
    occ = np.zeros((X, Y, Z), bool)
    pid = np.zeros((X, Y, Z), np.int16)
    col = np.zeros((X, Y, Z, 3), np.float32)
    tones = {}
    for x in range(X):
        for z in range(Z):
            wx, wz = x - O + 0.5, z - O + 0.5
            r, ang = math.hypot(wx, wz), math.atan2(wz, wx)
            if wx < 0:
                on_tooth = R - 0.5 < r <= tip and math.cos(teeth * (ang - math.pi)) > 0.2
                if r < bore or not (r <= R + 0.5 or on_tooth):
                    continue
                raised = hub and r <= hub
                ys = range(0, 6) if raised else range(1, 5)
                shine = 0.16 * math.cos((wx - wz) * 0.35)
                for y in ys:
                    occ[x, y, z], pid[x, y, z] = True, 2 if raised else 1
                    col[x, y, z] = METAL * (1 + shine) * (0.92 if raised else 1)
            else:
                if r > tip or (wx >= stem and r <= tip - bowl):
                    continue
                if plank:
                    part = 10 if wx < stem else 20 + int((wz + tip) // plank)
                else:
                    part = 10
                tone = tones.setdefault(part, rng.uniform(0.9, 1.08))
                stripe = 0.9 if plank == 0 and int((wz + tip) // 3) % 2 else 1.0   # plank hint without lines
                for y in range(1, 5):
                    occ[x, y, z], pid[x, y, z] = True, part
                    col[x, y, z] = WOOD * tone * stripe
    return occ, pid, col


def render_size(model, view, target):
    """Render so the logo itself (outline included) is `target` px on its longer side, centred in a square."""
    ppv = target / model[0].shape[2]
    for _ in range(8):
        img = render(*model, ppv=ppv, view=view, outline=1)
        img = img.crop(img.getbbox())
        if max(img.size) == target:
            break
        ppv *= (target - 0.5) / max(img.size) if max(img.size) > target else (target + 0.5) / max(img.size)
    img.thumbnail((target, target), Image.NEAREST)
    sq = Image.new("RGBA", (target, target))
    sq.paste(img, ((target - img.width) // 2, (target - img.height) // 2))
    return sq


def pixel_icon(size):
    """Option E: drawn straight onto the pixel grid, a flat front with a short extruded edge."""
    ext = max(1, size // 16)                     # extrusion depth, down-right
    line = 1 if size < 64 else 2
    c = (size - ext) / 2
    tip = c - line - 0.2
    R = tip * (0.66 if size < 32 else 0.74)
    stem = max(1, round(tip * 0.22))
    bowl = tip * 0.36

    def part(px, py):
        """0 empty, 1 metal, 2 wood, 3 axle hole (empty, but drawn dark)."""
        wx, wz = px + 0.5 - c, c - (py + 0.5)
        r, ang = math.hypot(wx, wz), math.atan2(wz, wx)
        if wx < 0:
            if size >= 32 and r < R * 0.32:
                return 3
            tooth = r <= tip and math.cos(6 * (ang - math.pi)) > 0.35
            return 1 if r <= R or tooth else 0
        if r > tip or (wx >= stem and r <= tip - bowl):
            return 0
        return 2

    grid = [[part(x, y) for x in range(size)] for y in range(size)]
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            p = grid[y][x]
            if p in (1, 2):
                wx, wz = x + 0.5 - c, c - (y + 0.5)
                light = 1 + 0.18 * (wz - wx) / tip                 # light from the top left
                if p == 1:
                    rgb = METAL * light
                else:
                    plank_h = max(2, size // 8)
                    seam = size >= 32 and wx >= stem and int((y + 0.5) // plank_h) != int((y + 1.5) // plank_h)
                    rgb = WOOD * light * (0.62 if seam else 1)
                if size >= 32 and 0 <= wx < 1:
                    rgb = np.array(OUTLINE_RGB)                     # seam between gear and D
                px[x, y] = (*np.clip(rgb, 0, 255).astype(int), 255)
            elif p == 3:
                px[x, y] = (*OUTLINE_RGB, 255)
            else:
                # Extruded side: something sits up-left of this pixel within the extrusion depth.
                for k in range(1, ext + 1):
                    if 0 <= x - k and 0 <= y - k and grid[y - k][x - k] in (1, 2):
                        base = METAL if grid[y - k][x - k] == 1 else WOOD
                        px[x, y] = (*(base * 0.55).astype(int), 255)
                        break
    a = np.array(img)
    shape = a[..., 3] > 0
    grown = shape.copy()
    for _ in range(line):
        grown = grown | np.roll(grown, 1, 0) | np.roll(grown, -1, 0) | np.roll(grown, 1, 1) | np.roll(grown, -1, 1)
    a[grown & ~shape] = (*OUTLINE_RGB, 255)
    return Image.fromarray(a, "RGBA")


OUTLINE_RGB = (14, 11, 18)


def main(out):
    os.makedirs(out, exist_ok=True)
    rows = []
    for name, cfg in OPTIONS.items():
        model = build(**cfg)
        imgs = {s: render_size(model, cfg["view"], s) for s in (16, 32, 64)}
        for s, im in imgs.items():
            im.save(os.path.join(out, f"{name}-{s}.png"))
        rows.append((name, imgs))
    imgs = {s: pixel_icon(s) for s in (16, 32, 64)}
    for s, im in imgs.items():
        im.save(os.path.join(out, f"E-pixel-{s}.png"))
    rows.append(("E-pixel", imgs))

    # Comparison sheet: real sizes on the site's dark background and on white, then 64 px blown up 4x.
    dark, light, grey = (20, 18, 28), (240, 238, 232), (92, 86, 110)
    cols = [("16", dark, 16), ("32", dark, 32), ("64", dark, 64), ("16 light", light, 16), ("32 light", light, 32)]
    cell, big = 84, 276
    sheet = Image.new("RGB", (120 + cell * len(cols) + big, 34 + len(rows) * big), (36, 33, 48))
    d = ImageDraw.Draw(sheet)
    for i, (head, _, _) in enumerate(cols):
        d.text((120 + cell * i + 8, 10), head + " px", fill=(200, 196, 210))
    d.text((120 + cell * len(cols) + 10, 10), "64 px x4", fill=(200, 196, 210))
    for r, (name, imgs) in enumerate(rows):
        y = 34 + r * big
        d.text((10, y + big // 2 - 6), name, fill=(236, 232, 244))
        for i, (_, bg, s) in enumerate(cols):
            x0 = 120 + cell * i
            d.rectangle((x0, y + big // 2 - 38, x0 + cell - 8, y + big // 2 + 38), fill=bg)
            sheet.paste(imgs[s], (x0 + (cell - 8 - s) // 2, y + big // 2 - s // 2), imgs[s])
        x0 = 120 + cell * len(cols)
        d.rectangle((x0 + 4, y + 6, x0 + 4 + 268, y + 6 + 268), fill=grey)
        z = imgs[64].resize((256, 256), Image.NEAREST)
        sheet.paste(z, (x0 + 10, y + 12), z)
    sheet.save(os.path.join(out, "sheet.png"))
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
