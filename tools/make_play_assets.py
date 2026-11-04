"""Google Play developer page art: the 512 x 512 studio icon and the 4096 x 2304 header image.

Both are opaque (24-bit) and kept under 1 MB, as Play asks. The header is a town screenshot from
Silly Delivery, taken with the game's store-shot options:

    godot --path silly-delivery -- --play --ctest --built=5 --at=2,-1 --radius=18 --zoom=62 \\
        --time=15.5 --nohud --shotsec=20 --shotsize=4096x2304 --shot=town.png
    python tools/make_play_assets.py town.png       # writes files/google-play/
"""
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

from make_logo import build, render
from make_splash import name_text

BG = (20, 18, 28)
LIMIT = 1024 * 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files", "google-play")


def icon():
    small = render(*build(), ppv=2.6)
    logo = small.resize((small.width * 3, small.height * 3), Image.NEAREST)
    img = Image.new("RGB", (512, 512), BG)
    img.paste(logo, ((512 - logo.width) // 2, (512 - logo.height) // 2), logo)
    return img


def save_jpeg(img, path):
    """Best JPEG quality that still fits in 1 MB."""
    for q in range(95, 50, -3):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True, progressive=True, subsampling=0 if q >= 90 else 2)
        if buf.tell() <= LIMIT:
            open(path, "wb").write(buf.getvalue())
            return q, buf.tell()
    raise SystemExit("could not fit " + path + " in 1 MB")


def with_logo(town):
    """The header with the studio logo and name in the middle, on a soft dark band (Play crops the
    header's sides on phones, so the middle is the part everyone sees)."""
    img = town.copy()
    small = render(*build(), ppv=3)
    logo = small.resize((small.width * 3, small.height * 3), Image.NEAREST)
    text = name_text(9)
    gap = 70
    w, h = logo.width + gap + text.width, logo.height
    x0, y0 = (img.width - w) // 2, (img.height - h) // 2
    band = Image.new("L", img.size, 0)
    ImageDraw.Draw(band).rounded_rectangle((x0 - 120, y0 - 80, x0 + w + 120, y0 + h + 80), 60, fill=200)
    band = band.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", img.size, BG), img, band)
    img.paste(logo, (x0, y0), logo)
    img.paste(text, (x0 + logo.width + gap, y0 + (h - text.height) // 2), text)
    return img


def main(shot):
    os.makedirs(OUT, exist_ok=True)
    ic = icon()
    ic.save(os.path.join(OUT, "geardrew-icon-512.png"))
    town = Image.open(shot).convert("RGB")
    assert town.size == (4096, 2304), town.size
    for name, img in (("geardrew-header-4096x2304.jpg", town), ("geardrew-header-logo-4096x2304.jpg", with_logo(town))):
        q, n = save_jpeg(img, os.path.join(OUT, name))
        print(name, "quality", q, n // 1024, "KB")
    print("geardrew-icon-512.png", os.path.getsize(os.path.join(OUT, "geardrew-icon-512.png")) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1])
