#!/usr/bin/env python3
"""The picture that tastes of one ingredient: GOLDEN HONEY.

One hero ingredient, drawn entirely in code with the Python
standard library only: a wooden honey dipper dripping thick
golden honey over a glistening chunk of honeycomb, on a dark
warm background with a golden glow.

No third-party imports. The picture is painted by a small
software rasterizer written by hand for this program: a flat
RGB pixel buffer, scanline polygon and ellipse fills, thick
lines, a vertical gradient with a radial glow, a soft shadow,
and a vignette. The PNG is encoded by hand too (zlib + the
PNG chunk format).

Deterministic: fixed palette, fixed geometry, no randomness,
no network, no external files. Writes entry.png to
OUTPUT_PATH, or MAKEFUN_OUTPUT_DIR/entry.png, or
/output/entry.png, with a local fallback next to this file.
"""

import math
import os
import struct
import zlib

W = H = 1024

# ------------------------------------------------------------------ palette
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


def mix(a, b, t):
    """Blend two RGB colours; t=0 gives a, t=1 gives b."""
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


# ------------------------------------------------------------------ canvas
class Canvas:
    """A flat RGB pixel buffer with scanline drawing primitives."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    # -- low level ---------------------------------------------------
    def _row_base(self, y):
        return y * self.w * 3

    def span(self, y, x0, x1, color):
        """Fill pixels [x0, x1) on row y with a solid colour."""
        if y < 0 or y >= self.h or x1 <= x0:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        base = self._row_base(y) + x0 * 3
        self.px[base:base + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def span_blend(self, y, x0, x1, color, alpha):
        """Blend a colour over pixels [x0, x1) on row y."""
        if y < 0 or y >= self.h or x1 <= x0 or alpha <= 0.0:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        inv = 1.0 - alpha
        r, g, b = color
        px = self.px
        i = self._row_base(y) + x0 * 3
        for _ in range(x1 - x0):
            px[i] = int(px[i] * inv + r * alpha)
            px[i + 1] = int(px[i + 1] * inv + g * alpha)
            px[i + 2] = int(px[i + 2] * inv + b * alpha)
            i += 3

    # -- shapes ------------------------------------------------------
    def polygon(self, pts, color):
        """Scanline-fill a polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(self.h - 1, int(math.floor(max(ys))))
        edges = []
        n = len(pts)
        for i in range(n):
            x0, ya = pts[i]
            x1, yb = pts[(i + 1) % n]
            if ya != yb:
                edges.append((ya, x0, yb, x1))
        for y in range(y0, y1 + 1):
            yc = y + 0.5
            xs = []
            for ya, xa, yb, xb in edges:
                if (ya <= yc < yb) or (yb <= yc < ya):
                    xs.append(xa + (yc - ya) / (yb - ya) * (xb - xa))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.span(y, int(math.ceil(xs[k])),
                          int(math.floor(xs[k + 1])) + 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        """Fill an axis-aligned ellipse."""
        if rx <= 0 or ry <= 0:
            return
        y0 = max(0, int(math.ceil(cy - ry)))
        y1 = min(self.h - 1, int(math.floor(cy + ry)))
        for y in range(y0, y1 + 1):
            t = (y + 0.5 - cy) / ry
            if -1.0 < t < 1.0:
                hw = rx * math.sqrt(1.0 - t * t)
                self.span(y, int(math.ceil(cx - hw)),
                          int(math.floor(cx + hw)) + 1, color)

    def disc(self, cx, cy, r, color):
        self.ellipse(cx, cy, r, r, color)

    def ellipse_alpha(self, cx, cy, rx, ry, color, alpha):
        """Fill an ellipse blending over what is already there."""
        if rx <= 0 or ry <= 0 or alpha <= 0.0:
            return
        y0 = max(0, int(math.ceil(cy - ry)))
        y1 = min(self.h - 1, int(math.floor(cy + ry)))
        for y in range(y0, y1 + 1):
            t = (y + 0.5 - cy) / ry
            if -1.0 < t < 1.0:
                hw = rx * math.sqrt(1.0 - t * t)
                self.span_blend(y, int(math.ceil(cx - hw)),
                                int(math.floor(cx + hw)) + 1,
                                color, alpha)

    def thick_line(self, x0, y0, x1, y1, width, color):
        """A line drawn as a filled quad, width in pixels."""
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length == 0:
            self.disc(x0, y0, width / 2.0, color)
            return
        nx, ny = -dy / length * width / 2.0, dx / length * width / 2.0
        self.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                      (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], color)

    # -- full-frame passes -------------------------------------------
    def paint_background(self):
        """Vertical gradient plus a warm radial glow, one pass."""
        w, h = self.w, self.h
        px = self.px
        gx, gy, gr = 512.0, 540.0, 620.0
        for y in range(h):
            t = y / (h - 1)
            br = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
            bg = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
            bb = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
            dy = y - gy
            base = y * w * 3
            for x in range(w):
                dx = x - gx
                d = math.sqrt(dx * dx + dy * dy) / gr
                if d < 1.0:
                    a = 0.5 * (1.0 - d) * (1.0 - d)
                    i = base + x * 3
                    px[i] = int(br * (1 - a) + GLOW[0] * a)
                    px[i + 1] = int(bg * (1 - a) + GLOW[1] * a)
                    px[i + 2] = int(bb * (1 - a) + GLOW[2] * a)
                else:
                    i = base + x * 3
                    px[i] = br
                    px[i + 1] = bg
                    px[i + 2] = bb

    def vignette(self):
        """Darken the corners; only pixels outside the inner circle."""
        w, h = self.w, self.h
        px = self.px
        cx = cy = 512.0
        inner = 450.0
        outer = 724.0
        for y in range(h):
            dy = y - cy
            if abs(dy) >= outer:
                x_lo, x_hi = 0, w
            else:
                hw = math.sqrt(max(0.0, inner * inner - dy * dy))
                x_lo, x_hi = int(math.ceil(cx - hw)), int(math.floor(cx + hw))
            for x in range(0, x_lo):
                dx = x - cx
                d = math.sqrt(dx * dx + dy * dy)
                if d > inner:
                    f = 1.0 - 0.32 * ((d - inner) / (outer - inner)) ** 2
                    i = (y * w + x) * 3
                    px[i] = int(px[i] * f)
                    px[i + 1] = int(px[i + 1] * f)
                    px[i + 2] = int(px[i + 2] * f)
            for x in range(x_hi, w):
                dx = x - cx
                d = math.sqrt(dx * dx + dy * dy)
                if d > inner:
                    f = 1.0 - 0.32 * ((d - inner) / (outer - inner)) ** 2
                    i = (y * w + x) * 3
                    px[i] = int(px[i] * f)
                    px[i + 1] = int(px[i + 1] * f)
                    px[i + 2] = int(px[i + 2] * f)


# ------------------------------------------------------------------ helpers
def hex_points(cx, cy, r, rot=0.0):
    return [(cx + r * math.cos(math.radians(60 * i + rot)),
             cy + r * math.sin(math.radians(60 * i + rot)))
            for i in range(6)]


# ------------------------------------------------------------------ picture
def honeycomb(cv, cx0, top_y, cell_r, row_lens):
    """A chunky slab of honeycomb: wax hex rims, glossy honey pools."""
    dy = cell_r * math.sqrt(3) * 0.92
    for row, n in enumerate(row_lens):
        y = top_y + row * dy
        row_w = n * cell_r * 1.5
        x0 = cx0 - row_w / 2 + cell_r * 0.75
        for col in range(n):
            cx = x0 + col * cell_r * 1.5
            cv.polygon(hex_points(cx, y, cell_r), WAX_DEEP)
            lvl = (row * 7 + col * 3) % 5
            if lvl == 0:
                fill = HONEY_DEEP
            elif lvl == 1:
                fill = mix(HONEY_DEEP, HONEY_MID, 0.5)
            elif lvl == 2:
                fill = mix(HONEY_MID, HONEY_BRIGHT, 0.45)
            else:
                fill = mix(HONEY_MID, HONEY_BRIGHT, 0.25)
            cv.polygon(hex_points(cx, y, cell_r * 0.84), fill)
            # glossy meniscus: bright crescent, top-left of the pool
            gx, gy = cx - cell_r * 0.26, y - cell_r * 0.30
            cv.ellipse(gx, gy, cell_r * 0.20, cell_r * 0.09, HONEY_LIGHT)
            # wax rim: bright on the two upper edges
            top = hex_points(cx, y, cell_r)
            cv.thick_line(top[4][0], top[4][1], top[5][0], top[5][1],
                          7, WAX_LIGHT)
            cv.thick_line(top[5][0], top[5][1], top[0][0], top[0][1],
                          6, mix(WAX_LIGHT, WAX_MID, 0.35))
            # a few cells overflow with honey spilling over the rim
            if (row * 5 + col) % 9 == 4:
                cv.ellipse(cx, y + cell_r * 0.68, cell_r * 0.5,
                           cell_r * 0.26, HONEY_BRIGHT)
                cv.ellipse(cx - cell_r * 0.09, y + cell_r * 0.65,
                           cell_r * 0.19, cell_r * 0.15, HONEY_LIGHT)


def drip_stream(cv, x0, y0, x1, y1, w0, w1, sway=10):
    """A thick glossy honey stream from (x0, y0) to (x1, y1)."""
    def centre(t):
        return (x0 + (x1 - x0) * t
                + sway * math.sin(t * math.pi) * (1 - t * 0.5),
                y0 + (y1 - y0) * t)

    steps = 48
    left, right = [], []
    for i in range(steps + 1):
        t = i / steps
        x, y = centre(t)
        w = w0 + (w1 - w0) * t
        left.append((x - w, y))
        right.append((x + w, y))
    cv.polygon(left + right[::-1], HONEY_MID)
    # bright core, offset to the lit side
    core_l, core_r = [], []
    for i in range(steps + 1):
        t = i / steps
        x, y = centre(t)
        w = (w0 + (w1 - w0) * t) * 0.40
        core_l.append((x - w - w0 * 0.30, y))
        core_r.append((x + w - w0 * 0.30, y))
    cv.polygon(core_l + core_r[::-1], HONEY_BRIGHT)
    # specular streak, kept narrow so the stream reads as honey
    cv.thick_line(x0 - w0 * 0.55, y0 + 8, x1 - w1 * 0.55, y1 - 10,
                  6, HONEY_PALE)
    # drip bulb at the bottom
    bx, by = x1 + 4, y1 + 30
    cv.ellipse(bx, by, 30, 40, HONEY_MID)
    cv.ellipse(bx, by, 20, 30, HONEY_BRIGHT)
    cv.ellipse(bx - 10, by - 14, 8, 14, HONEY_PALE)


def dipper(cv):
    """Big wooden honey dipper, diagonal, grooved head lower-left."""
    hx0, hy0 = 912, 84
    hx1, hy1 = 600, 330
    ang = math.atan2(hy1 - hy0, hx1 - hx0)
    perp = ang + math.pi / 2
    hw = 34
    px, py = math.cos(perp) * hw, math.sin(perp) * hw
    cv.polygon([(hx0 - px, hy0 - py), (hx1 - px, hy1 - py),
                (hx1 + px, hy1 + py), (hx0 + px, hy0 + py)], WOOD_MID)
    cv.thick_line(hx0 - px * 0.45, hy0 - py * 0.45,
                  hx1 - px * 0.45, hy1 - py * 0.45, 12, WOOD_PALE)
    cv.thick_line(hx0 + px * 0.72, hy0 + py * 0.72,
                  hx1 + px * 0.72, hy1 + py * 0.72, 10, WOOD_DEEP)
    # knob at the end of the handle
    cv.disc(hx0, hy0, 44, WOOD_MID)
    cv.disc(hx0, hy0, 30, WOOD_LIGHT)
    cv.ellipse(hx0 - 8, hy0 - 14, 10, 10, WOOD_PALE)
    # grooved head: stacked discs with dark gaps, honey-coated
    cx, cy = 512, 400
    radii = [128, 138, 142, 138, 128]
    for i, r in enumerate(radii):
        yy = cy - 96 + i * 46
        cv.ellipse(cx, yy - 11, r, 15, WOOD_DEEP)
        shade = mix(WOOD_MID, HONEY_MID, 0.5)
        cv.ellipse(cx, yy + 2, r, 24, shade)
        cv.ellipse(cx, yy - 13, r - 14, 9,
                   mix(shade, HONEY_BRIGHT, 0.6))
    # honey sheen on the head
    cv.ellipse(cx - 40, cy - 77, 22, 19, HONEY_LIGHT)
    cv.ellipse(cx + 64, cy + 48, 16, 14, HONEY_LIGHT)


def honey_pool(cv, cx, cy, rx, ry):
    """A wobbly pool of spilled honey (overlapping ellipses)."""
    cv.ellipse(cx, cy, rx, ry, HONEY_MID)
    cv.ellipse(cx + 2, cy + 2, rx * 0.80, ry * 0.64, HONEY_BRIGHT)
    cv.ellipse(cx - 18, cy - 10, rx * 0.28, ry * 0.40, HONEY_LIGHT)
    cv.ellipse(cx - 100, cy - 12, rx * 0.14, ry * 0.16, HONEY_PALE)


# ------------------------------------------------------------------ PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(cv, path):
    """Encode the canvas as a 1024x1024 RGB PNG (filter 0 rows)."""
    w, h = cv.w, cv.h
    raw = bytearray()
    stride = w * 3
    px = cv.px
    for y in range(h):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------ main
def resolve_output_path():
    if os.environ.get("OUTPUT_PATH"):
        return os.environ["OUTPUT_PATH"]
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        return os.path.join(out_dir, "entry.png")
    return "/output/entry.png"


def main():
    cv = Canvas(W, H)
    cv.paint_background()

    # soft shadow under the comb slab (layered translucent ellipses)
    for k, a in ((1.00, 0.10), (0.85, 0.12), (0.68, 0.14), (0.50, 0.16)):
        cv.ellipse_alpha(512, 895, 332 * k, 135 * k, (0, 0, 0), a)

    # big chunk of honeycomb, lower half: four rows, fully in frame
    honeycomb(cv, 512, 590, 74, [4, 5, 6, 5])

    # thick honey pouring from the dipper onto the comb
    drip_stream(cv, 470, 500, 500, 590, 26, 18)
    drip_stream(cv, 560, 505, 600, 585, 15, 10, sway=-8)

    # dipper on top, overlapping the streams' source
    dipper(cv)

    # honey spilling off the comb's bottom edge into a shallow pool
    drip_stream(cv, 430, 930, 442, 968, 11, 8, sway=4)
    honey_pool(cv, 512, 1006, 290, 30)

    cv.vignette()

    out = resolve_output_path()
    try:
        size = write_png(cv, out)
    except OSError:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "entry.png")
        size = write_png(cv, out)
    print("wrote", out, size, "bytes")


if __name__ == "__main__":
    main()
