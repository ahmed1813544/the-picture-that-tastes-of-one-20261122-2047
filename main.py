#!/usr/bin/env python3
"""The picture that tastes of one ingredient: GOLDEN HONEY.

One hero ingredient, drawn entirely in code with PIL:
a wooden honey dipper dripping thick golden honey over a
glistening chunk of honeycomb, on a dark warm background.

Deterministic: fixed palette, fixed geometry, no randomness,
no network, no external files. Writes /output/entry.png
(or OUTPUT_PATH, or ./entry.png as a local fallback).
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

W = H = 1024

# ---------------------------------------------------------------- palette
BG_TOP = (30, 16, 9)
BG_BOT = (10, 6, 4)
GLOW = (255, 176, 60)

HONEY_DEEP = (146, 72, 8)
HONEY_MID = (214, 128, 16)
HONEY_BRIGHT = (255, 178, 44)
HONEY_LIGHT = (255, 214, 110)
HONEY_PALE = (255, 232, 160)

WAX_DEEP = (112, 60, 10)
WAX_MID = (190, 118, 22)
WAX_LIGHT = (244, 176, 66)

WOOD_DEEP = (74, 40, 14)
WOOD_MID = (122, 70, 26)
WOOD_LIGHT = (176, 116, 52)
WOOD_PALE = (216, 160, 94)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, top, bottom):
    """Vertical gradient image."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        px[0, y] = lerp(top, bottom, y / max(1, h - 1))
    return img.resize((w, h))


def radial_glow(base, cx, cy, radius, color, alpha=150):
    """Soft warm glow: concentric translucent ellipses."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 24
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(alpha * (1 - t) ** 2 / steps * 4)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=color + (max(0, min(255, a)),))
    return Image.alpha_composite(base.convert("RGBA"), layer)


def hex_points(cx, cy, r, rot=0.0):
    pts = []
    for i in range(6):
        ang = math.radians(60 * i + rot)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def honeycomb(draw, cx0, top_y, cell_r, row_lens):
    """A chunky slab of honeycomb: wax hex rims, glossy honey pools.

    row_lens gives the cell count per row, so the slab reads as one
    solid piece of comb instead of a repeating pattern.
    """
    dy = cell_r * math.sqrt(3) * 0.92
    for row, n in enumerate(row_lens):
        y = top_y + row * dy
        row_w = n * cell_r * 1.5
        x0 = cx0 - row_w / 2 + cell_r * 0.75
        for col in range(n):
            cx = x0 + col * cell_r * 1.5
            # depth shadow inside the cell
            draw.polygon(hex_points(cx, cy=y, r=cell_r), fill=WAX_DEEP)
            inner = hex_points(cx, y, cell_r * 0.84)
            lvl = (row * 7 + col * 3) % 5
            if lvl == 0:
                fill = HONEY_DEEP
            elif lvl == 1:
                fill = lerp(HONEY_DEEP, HONEY_MID, 0.5)
            elif lvl == 2:
                fill = lerp(HONEY_MID, HONEY_BRIGHT, 0.45)
            else:
                fill = lerp(HONEY_MID, HONEY_BRIGHT, 0.25)
            draw.polygon(inner, fill=fill)
            # glossy meniscus: soft bright crescent, top-left of the pool
            gx, gy = cx - cell_r * 0.26, y - cell_r * 0.30
            draw.ellipse([gx - cell_r * 0.20, gy - cell_r * 0.09,
                          gx + cell_r * 0.20, gy + cell_r * 0.09],
                         fill=HONEY_LIGHT)
            # wax rim: bright on the two upper edges
            top = hex_points(cx, y, cell_r)
            draw.line([top[4], top[5]], fill=WAX_LIGHT, width=7)
            draw.line([top[5], top[0]], fill=lerp(WAX_LIGHT, WAX_MID, 0.35),
                      width=6)
            # a few cells overflow with honey spilling over the rim
            if (row * 5 + col) % 9 == 4:
                draw.ellipse([cx - cell_r * 0.5, y + cell_r * 0.42,
                              cx + cell_r * 0.5, y + cell_r * 0.95],
                             fill=HONEY_BRIGHT)
                draw.ellipse([cx - cell_r * 0.28, y + cell_r * 0.5,
                              cx + cell_r * 0.1, y + cell_r * 0.8],
                             fill=HONEY_LIGHT)


def drip_stream(draw, x0, y0, x1, y1, w0, w1, sway=10):
    """A thick glossy honey stream from (x0,y0) to (x1,y1)."""
    steps = 48
    pts_l, pts_r = [], []
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t + sway * math.sin(t * math.pi) * (1 - t * 0.5)
        y = y0 + (y1 - y0) * t
        w = w0 + (w1 - w0) * t
        pts_l.append((x - w, y))
        pts_r.append((x + w, y))
    draw.polygon(pts_l + pts_r[::-1], fill=HONEY_MID)
    # bright core, offset to the lit side
    core_l, core_r = [], []
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t + sway * math.sin(t * math.pi) * (1 - t * 0.5) \
            - w0 * 0.30
        y = y0 + (y1 - y0) * t
        w = (w0 + (w1 - w0) * t) * 0.40
        core_l.append((x - w, y))
        core_r.append((x + w, y))
    draw.polygon(core_l + core_r[::-1], fill=HONEY_BRIGHT)
    # specular streak
    draw.line([(x0 - w0 * 0.55, y0 + 8), (x1 - w1 * 0.55, y1 - 10)],
              fill=HONEY_PALE, width=8)
    # drip bulb at the bottom
    bx, by = x1 + 4, y1 + 30
    draw.ellipse([bx - 30, by - 40, bx + 30, by + 40], fill=HONEY_MID)
    draw.ellipse([bx - 20, by - 30, bx + 20, by + 30], fill=HONEY_BRIGHT)
    draw.ellipse([bx - 18, by - 28, bx - 2, by + 0], fill=HONEY_PALE)


def dipper(draw):
    """Big wooden honey dipper, diagonal, grooved head lower-left."""
    # handle: long tapered rounded bar from top-right to the head
    hx0, hy0 = 912, 84
    hx1, hy1 = 600, 330
    ang = math.atan2(hy1 - hy0, hx1 - hx0)
    perp = ang + math.pi / 2
    hw = 34
    px, py = math.cos(perp) * hw, math.sin(perp) * hw
    draw.polygon([(hx0 - px, hy0 - py), (hx1 - px, hy1 - py),
                  (hx1 + px, hy1 + py), (hx0 + px, hy0 + py)],
                 fill=WOOD_MID)
    # handle light and shade
    draw.line([(hx0 - px * 0.45, hy0 - py * 0.45),
               (hx1 - px * 0.45, hy1 - py * 0.45)], fill=WOOD_PALE, width=12)
    draw.line([(hx0 + px * 0.72, hy0 + py * 0.72),
               (hx1 + px * 0.72, hy1 + py * 0.72)], fill=WOOD_DEEP, width=10)
    # knob at the end
    draw.ellipse([hx0 - 44, hy0 - 44, hx0 + 44, hy0 + 44], fill=WOOD_MID)
    draw.ellipse([hx0 - 30, hy0 - 30, hx0 + 30, hy0 + 30], fill=WOOD_LIGHT)
    draw.ellipse([hx0 - 18, hy0 - 24, hx0 + 2, hy0 - 4], fill=WOOD_PALE)
    # grooved head: stacked discs with dark gaps, honey-coated
    cx, cy = 512, 400
    radii = [128, 138, 142, 138, 128]
    for i, r in enumerate(radii):
        yy = cy - 96 + i * 46
        # dark groove gap above each disc
        draw.ellipse([cx - r, yy - 26, cx + r, yy + 4], fill=WOOD_DEEP)
        shade = lerp(WOOD_MID, HONEY_MID, 0.5)
        draw.ellipse([cx - r, yy - 22, cx + r, yy + 26], fill=shade)
        draw.ellipse([cx - r + 14, yy - 22, cx + r - 14, yy - 4],
                     fill=lerp(shade, HONEY_BRIGHT, 0.6))
    # honey sheen on the head: small, warm, never a white blob
    draw.ellipse([cx - 62, cy - 96, cx - 18, cy - 58], fill=HONEY_LIGHT)
    draw.ellipse([cx + 48, cy + 34, cx + 80, cy + 62], fill=HONEY_LIGHT)


def honey_pool(draw, cx, cy, rx, ry):
    """A wobbly pool of spilled honey (overlapping ellipses)."""
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=HONEY_MID)
    draw.ellipse([cx - rx * 0.78, cy - ry * 0.62,
                  cx + rx * 0.82, cy + ry * 0.66], fill=HONEY_BRIGHT)
    draw.ellipse([cx - rx * 0.45, cy - ry * 0.5,
                  cx + rx * 0.1, cy + ry * 0.3], fill=HONEY_LIGHT)
    draw.ellipse([cx - rx * 0.34, cy - ry * 0.38,
                  cx - rx * 0.05, cy - ry * 0.05], fill=HONEY_PALE)


def main():
    img = vgrad((W, H), BG_TOP, BG_BOT).convert("RGBA")
    img = radial_glow(img, 512, 540, 620, GLOW, alpha=130)

    # soft shadow under the comb slab
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.ellipse([180, 760, 844, 1030], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(34))
    img = Image.alpha_composite(img, sh)

    draw = ImageDraw.Draw(img)

    # big chunk of honeycomb, lower half: four rows, fully in frame
    honeycomb(draw, 512, 590, 74, [4, 5, 6, 5])

    # thick honey pouring from the dipper onto the comb
    drip_stream(draw, 470, 500, 500, 590, 26, 18)
    drip_stream(draw, 560, 505, 600, 585, 15, 10, sway=-8)

    # dipper on top, overlapping the stream's source
    dipper(draw)

    # honey spilling off the comb's bottom edge into a shallow pool
    drip_stream(draw, 430, 930, 442, 968, 11, 8, sway=4)
    honey_pool(draw, 512, 1006, 290, 30)

    # gentle vignette
    vg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vg)
    for i in range(18, 0, -1):
        t = i / 18
        dv.rectangle([0, 0, W, H], outline=(0, 0, 0, int(9 * (1 - t))),
                     width=26)
    img = Image.alpha_composite(img, vg)

    out = os.environ.get("OUTPUT_PATH", "/output/entry.png")
    try:
        img.convert("RGB").save(out, "PNG", optimize=True)
    except OSError:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "entry.png")
        img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
