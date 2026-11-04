"""The GearDrew studio splash for the games: the voxel logo with "GearDrew" to its right.

Transparent and cropped tight; the game centres it on the studio background (#14121c).

    python tools/make_splash.py OUT.png      # e.g. ../silly-delivery/splash/geardrew_logo.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

from make_logo import build, render

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts", "GeardrewPixel.ttf")
OUTLINE = (14, 11, 18)


def name_text(scale):
    """ "Gear" light, "Drew" orange, outlined; drawn at 2 px per font pixel (92/1000 em) so the pixel font
    lands on the grid, then scaled up with nearest-neighbour."""
    font = ImageFont.truetype(FONT, 2 * 1000 / 92)
    parts = [("Gear", (236, 232, 244)), ("Drew", (244, 165, 58))]
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths = [probe.textlength(t, font=font) for t, _ in parts]
    img = Image.new("RGBA", (int(sum(widths)) + 8, 24))
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    x = 4
    for (t, c), w in zip(parts, widths):
        d.text((x, 2), t, font=font, fill=c, stroke_width=2, stroke_fill=OUTLINE)
        x += w
    img = img.crop(img.getbbox())
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def main(out):
    small = render(*build(), ppv=3)
    logo = small.resize((small.width * 2, small.height * 2), Image.NEAREST)
    text = name_text(6)
    gap = 48
    img = Image.new("RGBA", (logo.width + gap + text.width, logo.height))
    img.paste(logo, (0, 0), logo)
    img.paste(text, (logo.width + gap, (logo.height - text.height) // 2), text)
    img.save(out)
    print(out, img.size)


if __name__ == "__main__":
    main(sys.argv[1])
