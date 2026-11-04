"""Render the GearDrew logo: half a metal gear (left) joined to a wooden-plank letter D (right).

Builds the logo as voxels, ray-casts it from a slight isometric angle, shades the faces, adds
black pixel outlines and upscales with nearest-neighbour for a chunky pixel look.

    pip install numpy pillow
    python tools/make_logo.py            # writes assets/img/logo.png and assets/img/favicon.png
"""
import math
import os
import random

import numpy as np
from PIL import Image

R = 20                      # radius of the gear body, in voxels
TIP = R + 4.5               # gear tooth tips; the D's bowl is this big too
X, Y, Z = 58, 10, 58        # grid size; y is depth (camera looks along +y)
OX, OZ = 29, 29             # circle centre in the grid
OUTLINE = (14, 11, 18)

METAL = 1                   # part ids 1-9: gear pieces, 10+: planks
rng = random.Random(7)


def build():
    occ = np.zeros((X, Y, Z), bool)
    pid = np.zeros((X, Y, Z), np.int16)
    col = np.zeros((X, Y, Z, 3), np.float32)

    plank_tone = {}
    plank_front = {}
    for x in range(X):
        for z in range(Z):
            wx, wz = x - OX + 0.5, z - OZ + 0.5
            r = math.hypot(wx, wz)
            ang = math.atan2(wz, wx)

            if wx < 0:
                # Half gear: thick rim with teeth, thin web with two holes, thick hub round the axle.
                tooth = R - 0.5 < r <= TIP and math.cos(10 * (ang - math.pi)) > 0.25 + 0.04 * (r - R)
                hole = any(math.hypot(wx - 13 * math.cos(a), wz - 13 * math.sin(a)) < 3.6
                           for a in (math.radians(135), math.radians(225)))
                if r < 5.5 or hole:
                    continue
                if r <= 9.5:
                    ys, part = range(0, 8), 2          # hub sticks out toward the viewer
                elif r <= R - 3.5:
                    ys, part = range(3, 6), 1          # web
                elif r <= R + 0.5 or tooth:
                    ys, part = range(1, 7), 1          # rim and teeth
                else:
                    continue
                for y in ys:
                    shine = 0.18 * math.cos((wx - wz) * 0.16)    # soft diagonal sheen across the metal
                    base = np.array([150, 158, 170]) * (1 + shine + rng.uniform(-0.03, 0.03))
                    if part == 2 and r <= 6.5:
                        base *= 0.7                      # axle bore
                    occ[x, y, z], pid[x, y, z], col[x, y, z] = True, part, base
            else:
                # Letter D: two upright planks for the stem, horizontal planks for the bowl.
                if r > TIP:
                    continue
                if wx >= 6 and r <= TIP - 7.5:
                    continue                             # the D's counter
                if wx < 6:
                    plank = 10 + int(wx // 3)
                    along, across = wz, wx % 3
                else:
                    plank = 20 + int((wz + TIP) // 4)
                    along, across = wx, (wz + TIP) % 4
                if plank not in plank_tone:
                    plank_tone[plank] = rng.uniform(0.85, 1.12)
                    plank_front[plank] = rng.choice((1, 1, 2))   # slightly uneven planks
                for y in range(plank_front[plank], 6):
                    grain = 0.8 if (int(along * 0.5 + across * 2.3 + plank * 5) % 5 == 0) else 1.0
                    base = np.array([176, 116, 62]) * plank_tone[plank] * grain * rng.uniform(0.96, 1.04)
                    nail = (y == plank_front[plank] and abs(across - (1.5 if wx < 6 else 2)) < 0.6
                            and (abs(along - (7 if wx >= 6 else 15)) < 0.6
                                 or abs(along + (15 if wx < 6 else -100)) < 0.6))
                    if nail:
                        base = np.array([70, 72, 80])
                    occ[x, y, z], pid[x, y, z], col[x, y, z] = True, plank, base
    return occ, pid, col


def render(occ, pid, col, ppv, view=(-0.34, 1.0, -0.3), outline=2):
    X, Y, Z = occ.shape
    OX, OZ = X // 2, Z // 2
    f = np.array(view, float)
    f /= np.linalg.norm(f)
    right = np.cross(f, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)

    centre = np.array([OX, Y / 2, OZ])
    pts = np.argwhere(occ) + 0.5 - centre
    s, t = pts @ right, pts @ up
    pad = 4 / ppv
    s0, s1, t0, t1 = s.min() - 1 - pad, s.max() + 1 + pad, t.min() - 1 - pad, t.max() + 1 + pad
    w, h = int((s1 - s0) * ppv), int((t1 - t0) * ppv)

    ss = s0 + (np.arange(w) + 0.5) / ppv
    tt = t1 - (np.arange(h) + 0.5) / ppv
    S, T = np.meshgrid(ss, tt)
    L = 60.0
    origin = centre + S[..., None] * right + T[..., None] * up - L * f

    hit = np.zeros((h, w), bool)
    hit_idx = np.zeros((h, w, 3), int)
    face = np.zeros((h, w), int)           # 0 x (right side), 1 y (front), 2 z (top)
    depth = np.full((h, w), 1e6)
    step = 0.04
    for i in range(int(2 * L / step)):
        d = i * step
        cell = np.floor(origin + d * f).astype(int)
        inside = ((cell >= 0) & (cell < [X, Y, Z])).all(-1) & ~hit
        if inside.any():
            c = cell[inside]
            got = occ[c[:, 0], c[:, 1], c[:, 2]]
            if got.any():
                rows, cols = np.nonzero(inside)
                rows, cols, c = rows[got], cols[got], c[got]
                hit[rows, cols] = True
                hit_idx[rows, cols] = c
                depth[rows, cols] = d
                # Entry face: the voxel boundary the ray crossed most recently.
                frac = origin[rows, cols] + d * f - c
                since = np.where(f > 0, frac, 1 - frac) / np.maximum(abs(f), 1e-9)
                face[rows, cols] = np.argmin(since, axis=1)

    # A lone pixel whose face disagrees with all four neighbours is a grazing-ray miss: take theirs.
    nbrs = [np.roll(face, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
    lone = hit & np.all([n != face for n in nbrs], axis=0) & (nbrs[0] == nbrs[1])
    face[lone] = nbrs[0][lone]

    light = np.array([0.72, 1.0, 1.22])
    img = np.zeros((h, w, 4), np.float32)
    hi = hit_idx[hit]
    rgb = col[hi[:, 0], hi[:, 1], hi[:, 2]] * light[face[hit]][:, None]
    img[hit, :3] = rgb
    img[hit, 3] = 255
    ids = np.where(hit, pid[hit_idx[..., 0], hit_idx[..., 1], hit_idx[..., 2]], 0)

    # Black outlines: two pixels round the silhouette, one pixel between parts and where a
    # surface steps back.
    shape = ids != 0
    grown = shape.copy()
    for _ in range(outline):
        grown = grown | np.roll(grown, 1, 0) | np.roll(grown, -1, 0) | np.roll(grown, 1, 1) | np.roll(grown, -1, 1)
    line = grown & ~shape
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nid = np.roll(ids, (dy, dx), (0, 1))
        nd = np.roll(depth, (dy, dx), (0, 1))
        both = shape & (nid != 0)
        line |= both & (nid != ids) & ((nd < depth - 0.6) | ((abs(nd - depth) <= 0.6) & (nid < ids)))
        line |= both & (nid == ids) & (nd < depth - 3.0)
    img[line] = (*OUTLINE, 255)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")


def main():
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "img")
    occ, pid, col = build()
    small = render(occ, pid, col, ppv=3)
    big = small.resize((small.width * 4, small.height * 4), Image.NEAREST)
    big.save(os.path.join(here, "logo.png"))
    icon = render(occ, pid, col, ppv=1.4)
    side = max(icon.size)
    sq = Image.new("RGBA", (side, side))
    sq.paste(icon, ((side - icon.width) // 2, (side - icon.height) // 2))
    sq.resize((side * 4, side * 4), Image.NEAREST).save(os.path.join(here, "favicon.png"))
    print("logo", big.size, "favicon", sq.size)


if __name__ == "__main__":
    main()
