"""Draw a dark Gotham-night wallpaper (1920x1080): Bat-Signal in the clouds, skyline, black lower third.

Usage: python3 -I themes/batman/make/make_gotham.py themes/batman/wallpaper.jpg
"""
import math
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H = 1920, 1080
rnd = random.Random(1939)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# Sky: deep slate-blue at the top fading to black well before the dock.
img = Image.new("RGB", (W, H))
px = img.load()
top, mid, low = (22, 28, 40), (10, 13, 20), (0, 0, 0)
for y in range(H):
    t = y / H
    c = lerp(top, mid, t / 0.45) if t < 0.45 else lerp(mid, low, min(1, (t - 0.45) / 0.3))
    for x in range(W):
        px[x, y] = c

# Clouds: soft, blurred blobs, lit faintly from the signal.
clouds = Image.new("L", (W, H), 0)
cd = ImageDraw.Draw(clouds)
for _ in range(70):
    cx, cy = rnd.uniform(500, 1920), rnd.uniform(120, 560)
    rx, ry = rnd.uniform(90, 260), rnd.uniform(30, 80)
    cd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=rnd.randint(18, 42))
clouds = clouds.filter(ImageFilter.GaussianBlur(40))
img.paste((70, 82, 104), mask=clouds)

# Bat-Signal: a pale disc on the clouds with a bat silhouette inside, and the beam rising to it.
SX, SY, SR = 1340, 360, 150
beam = Image.new("L", (W, H), 0)
ImageDraw.Draw(beam).polygon([(1180, H), (1230, H), (SX + SR * 0.95, SY + 40), (SX - SR * 0.95, SY + 40)], fill=34)
beam = beam.filter(ImageFilter.GaussianBlur(28))
img.paste((190, 196, 170), mask=beam)

glow = Image.new("L", (W, H), 0)
ImageDraw.Draw(glow).ellipse([SX - SR * 1.9, SY - SR * 1.25, SX + SR * 1.9, SY + SR * 1.25], fill=60)
glow = glow.filter(ImageFilter.GaussianBlur(70))
img.paste((215, 210, 170), mask=glow)

disc = Image.new("L", (W, H), 0)
ImageDraw.Draw(disc).ellipse([SX - SR * 1.45, SY - SR * 0.85, SX + SR * 1.45, SY + SR * 0.85], fill=150)
disc = disc.filter(ImageFilter.GaussianBlur(10))
img.paste((226, 220, 176), mask=disc)

# Bat: right half as (x, y) in units of the wing span, mirrored for the left half.
half = [(0.0, -0.12), (0.045, -0.42), (0.09, -0.16), (0.15, -0.14), (0.24, -0.20), (0.40, -0.34),
        (0.62, -0.46), (0.84, -0.52), (1.00, -0.42), (0.93, -0.12), (0.81, -0.22), (0.72, 0.08),
        (0.58, -0.05), (0.46, 0.22), (0.32, 0.07), (0.17, 0.36), (0.07, 0.24), (0.0, 0.44)]
pts = half + [(-x, y) for x, y in reversed(half[1:-1])]
bw, bh = SR * 1.22, SR * 0.80
bat = [(SX + x * bw, SY + y * bh) for x, y in pts]
ImageDraw.Draw(img).polygon(bat, fill=(14, 15, 18))

# Skyline: two layers of towers, the far one lighter, a few amber windows.
draw = ImageDraw.Draw(img)
for layer, (base_y, hmin, hmax, col) in enumerate([(700, 80, 330, (12, 14, 20)), (760, 60, 260, (3, 3, 5))]):
    x = -20
    while x < W + 20:
        w = rnd.randint(50, 140)
        h = rnd.randint(hmin, hmax)
        top_y = base_y - h
        draw.rectangle([x, top_y, x + w, H], fill=col)
        if rnd.random() < 0.25 and not (SX - SR * 1.6 < x + w // 2 < SX + SR * 1.6):  # spire, not into the signal
            sx = x + w // 2
            draw.polygon([(sx - 8, top_y), (sx + 8, top_y), (sx, top_y - rnd.randint(40, 110))], fill=col)
        if layer == 0:
            for wy in range(top_y + 14, base_y, 22):
                for wx in range(x + 8, x + w - 8, 18):
                    if rnd.random() < 0.05:
                        draw.rectangle([wx, wy, wx + 5, wy + 8], fill=(120, 96, 52))
        x += w + rnd.randint(0, 12)

# Fade the lower third to pure black so the dock sits on black.
fade = Image.new("L", (W, H), 0)
fd = ImageDraw.Draw(fade)
for y in range(720, H):
    fd.line([(0, y), (W, y)], fill=min(255, int((y - 720) / 220 * 255)))
img.paste((0, 0, 0), mask=fade)

# Grain: breaks up gradient banding when the TV decodes the picture as RGB_565.
noise = Image.effect_noise((W, H), 3)
img = ImageChops.add(img, Image.merge("RGB", (noise, noise, noise)), scale=1.0, offset=-128)

out = sys.argv[1]
img.save(out, "JPEG", quality=84, optimize=True, progressive=False)
print(out)
