"""Arc and Side wallpapers: 1920x1080 WebP, graded for white icons, with grain against RGB_565 banding.

Usage: python3 -I themes/batman/make/make_wallpapers.py <folder with src-6lld66.png and src-poo9ze.png> themes/batman
(the two sources are Wallhaven wallpapers 6lld66 and poo9ze, see ../CREDITS.md)
"""
import os
import sys

from PIL import Image, ImageChops

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1920, 1080


def grain(im, sigma=2.5):
    n = Image.effect_noise((W, H), sigma)
    return ImageChops.add(im, Image.merge("RGB", (n, n, n)), scale=1.0, offset=-128)


def save(im, name):
    dest = os.path.join(OUT, name)
    im.save(dest, "WEBP", quality=84, method=6)
    print(dest, os.path.getsize(dest), "bytes")


# Arc: Batman standing in shadow, centred. Lift the dark figure (gamma curve keeps the black background black).
arc = Image.open(os.path.join(SRC, "src-6lld66.png")).convert("RGB").resize((W, H), Image.LANCZOS)
lut = [min(255, int(255 * (v / 255) ** 0.62 * 1.15)) if v > 3 else 0 for v in range(256)]
arc = arc.point(lut * 3)
save(grain(arc), "wallpaper-arc.webp")

# Side: comic Batman, arms crossed, bottom right. Dim him a little so the white icon column leads.
side = Image.open(os.path.join(SRC, "src-poo9ze.png")).convert("RGB").resize((W, H), Image.LANCZOS)
side = side.point([int(v * 0.72) for v in range(256)] * 3)
save(grain(side), "wallpaper-side.webp")
