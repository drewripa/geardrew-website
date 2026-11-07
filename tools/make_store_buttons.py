"""Voxel store buttons for the game pages: a chunky slab with a raised play arrow and pixel-font text,
yellow "DEMO" and green "BUY", both the same size, rendered like the studio logo (make_logo.py).

    python tools/make_store_buttons.py        # writes assets/img/btn-demo.png and assets/img/btn-buy.png
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from make_logo import render

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "assets", "fonts", "GeardrewPixel.ttf")
OUT = os.path.join(HERE, "..", "assets", "img")

H = 30                  # slab height in voxels
PAD = 7                 # margin round the arrow and the text
GAP = 6                 # between the arrow and the text
ARROW = 16              # play arrow height
SLAB = range(3, 8)      # slab depth (y; the camera looks along +y, so smaller y is nearer)
RAISED = range(0, 3)    # arrow and letters stand out of the slab's face
BORDER = 1              # black border round the arrow and letters, in voxels
BORDER_COLOR = (22, 16, 12)
BUTTONS = {
    "demo": ("DEMO", (247, 196, 46), (255, 250, 232)),
    "buy": ("BUY", (88, 186, 82), (250, 250, 240)),
}


def text_mask(text):
    """The word in Geardrew Pixel, 2 voxels per font pixel (one font pixel = 92/1000 em)."""
    font = ImageFont.truetype(FONT, 2 * 1000 / 92)
    img = Image.new("L", (200, 40))
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    d.text((2, 2), text, font=font, fill=255)
    return np.array(img.crop(img.getbbox())) > 127


def arrow_mask(h):
    w = (h + 1) // 2 + 2
    m = np.zeros((h, w), bool)
    for r in range(h):
        reach = min(r, h - 1 - r) / ((h - 1) / 2)          # 0 at the tips, 1 in the middle
        m[r, : max(1, round(reach * w))] = True
    return m


def build(word, face, ink, width):
    tm = text_mask(word)
    am = arrow_mask(ARROW)
    X, Z, Y = width, H, max(SLAB) + 1
    occ = np.zeros((X, Y, Z), bool)
    pid = np.zeros((X, Y, Z), np.int16)
    col = np.zeros((X, Y, Z, 3), np.float32)
    face, ink = np.array(face, float), np.array(ink, float)
    for x in range(X):
        for z in range(Z):
            # rounded corners: knock out a little staircase at each corner
            cx, cz = min(x, X - 1 - x), min(z, Z - 1 - z)
            if cx + cz < 3:
                continue
            shade = 1.08 if z >= Z - 4 else (0.9 if z < 4 else 1.0)    # lighter top lip, darker bottom
            for y in SLAB:
                occ[x, y, z], pid[x, y, z], col[x, y, z] = True, 1, face * shade
    # the play arrow, then the word, centred together on the slab's face
    total = am.shape[1] + GAP + tm.shape[1]
    x0 = (X - total) // 2

    def stamp(mask, left, part):
        h = mask.shape[0]
        z_top = (Z + h) // 2                     # mask row 0 is the top
        # a one-voxel black border round the shape, just under it, so the letters read at a glance
        ring = np.pad(mask, BORDER)
        for _ in range(BORDER):
            ring = ring | np.roll(ring, 1, 0) | np.roll(ring, -1, 0) | np.roll(ring, 1, 1) | np.roll(ring, -1, 1)
        for r in range(ring.shape[0]):
            for c in range(ring.shape[1]):
                if ring[r, c]:
                    x, z = left + c - BORDER, z_top - 1 - r + BORDER
                    for y in range(RAISED.start + 1, RAISED.stop):
                        occ[x, y, z], pid[x, y, z], col[x, y, z] = True, 4, BORDER_COLOR
        for r in range(h):
            for c in range(mask.shape[1]):
                if mask[r, c]:
                    for y in RAISED:
                        occ[left + c, y, z_top - 1 - r] = True
                        pid[left + c, y, z_top - 1 - r] = part
                        col[left + c, y, z_top - 1 - r] = ink

    stamp(am, x0, 2)
    stamp(tm, x0 + am.shape[1] + GAP, 3)
    return occ, pid, col


def main():
    width = max(arrow_mask(ARROW).shape[1] + GAP + text_mask(w).shape[1] for w, _, _ in BUTTONS.values()) + 2 * PAD
    for name, (word, face, ink) in BUTTONS.items():
        img = render(*build(word, face, ink, width), ppv=2.07, view=(-0.2, 1.0, -0.22), outline=1)
        img = img.crop(img.getbbox())
        img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
        img.save(os.path.join(OUT, f"btn-{name}.png"))
        print(name, img.size)


if __name__ == "__main__":
    main()
