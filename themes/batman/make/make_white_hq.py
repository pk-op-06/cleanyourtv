"""High-quality white glyphs (banner_white_*.png, 576x324): from 2400 px vector renders, with soft anti-aliased
masks instead of hard colour thresholds, so edges stay smooth at the 1.5x focus zoom.

Usage: python3 -I themes/batman/make/make_white_hq.py <logos folder: src/ from fetch.py, hq/ 2400 px renders> launcher/app/src/main/res/drawable-nodpi
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE, OUT = sys.argv[1], sys.argv[2]
W, H = 576, 324


def load(path):
    return Image.open(os.path.join(BASE, path)).convert("RGBA")


def trim(im):
    box = im.getchannel("A").getbbox()
    return im.crop(box) if box else im


def white(alpha):
    """A white glyph with this alpha channel."""
    out = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def mask(im, weight):
    """Alpha = source alpha x weight(r, g, b) in 0..1, keeping the source's anti-aliased edges."""
    px = im.load()
    a = Image.new("L", im.size, 0)
    ap = a.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, al = px[x, y]
            if al:
                ap[x, y] = int(al * max(0.0, min(1.0, weight(r, g, b))))
    return a


icons = {}
icons["netflix"] = white(trim(load("hq/netflix_n.png")).getchannel("A"))

p = load("hq/prime.png")
icons["prime"] = white(trim(p.crop((int(p.width * 0.25), int(p.height * 0.5), p.width, p.height))).getchannel("A"))

# YouTube: the red button is the glyph; the white triangle (no red) becomes a cut-out, softly.
# The dark wordmark has no red, so the mask alone leaves only the button; no crop that could clip it.
icons["youtube"] = white(mask(load("hq/youtube.png"), lambda r, g, b: (r - max(g, b)) / 140))

icons["zee5"] = white(trim(load("hq/zee5.png")).getchannel("A"))

# VLC: the orange cone is the glyph; its silver stripes (low saturation) become cut-outs, softly.
def vlc_weight(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    sat = 0 if mx == 0 else (mx - mn) / mx
    return (sat - 0.25) / 0.3


icons["vlc"] = white(mask(trim(load("hq/vlc.png")), vlc_weight))

# JioHotstar: no vector source; its star is light on a transparent ground left of the dark wordmark.
hs = load("src/hotstar.png")
star = hs.crop((0, 0, int(hs.width * 0.33), hs.height))
star_alpha = mask(trim(star), lambda r, g, b: ((r + g + b) / 765 - 0.12) / 0.12)
# Close the hairline gaps its 3D shading leaves (a grow then shrink of the mask by the same amount).
star_alpha = star_alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
icons["hotstar"] = white(star_alpha)

# Sony LIV: drawn from fonts at a large size (a font is a vector), then sampled down.
def text_glyph(txt, font):
    img = Image.new("RGBA", (3600, 1600), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((80, 80), txt, font=font, fill=(255, 255, 255, 255))
    return trim(img)


sony = text_glyph("SONY", ImageFont.truetype("/System/Library/Fonts/Supplemental/SuperClarendon.ttc", 480, index=5))
liv = text_glyph("liv", ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf", 1240))
sony = sony.resize((liv.width, round(sony.height * liv.width / sony.width)), Image.LANCZOS)
gap = round(liv.height * 0.12)
stack = Image.new("RGBA", (liv.width, sony.height + gap + liv.height), (0, 0, 0, 0))
stack.paste(sony, (0, 0), sony)
stack.paste(liv, (0, sony.height + gap), liv)
icons["sonyliv"] = stack

MAX_H = {"netflix": 192, "prime": 105, "hotstar": 195, "youtube": 138, "sonyliv": 192, "zee5": 174, "vlc": 192}
MAX_W = {"prime": 345, "youtube": 192, "zee5": 225}
os.makedirs(OUT, exist_ok=True)
for name, im in icons.items():
    im = trim(im)
    scale = min(MAX_H[name] / im.height, MAX_W.get(name, 300) / im.width)
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    canvas.alpha_composite(im, ((W - im.width) // 2, (H - im.height) // 2))
    dest = os.path.join(OUT, f"banner_white_{name}.png")
    canvas.save(dest, optimize=True)
    print(f"{name}: glyph {im.size}, {os.path.getsize(dest)} bytes")

sheet = Image.new("RGB", (W * 7, H), (8, 8, 12))
for i, name in enumerate(["netflix", "prime", "hotstar", "youtube", "sonyliv", "zee5", "vlc"]):
    tile = Image.open(os.path.join(OUT, f"banner_white_{name}.png"))
    sheet.paste(tile, (i * W, 0), tile)
sheet.save("/tmp/white-hq.png")
sheet.crop((W * 2, 0, W * 4, H)).save("/tmp/white-hq-zoom.png")
