#!/usr/bin/env python3
"""Procedural VFX textures for WordEngine Effects (Pillow + numpy). Deterministic (fixed seeds).

    python3 assets/textures/generate.py            # writes assets/textures/*.png

Conventions (Roblox particle/beam best practice):
- White/greyscale art on transparent alpha so ParticleEmitter.Color / Beam.Color tint it per element.
- Soft alpha falloff to the edge (no hard sprite borders), transparent padding between flipbook frames.
- Flipbooks are 1024x1024 Grid4x4 (16 frames of 256px), the smallest layout that still reads on phones.
- Sizes are powers of two. Every file is listed in docs/manual/vfx.md and Effects/Assets.luau.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(1337)


def save(name, rgba):
    if isinstance(rgba, np.ndarray):
        rgba = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
    rgba.save(os.path.join(OUT, name + ".png"), optimize=True)


def grid(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    return (x - c) / c, (y - c) / c  # -1..1


def white(alpha, rgb=(255, 255, 255)):
    h, w = alpha.shape
    out = np.zeros((h, w, 4), np.float32)
    out[..., 0], out[..., 1], out[..., 2] = rgb
    out[..., 3] = np.clip(alpha, 0, 1) * 255
    return out


def value_noise(n, scale, seed, octaves=4):
    """Tileable fractal value noise in 0..1."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((n, n), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = scale * (2 ** o)
        g = rng.random((cells, cells)).astype(np.float32)
        img = Image.fromarray((g * 255).astype(np.uint8), "L").resize((n, n), Image.BICUBIC)
        acc += np.asarray(img, np.float32) / 255 * amp
        total += amp
        amp *= 0.5
    return acc / total


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# --- singles -------------------------------------------------------------------------------------------------

def soft_glow():
    x, y = grid(256)
    r = np.sqrt(x * x + y * y)
    a = np.exp(-(r ** 2) * 4.5) * smoothstep(1.0, 0.85, r)
    save("glow", white(a))


def hard_glow():
    x, y = grid(256)
    r = np.sqrt(x * x + y * y)
    a = np.clip(1 - r, 0, 1) ** 1.2 + np.exp(-(r ** 2) * 30) * 0.6
    a *= smoothstep(1.0, 0.9, r)
    save("glow_core", white(np.clip(a, 0, 1)))


def spark():
    # elongated streak for VelocityParallel orientation; long axis is vertical (particle Y)
    x, y = grid(256)
    a = np.exp(-(x ** 2) * 180) * np.clip(1 - np.abs(y), 0, 1) ** 1.6
    a += np.exp(-(x ** 2 + (y * 0.5) ** 2) * 40) * 0.35
    save("spark", white(np.clip(a, 0, 1)))


def star():
    x, y = grid(256)
    r = np.sqrt(x * x + y * y)
    rays = np.exp(-np.abs(x) * 28) * np.clip(1 - np.abs(y), 0, 1) ** 2 + np.exp(-np.abs(y) * 28) * np.clip(1 - np.abs(x), 0, 1) ** 2
    d1, d2 = (x + y) / math.sqrt(2), (x - y) / math.sqrt(2)
    rays2 = (np.exp(-np.abs(d1) * 40) * np.clip(1 - np.abs(d2) * 1.6, 0, 1) ** 2 + np.exp(-np.abs(d2) * 40) * np.clip(1 - np.abs(d1) * 1.6, 0, 1) ** 2) * 0.45
    core = np.exp(-(r ** 2) * 60)
    save("star", white(np.clip(rays + rays2 + core, 0, 1)))


def burst():
    # radial impact flash with spikes
    n = 512
    x, y = grid(n)
    r = np.sqrt(x * x + y * y) + 1e-6
    th = np.arctan2(y, x)
    rng = np.random.default_rng(7)
    spikes = np.zeros_like(r)
    for _ in range(22):
        ang = rng.uniform(-math.pi, math.pi)
        width = rng.uniform(0.03, 0.09)
        length = rng.uniform(0.55, 0.98)
        d = np.angle(np.exp(1j * (th - ang)))
        spikes = np.maximum(spikes, np.exp(-(d / width) ** 2) * np.clip(1 - r / length, 0, 1))
    core = np.exp(-(r ** 2) * 14)
    a = np.clip(spikes * 0.9 + core, 0, 1) * smoothstep(1, 0.9, r)
    save("burst", white(a))


def ring():
    x, y = grid(512)
    r = np.sqrt(x * x + y * y)
    a = np.exp(-((r - 0.82) / 0.07) ** 2) + np.exp(-((r - 0.82) / 0.2) ** 2) * 0.35
    a *= smoothstep(1.0, 0.95, r)
    save("ring", white(np.clip(a, 0, 1)))


def shadow():
    x, y = grid(256)
    r = np.sqrt(x * x + y * y)
    a = (1 - smoothstep(0.15, 1.0, r)) ** 1.5 * 0.85
    save("shadow", white(a, (0, 0, 0)))


def scorch():
    n = 512
    x, y = grid(n)
    r = np.sqrt(x * x + y * y)
    nz = value_noise(n, 6, 11)
    edge = 0.72 + (nz - 0.5) * 0.45
    a = (1 - smoothstep(edge - 0.35, edge, r)) * (0.65 + nz * 0.35)
    streak_noise = value_noise(n, 3, 12, 3)
    a = np.clip(a * (0.8 + 0.4 * streak_noise), 0, 1) * smoothstep(1.0, 0.92, r)
    # warm char centre, near-black outside so it reads on any ground colour
    rgb = np.zeros((n, n, 3), np.float32)
    rgb[..., 0] = 20 + 30 * (1 - r).clip(0, 1)
    rgb[..., 1] = 14 + 10 * (1 - r).clip(0, 1)
    rgb[..., 2] = 10
    out = np.dstack([rgb, a * 255])
    save("scorch", out)


def crack():
    n = 512
    img = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(21)
    c = n / 2

    def branch(x, y, ang, length, w, depth):
        while length > 0 and w >= 1:
            step = rng.uniform(10, 24)
            ang += rng.uniform(-0.45, 0.45)
            nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
            if math.hypot(nx - c, ny - c) > c * 0.95:
                return
            d.line([(x, y), (nx, ny)], fill=255, width=int(w))
            x, y, length = nx, ny, length - step
            w *= 0.93
            if depth < 2 and rng.random() < 0.18:
                branch(x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1), length * 0.5, w * 0.7, depth + 1)

    for i in range(9):
        a0 = i / 9 * math.tau + rng.uniform(-0.2, 0.2)
        branch(c, c, a0, rng.uniform(150, 240), 9, 0)
    d.ellipse([c - 22, c - 22, c + 22, c + 22], fill=200)
    blurred = img.filter(ImageFilter.GaussianBlur(2.2))
    a = np.asarray(blurred, np.float32) / 255
    out = white(np.clip(a * 1.3, 0, 1), (18, 12, 8))
    save("crack", out)


def frost():
    n = 512
    x, y = grid(n)
    r = np.sqrt(x * x + y * y)
    nz = value_noise(n, 10, 31, 5)
    img = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(32)
    for _ in range(140):  # little frost ferns
        cx, cy = rng.uniform(0.1, 0.9) * n, rng.uniform(0.1, 0.9) * n
        ang = rng.uniform(0, math.tau)
        L = rng.uniform(12, 40)
        ex, ey = cx + math.cos(ang) * L, cy + math.sin(ang) * L
        d.line([(cx, cy), (ex, ey)], fill=255, width=2)
        for k in range(1, 4):
            px, py = cx + (ex - cx) * k / 4, cy + (ey - cy) * k / 4
            for s in (-1, 1):
                a2 = ang + s * 0.7
                d.line([(px, py), (px + math.cos(a2) * L * 0.3, py + math.sin(a2) * L * 0.3)], fill=200, width=1)
    ferns = np.asarray(img.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    a = (0.35 * nz + 0.75 * ferns) * (1 - smoothstep(0.55, 1.0, r + (nz - 0.5) * 0.3))
    save("frost", white(np.clip(a, 0, 1)))


def rune_circle():
    n = 1024
    img = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(img)
    c = n / 2
    for rad, w in ((0.94, 6), (0.86, 3), (0.62, 4), (0.56, 2), (0.3, 3)):
        R = c * rad
        d.ellipse([c - R, c - R, c + R, c + R], outline=255, width=w)
    # glyph band between 0.86 and 0.94
    rng = np.random.default_rng(41)
    for i in range(36):
        a = i / 36 * math.tau
        R = c * 0.9
        gx, gy = c + math.cos(a) * R, c + math.sin(a) * R
        for _ in range(3):
            ox, oy = rng.uniform(-12, 12), rng.uniform(-12, 12)
            ox2, oy2 = rng.uniform(-12, 12), rng.uniform(-12, 12)
            d.line([(gx + ox, gy + oy), (gx + ox2, gy + oy2)], fill=255, width=3)
    # hexagram
    for k in range(2):
        pts = []
        for i in range(3):
            a = math.pi / 2 + i * math.tau / 3 + k * math.pi
            pts.append((c + math.cos(a) * c * 0.62, c + math.sin(a) * c * 0.62))
        d.polygon(pts, outline=255, width=4)
    # small orbiting circles
    for i in range(6):
        a = i / 6 * math.tau + math.pi / 6
        R = c * 0.74
        gx, gy = c + math.cos(a) * R, c + math.sin(a) * R
        d.ellipse([gx - 26, gy - 26, gx + 26, gy + 26], outline=255, width=3)
    sharp = np.asarray(img, np.float32) / 255
    glow = np.asarray(img.filter(ImageFilter.GaussianBlur(9)), np.float32) / 255
    save("rune_circle", white(np.clip(sharp + glow * 0.9, 0, 1)))


def glyph(d, cx, cy, s, rng):
    pts = [(cx + rng.uniform(-s, s), cy + rng.uniform(-s, s)) for _ in range(rng.integers(3, 6))]
    d.line(pts, fill=255, width=max(3, int(s / 6)), joint="curve")
    if rng.random() < 0.6:
        R = s * rng.uniform(0.2, 0.4)
        ox, oy = rng.uniform(-s / 2, s / 2), rng.uniform(-s / 2, s / 2)
        d.ellipse([cx + ox - R, cy + oy - R, cx + ox + R, cy + oy + R], outline=255, width=max(2, int(s / 8)))


def runes_sheet():
    n, cells = 1024, 4
    f = n // cells
    img = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(42)
    for i in range(cells * cells):
        cx, cy = (i % cells) * f + f / 2, (i // cells) * f + f / 2
        glyph(d, cx, cy, f * 0.28, rng)
    sharp = np.asarray(img, np.float32) / 255
    glow = np.asarray(img.filter(ImageFilter.GaussianBlur(7)), np.float32) / 255
    save("runes_4x4", white(np.clip(sharp + glow * 0.8, 0, 1)))


def shape_icon(name, draw_fn, n=256, blur=1.2, glow=0.0):
    img = Image.new("L", (n, n), 0)
    draw_fn(ImageDraw.Draw(img), n)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255
    if glow:
        a = a + np.asarray(img.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255 * glow
    save(name, white(np.clip(a, 0, 1)))


def snowflake(d, n):
    c = n / 2
    for i in range(6):
        a = i / 6 * math.tau
        ex, ey = c + math.cos(a) * n * 0.42, c + math.sin(a) * n * 0.42
        d.line([(c, c), (ex, ey)], fill=255, width=10)
        for k in (0.45, 0.7):
            px, py = c + math.cos(a) * n * 0.42 * k, c + math.sin(a) * n * 0.42 * k
            for s in (-1, 1):
                a2 = a + s * 0.75
                d.line([(px, py), (px + math.cos(a2) * n * 0.12, py + math.sin(a2) * n * 0.12)], fill=255, width=7)
    d.ellipse([c - 16, c - 16, c + 16, c + 16], fill=255)


def shard(d, n):
    c = n / 2
    d.polygon([(c, n * 0.04), (c + n * 0.13, c), (c, n * 0.96), (c - n * 0.13, c)], fill=255)
    d.polygon([(c, n * 0.04), (c + n * 0.13, c), (c, c + 10)], fill=170)


def leaf(d, n):
    c = n / 2
    pts = []
    for i in range(41):
        t = i / 40
        y = n * 0.08 + t * n * 0.84
        w = math.sin(t * math.pi) ** 0.8 * n * 0.26
        pts.append((c + w, y))
    for i in range(40, -1, -1):
        t = i / 40
        y = n * 0.08 + t * n * 0.84
        w = math.sin(t * math.pi) ** 0.8 * n * 0.26
        pts.append((c - w, y))
    d.polygon(pts, fill=230)
    d.line([(c, n * 0.1), (c, n * 0.95)], fill=255, width=6)
    for k in range(1, 6):
        y = n * 0.12 + k * n * 0.13
        d.line([(c, y + 20), (c + n * 0.17, y - 10)], fill=255, width=3)
        d.line([(c, y + 20), (c - n * 0.17, y - 10)], fill=255, width=3)


def petal(d, n):
    c = n / 2
    d.ellipse([c - n * 0.2, n * 0.1, c + n * 0.2, n * 0.9], fill=255)
    d.polygon([(c - n * 0.08, n * 0.1), (c, n * 0.2), (c + n * 0.08, n * 0.1)], fill=0)


def heart(d, n):
    c = n / 2
    r = n * 0.2
    d.ellipse([c - 2 * r + 6, n * 0.22, c + 6, n * 0.22 + 2 * r], fill=255)
    d.ellipse([c - 6, n * 0.22, c + 2 * r - 6, n * 0.22 + 2 * r], fill=255)
    d.polygon([(c - 2 * r + 8, n * 0.22 + r * 1.25), (c + 2 * r - 8, n * 0.22 + r * 1.25), (c, n * 0.86)], fill=255)


def arrow_down(d, n):
    c = n / 2
    d.rectangle([c - n * 0.09, n * 0.1, c + n * 0.09, n * 0.58], fill=255)
    d.polygon([(c - n * 0.28, n * 0.52), (c + n * 0.28, n * 0.52), (c, n * 0.92)], fill=255)


def plus(d, n):
    c = n / 2
    d.rounded_rectangle([c - n * 0.11, n * 0.12, c + n * 0.11, n * 0.88], radius=12, fill=255)
    d.rounded_rectangle([n * 0.12, c - n * 0.11, n * 0.88, c + n * 0.11], radius=12, fill=255)


def music_note(d, n):
    # eighth note: head + stem + flag
    d.ellipse([n * 0.18, n * 0.62, n * 0.5, n * 0.86], fill=255)
    d.rectangle([n * 0.44, n * 0.14, n * 0.5, n * 0.76], fill=255)
    d.polygon([(n * 0.5, n * 0.14), (n * 0.78, n * 0.3), (n * 0.76, n * 0.44), (n * 0.5, n * 0.3)], fill=255)


def zzz(d, n):
    for (x0, y0, s, w) in ((0.06, 0.6, 0.3, 15), (0.44, 0.34, 0.22, 11), (0.74, 0.1, 0.16, 8)):
        x0, y0, s = x0 * n, y0 * n, s * n
        d.line([(x0, y0), (x0 + s, y0), (x0, y0 + s), (x0 + s, y0 + s)], fill=255, width=w, joint="curve")


def question(d, n):
    c = n / 2
    d.arc([c - n * 0.24, n * 0.1, c + n * 0.24, n * 0.52], start=180, end=60, fill=255, width=26)
    d.line([(c + n * 0.11, n * 0.48), (c, n * 0.56), (c, n * 0.68)], fill=255, width=26, joint="curve")
    d.ellipse([c - 18, n * 0.78, c + 18, n * 0.78 + 36], fill=255)


def pixel(d, n):
    d.rectangle([n * 0.2, n * 0.2, n * 0.8, n * 0.8], fill=255)


def raindrop():
    x, y = grid(128)
    a = np.exp(-(x ** 2) * 220) * np.clip(1 - np.abs(y), 0, 1) ** 0.6
    save("raindrop", white(np.clip(a * 1.2, 0, 1)))


def bubble():
    x, y = grid(256)
    r = np.sqrt(x * x + y * y)
    rim = np.exp(-((r - 0.86) / 0.06) ** 2)
    fill = 0.12 * smoothstep(0.9, 0.0, r)
    hl = np.exp(-(((x + 0.35) ** 2 + (y + 0.35) ** 2) / 0.02)) * 0.9
    a = np.clip(rim + fill + hl, 0, 1) * smoothstep(1.0, 0.94, r)
    save("bubble", white(a))


def swirl():
    # curved wind streak (crescent) for tornado / wind / haste
    x, y = grid(256)
    r = np.sqrt(x * x + y * y)
    th = np.arctan2(y, x)
    band = np.exp(-((r - 0.7) / 0.06) ** 2)
    along = smoothstep(-2.6, 0.2, th) * smoothstep(1.6, 0.4, th)
    save("swirl", white(np.clip(band * along, 0, 1)))


def beam_tex(name, seed, jag):
    """Horizontally tileable beam texture: width across V, length along U."""
    w, h = 512, 128
    rng = np.random.default_rng(seed)
    yy = np.arange(h, dtype=np.float32)[:, None]
    if jag:
        # lightning: a jagged polyline whose ends meet at the centre line (tileable)
        img = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(img)
        pts, x = [(0, h / 2)], 0.0
        while x < w - 24:
            x += rng.uniform(14, 34)
            pts.append((min(x, w - 1), h / 2 + rng.uniform(-h * 0.33, h * 0.33)))
        pts.append((w, h / 2))
        d.line(pts, fill=255, width=7, joint="curve")
        for i in range(1, len(pts) - 1, 3):  # small forks
            px, py = pts[i]
            d.line([(px, py), (px + rng.uniform(10, 30), py + rng.uniform(-30, 30))], fill=200, width=3)
        core = np.asarray(img.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
        glow = np.asarray(img.filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
        a = np.clip(core + glow * 1.3, 0, 1)
    else:
        nz = value_noise(w, 8, seed, 4)[:h, :]
        nz = np.asarray(Image.fromarray((nz * 255).astype(np.uint8)).resize((w, h)), np.float32) / 255
        prof = np.exp(-((yy - h / 2) / (h * 0.22)) ** 2)
        core = np.exp(-((yy - h / 2) / (h * 0.07)) ** 2)
        a = np.clip(prof * (0.45 + 0.75 * nz) + core * 0.9, 0, 1)
        a = np.broadcast_to(a, (h, w))
    save(name, white(a))


# --- flipbooks -----------------------------------------------------------------------------------------------

def flipbook(name, frame_fn, cells=4, n=1024, pad=10):
    f = n // cells
    out = np.zeros((n, n, 4), np.float32)
    for i in range(cells * cells):
        frame = frame_fn(i / (cells * cells - 1), f - 2 * pad, i)
        cx, cy = (i % cells) * f + pad, (i // cells) * f + pad
        out[cy:cy + f - 2 * pad, cx:cx + f - 2 * pad] = frame
    save(name, out)


def smoke_frame(t, s, i):
    x, y = grid(s)
    r = np.sqrt(x * x + y * y)
    nz = value_noise(s, 4, 100 + i // 1, 5)
    nz2 = value_noise(s, 3, 500, 4)  # shared across frames: continuity
    blob = 1 - smoothstep(0.25 + t * 0.35, 0.95, r + (nz2 - 0.5) * 0.5)
    dens = blob * (0.55 + 0.6 * nz) * (1 - t * 0.55)
    a = np.clip(dens, 0, 1) * smoothstep(1.0, 0.85, r)
    shade = 0.75 + 0.25 * (1 - (y + 1) / 2)  # top lit
    return white(a, (255, 255, 255)) * np.dstack([shade, shade, shade, np.ones_like(shade)])


def flame_frame(t, s, i):
    x, y = grid(s)
    yy = (y + 1) / 2  # 0 top .. 1 bottom
    nz = value_noise(s, 3, 900 + i, 4)
    nz2 = value_noise(s, 5, 1900 + i, 3)
    phase = t * math.tau
    # teardrop: pointed licking tip, round base; tongues sway with time
    sway = (np.sin(yy * 5.0 - phase * 2) * 0.12 + (nz - 0.5) * 0.5) * (1 - yy) ** 1.5
    xs = x - sway
    w = 0.9 * np.clip(np.sin(math.pi * np.clip(yy, 0, 1) ** 2.4), 0, 1) ** 0.6 * 0.85 + 0.02
    d = np.abs(xs) / np.maximum(w, 1e-3)
    body = 1 - smoothstep(0.3, 1.0, d + (nz2 - 0.5) * 0.4)
    core = 1 - smoothstep(0.0, 0.55, d * 1.4 + (1 - yy) * 0.6)
    a = np.clip(body * (0.65 + 0.45 * nz) + core * 0.5, 0, 1)
    a *= smoothstep(1.0, 0.93, yy) * smoothstep(0.0, 0.06, yy)
    return white(a)


def main():
    os.makedirs(OUT, exist_ok=True)
    soft_glow(); hard_glow(); spark(); star(); burst(); ring(); shadow(); scorch(); crack(); frost()
    rune_circle(); runes_sheet(); raindrop(); bubble(); swirl()
    shape_icon("snowflake", snowflake, glow=0.5)
    shape_icon("shard", shard, blur=1.0, glow=0.4)
    shape_icon("leaf", leaf, blur=1.0)
    shape_icon("petal", petal, blur=1.5)
    shape_icon("heart", heart, blur=1.5, glow=0.4)
    shape_icon("arrow_down", arrow_down, blur=1.5, glow=0.4)
    shape_icon("plus", plus, blur=1.5, glow=0.5)
    shape_icon("music_note", music_note, blur=1.5, glow=0.4)
    shape_icon("zzz", zzz, blur=1.5, glow=0.4)
    shape_icon("question", question, blur=1.5, glow=0.4)
    shape_icon("pixel", pixel, n=64, blur=0.6)
    beam_tex("beam_lightning", 61, True)
    beam_tex("beam_energy", 62, False)
    flipbook("smoke_4x4", smoke_frame)
    flipbook("flame_4x4", flame_frame)
    print("textures written to", OUT)


if __name__ == "__main__":
    main()
