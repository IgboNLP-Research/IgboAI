#!/usr/bin/env python3
"""Render the IgboNLP-Research org avatar.

Design: the lowercase letter "i" with a dot BELOW as well as above --
evoking the distinctive Igbo orthographic dot-below (as in i-dot: the
vowel in "Igbo" itself when written with full diacritics). The dot-below
is rendered in terracotta as the focal accent. Around it, an uli-inspired
ring of dots and four node-and-line motifs suggest the network/AI side.
Palette drawn from uli body-art tradition: deep indigo-black ground,
cream line-work, terracotta accent.
"""
from PIL import Image, ImageDraw, ImageFont
import math

S = 1024
INDIGO = (26, 24, 38)        # deep indigo-black ground
CREAM = (240, 230, 210)      # uli cream
TERRA = (193, 84, 44)        # terracotta accent
TERRA_SOFT = (193, 84, 44, 90)

img = Image.new("RGB", (S, S), INDIGO)
d = ImageDraw.Draw(img, "RGBA")
cx, cy = S / 2, S / 2

# --- uli dot ring (broken at the cardinal points, hand-drawn feel) ---
R = 400
for k in range(72):
    ang = k * 5 + 2.5
    # leave gaps at the four cardinals for breathing room
    if min(abs(((ang % 90) + 45) % 90 - 45), 45) < 6:
        continue
    x = cx + R * math.cos(math.radians(ang))
    y = cy + R * math.sin(math.radians(ang))
    r = 5 if k % 2 else 8
    d.ellipse([x - r, y - r, x + r, y + r], fill=CREAM if k % 3 else TERRA)

# --- four node-and-line motifs at the cardinals (the "network") ---
for ang in (0, 90, 180, 270):
    a = math.radians(ang)
    x1 = cx + (R - 55) * math.cos(a); y1 = cy + (R - 55) * math.sin(a)
    x2 = cx + (R + 55) * math.cos(a); y2 = cy + (R + 55) * math.sin(a)
    d.line([x1, y1, x2, y2], fill=CREAM, width=7)
    for t, rr in ((0.0, 13), (1.0, 13)):
        x = x1 + (x2 - x1) * t; y = y1 + (y2 - y1) * t
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=CREAM, width=7,
                  fill=INDIGO)

# --- the letterform: a drawn "I" stem so we control both dots ---
stem_w = 74
stem_top = cy - 205
stem_bot = cy + 158
d.rounded_rectangle([cx - stem_w / 2, stem_top, cx + stem_w / 2, stem_bot],
                    radius=stem_w / 2, fill=CREAM)

# dot above (cream, the ordinary i-dot)
r1 = 52
d.ellipse([cx - r1, stem_top - 150 - r1, cx + r1, stem_top - 150 + r1],
          fill=CREAM)

# dot below (terracotta, the Igbo dot-below -- the hero of the mark)
r2 = 62
by = stem_bot + 150
d.ellipse([cx - r2 - 26, by - r2 - 26, cx + r2 + 26, by + r2 + 26],
          fill=TERRA_SOFT)  # soft halo
d.ellipse([cx - r2, by - r2, cx + r2, by + r2], fill=TERRA)

img.save("avatar_1024.png")
for size in (512, 256):
    img.resize((size, size), Image.LANCZOS).save(f"avatar_{size}.png")
print("rendered")
