#!/usr/bin/env python3
"""Render IgboAI wordmark lockups (horizontal, dark and light) reusing the
core mark from make_avatar.py's design. Outputs:
  lockup_dark.png  (for dark backgrounds / slides)
  lockup_light.png (for white backgrounds, e.g. GitHub README on light theme)
The wordmark's initial capital I carries a terracotta dot below as a
stylistic echo of the mark; this is a design gesture, not orthography
(the word "Igbo" is spelled with plain i).
"""
from PIL import Image, ImageDraw, ImageFont
import math

INDIGO = (26, 24, 38)
CREAM = (240, 230, 210)
TERRA = (193, 84, 44)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def draw_mark(d, cx, cy, scale, fg, accent, bg):
    """The ring/nodes/letterform mark, scaled; colors injectable."""
    R = 405 * scale
    for k in range(72):
        ang = k * 5 + 2.5
        if min(abs(((ang - 45) % 90 + 45) % 90 - 45), 45) < 7:
            continue
        x = cx + R * math.cos(math.radians(ang))
        y = cy + R * math.sin(math.radians(ang))
        r = (5 if k % 2 else 8) * scale
        d.ellipse([x - r, y - r, x + r, y + r], fill=fg if k % 3 else accent)
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        x1 = cx + (R - 52 * scale) * math.cos(a); y1 = cy + (R - 52 * scale) * math.sin(a)
        x2 = cx + (R + 52 * scale) * math.cos(a); y2 = cy + (R + 52 * scale) * math.sin(a)
        w = max(2, int(7 * scale))
        d.line([x1, y1, x2, y2], fill=fg, width=w)
        for t in (0.0, 1.0):
            x = x1 + (x2 - x1) * t; y = y1 + (y2 - y1) * t
            rr = 13 * scale
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=fg, width=w, fill=bg)
    stem_w = 76 * scale
    stem_top, stem_bot = cy - 195 * scale, cy + 120 * scale
    d.rounded_rectangle([cx - stem_w / 2, stem_top, cx + stem_w / 2, stem_bot],
                        radius=stem_w / 2, fill=fg)
    r1 = 52 * scale
    d.ellipse([cx - r1, stem_top - 135 * scale - r1, cx + r1,
               stem_top - 135 * scale + r1], fill=fg)
    r2 = 62 * scale
    by = stem_bot + 140 * scale
    halo = 22 * scale
    d.ellipse([cx - r2 - halo, by - r2 - halo, cx + r2 + halo, by + r2 + halo],
              fill=accent + (70,))
    d.ellipse([cx - r2, by - r2, cx + r2, by + r2], fill=accent)


def lockup(bg, fg, accent, path):
    W, H = 2200, 680
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img, "RGBA")
    # mark on the left
    mcx, mcy = 340, H / 2
    draw_mark(d, mcx, mcy, 0.62, fg, accent, bg)
    # wordmark
    font = ImageFont.truetype(FONT, 300)
    text = "IgboAI"
    tx = 700
    bbox = d.textbbox((0, 0), text, font=font)
    ty = (H - (bbox[3] - bbox[1])) / 2 - bbox[1]
    d.text((tx, ty), text, font=font, fill=fg)
    # terracotta dot below the initial "I" (stylistic echo, not orthography)
    ibox = d.textbbox((tx, ty), "I", font=font)
    icx = (ibox[0] + ibox[2]) / 2
    dot_y = ibox[3] + 64
    d.ellipse([icx - 30, dot_y - 30, icx + 30, dot_y + 30], fill=accent)
    # subtitle
    sub = ImageFont.truetype(FONT, 62)
    d.text((tx + 12, ty + (bbox[3] - bbox[1]) + 118),
           "Open research infrastructure for Igbo language AI",
           font=sub, fill=tuple(int(c * 0.72 + b * 0.28) for c, b in zip(fg, bg)))
    img.save(path)


lockup(INDIGO, CREAM, TERRA, "lockup_dark.png")
lockup((247, 243, 235), INDIGO, TERRA, "lockup_light.png")
print("lockups rendered")
