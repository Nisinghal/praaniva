# The Praaniva lid artwork, redrawn from the product photo: a maroon field framed in ivory, flowering branches
# up both sides, a gold arch with hanging bells, the wordmark, and diyas glowing at the foot.
# Writes three maps: colour, normal (foil sits proud, ink sits in) and metal-roughness (gold foil is metal).
# Swap lidtop_col.png for the real print file whenever it's available.
import numpy as np, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT, FONTS = sys.argv[1], sys.argv[2]
S = 2048
rng = np.random.default_rng(11)
hexc = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
IVORY, MAROON, MAROON_D, GOLD = hexc('#efe4cc'), hexc('#8c1c22'), hexc('#5e0f15'), hexc('#d9a441')
CREAM = hexc('#f6e3c0')
LEAF = [hexc('#f26b2a'), hexc('#e8452c'), hexc('#f59a3c'), hexc('#d63a2f'), hexc('#ef7f6a'), hexc('#c62f2a')]
GREEN = [hexc('#2f6b35'), hexc('#3e7d3a')]

img = Image.new('RGB', (S, S), IVORY)
foil = Image.new('L', (S, S), 0)      # gold foil: raised and metallic
ink = Image.new('L', (S, S), 0)       # printed areas: pressed in a hair
d, fd, idr = ImageDraw.Draw(img, 'RGBA'), ImageDraw.Draw(foil), ImageDraw.Draw(ink)

# maroon field with a soft glow behind the wordmark and a deeper edge
M0 = int(S * .045)
yy, xx = np.mgrid[0:S, 0:S]
r = np.hypot((xx - S / 2) / S, (yy - S * .42) / S)
field = np.array(MAROON, float) * (1.08 - .55 * np.clip(r, 0, .75))[..., None]
field = field * (1 + .04 * rng.standard_normal((S, S, 1)))
arr = np.asarray(img).astype(float)
inside = (xx >= M0) & (xx < S - M0) & (yy >= M0) & (yy < S - M0)
arr[inside] = field[inside]
img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img, 'RGBA')
idr.rectangle([M0, M0, S - M0, S - M0], fill=255)

def gold_line(pts, w):
    d.line(pts, fill=GOLD, width=w); fd.line(pts, fill=255, width=w)
def gold_poly(pts):
    d.polygon(pts, fill=GOLD); fd.polygon(pts, fill=255)
m = M0 + 26
d.rectangle([m, m, S - m, S - m], outline=GOLD, width=6); fd.rectangle([m, m, S - m, S - m], outline=255, width=6)

def star(cx, cy, s, fill=GOLD, to_foil=True):
    pts = [(cx + (s if k % 2 == 0 else s * .2) * math.cos(k * math.pi / 4 - math.pi / 2),
            cy + (s if k % 2 == 0 else s * .2) * math.sin(k * math.pi / 4 - math.pi / 2)) for k in range(8)]
    d.polygon(pts, fill=fill)
    if to_foil: fd.polygon(pts, fill=255)

def leaf(cx, cy, length, width, ang, col, rib=True):
    pts = []
    for i in range(25):
        t = i / 24; w = width * math.sin(math.pi * t) ** .85
        pts.append((t * length, w))
    pts += [(t * length, -width * math.sin(math.pi * t) ** .85) for t in [i / 24 for i in range(24, -1, -1)]]
    ca, sa = math.cos(ang), math.sin(ang)
    P = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    d.polygon(P, fill=col + (255,))
    # a lighter half, as in the print's two-tone leaves
    half = P[:25] + [(cx + length * ca, cy + length * sa)]
    d.polygon(half + [(cx, cy)], fill=tuple(min(255, int(c * 1.12 + 12)) for c in col) + (255,))
    if rib: d.line([(cx, cy), (cx + length * .92 * ca, cy + length * .92 * sa)], fill=tuple(int(c * .7) for c in col) + (255,), width=4)

def flower(cx, cy, s, ang=0):
    for k in range(5):
        a = ang + k * 2 * math.pi / 5
        px, py = cx + math.cos(a) * s * .55, cy + math.sin(a) * s * .55
        d.ellipse([px - s * .5, py - s * .5, px + s * .5, py + s * .5], fill=(255, 248, 236, 255))
    d.ellipse([cx - s * .32, cy - s * .32, cx + s * .32, cy + s * .32], fill=(248, 196, 64, 255))
    d.ellipse([cx - s * .14, cy - s * .14, cx + s * .14, cy + s * .14], fill=(226, 92, 40, 255))

def branch(x0, y0, x1, y1, side, n):
    """A flowering branch climbing one side of the field."""
    pts = [(x0 + (x1 - x0) * t + side * 40 * math.sin(t * 6), y0 + (y1 - y0) * t) for t in np.linspace(0, 1, 30)]
    d.line(pts, fill=(120, 30, 25, 255), width=6)
    for i in range(n):
        t = (i + .5) / n; bx, by = pts[int(t * 29)]
        for k in range(2):
            ang = (-math.pi / 2 + side * (.5 + .7 * rng.random())) + (k * side * .9)
            big = 170 + 90 * rng.random()
            leaf(bx, by, big, big * .26, ang if side > 0 else math.pi - ang + math.pi, LEAF[rng.integers(len(LEAF))])
        if rng.random() < .35:
            g = 120 + 50 * rng.random(); leaf(bx, by, g, g * .22, -math.pi / 2 - side * .4 + rng.random() * .3, GREEN[rng.integers(2)])
        if rng.random() < .55:
            flower(bx + side * (60 + 60 * rng.random()), by - 40 + 80 * rng.random(), 46 + 18 * rng.random(), rng.random())
for side, x in ((1, M0 + 60), (-1, S - M0 - 60)):
    branch(x, S - M0 - 120, x + side * 30, M0 + 120, side, 11)

# the arch, hanging bells and scattered stars
cx = S / 2; ay, aw, ah = M0 + 290, 520, 230
arch = []
for i in range(81):
    t = i / 80; x = cx - aw + 2 * aw * t
    y = ay + ah * (1 - math.sin(math.pi * t) ** .55) - 70 * math.exp(-((t - .5) / .06) ** 2)  # pointed crown
    for c in (.22, .78):  # cusps
        y -= 22 * math.exp(-((t - c) / .035) ** 2)
    arch.append((x, y))
gold_line(arch, 7)
gold_line([(cx - aw, arch[0][1]), (cx - aw, ay + ah + 260)], 6); gold_line([(cx + aw, arch[-1][1]), (cx + aw, ay + ah + 260)], 6)
for bx in (cx - aw + 40, cx + aw - 40):
    by = ay + ah + 130
    gold_line([(bx, ay + ah - 80), (bx, by)], 4)
    gold_poly([(bx - 34, by + 62), (bx - 26, by + 8), (bx, by - 4), (bx + 26, by + 8), (bx + 34, by + 62)])
    d.ellipse([bx - 9, by + 58, bx + 9, by + 76], fill=GOLD); fd.ellipse([bx - 9, by + 58, bx + 9, by + 76], fill=255)
# a little lotus at the crown
for k in range(5):
    a = -math.pi / 2 + (k - 2) * .38
    leaf(cx, ay + 40, 70, 20, a, (238, 120, 60))
for _ in range(26):
    x, y = M0 + 260 + rng.random() * (S - 2 * M0 - 520), M0 + 160 + rng.random() * (S * .55)
    if abs(x - cx) < 420 and abs(y - S * .45) < 300: continue
    star(x, y, 10 + 14 * rng.random())

# the wordmark and lines, in gold foil
F = lambda n, s: ImageFont.truetype(f'{FONTS}/{n}', s)
def gtext(y, s, font, spacing=0, fill=CREAM, to_foil=True):
    w = sum(d.textlength(ch, font=font) for ch in s) + spacing * (len(s) - 1) if spacing else d.textlength(s, font=font)
    x = cx - w / 2
    if spacing:
        for ch in s:
            d.text((x, y), ch, font=font, fill=fill, anchor='ls')
            if to_foil: fd.text((x, y), ch, font=font, fill=255, anchor='ls')
            x += d.textlength(ch, font=font) + spacing
    else:
        d.text((cx, y), s, font=font, fill=fill, anchor='ms')
        if to_foil: fd.text((cx, y), s, font=font, fill=255, anchor='ms')
gtext(830, 'प्राणीवा', F('tiro-devanagari-hindi-devanagari-400-normal.woff', 250), fill=hexc('#f1d39a'))
gtext(905, 'PRAANIVA', F('hind-latin-500-normal.woff', 54), spacing=18, fill=hexc('#f1d39a'))
for y in (985, 1205):
    gold_line([(cx - 330, y), (cx - 30, y)], 4); gold_line([(cx + 30, y), (cx + 330, y)], 4); star(cx, y, 16)
gtext(1130, 'DAILY POOJA KIT', F('cormorant-garamond-latin-600-normal.woff', 130), spacing=6, fill=hexc('#f3d8a2'))
gtext(1300, 'ROOTED IN RITUAL', F('hind-latin-400-normal.woff', 46), spacing=14, fill=hexc('#efd9b6'), to_foil=False)
gtext(1370, 'CURATED WITH CARE', F('hind-latin-400-normal.woff', 46), spacing=14, fill=hexc('#efd9b6'), to_foil=False)

# the foot: waves of leaves, and diyas glowing
for i in range(26):
    x = M0 + 80 + i * (S - 2 * M0 - 160) / 25; y = S - M0 - 120 - 60 * math.sin(i * .7)
    leaf(x, y, 210, 50, -math.pi / 2 + (rng.random() - .5) * 1.6, LEAF[i % len(LEAF)])
def diya(x, y, s):
    glow = Image.new('L', (S, S), 0); ImageDraw.Draw(glow).ellipse([x - s * 2.6, y - s * 3.2, x + s * 2.6, y + s * .8], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(s * 1.1))
    a = np.asarray(img).astype(float); g = np.asarray(glow).astype(float)[..., None] / 255
    a = a + g * np.array([120, 70, 20]) * .9
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    dd = ImageDraw.Draw(img, 'RGBA')
    dd.chord([x - s * 1.3, y - s * .9, x + s * 1.3, y + s * .9], 0, 180, fill=(212, 120, 40, 255))
    for k in range(5): dd.line([(x - s + k * s / 2, y + s * .1), (x - s + k * s / 2, y + s * .6)], fill=(150, 70, 20, 255), width=max(2, int(s / 18)))
    dd.ellipse([x - s * 1.3, y - s * .25, x + s * 1.3, y + s * .25], fill=(236, 160, 60, 255))
    dd.polygon([(x, y - s * 1.9), (x + s * .32, y - s * .7), (x, y - s * .25), (x - s * .32, y - s * .7)], fill=(255, 214, 110, 255))
    dd.polygon([(x, y - s * 1.45), (x + s * .15, y - s * .7), (x, y - s * .4), (x - s * .15, y - s * .7)], fill=(255, 250, 225, 255))
    return dd
diya(cx, S - M0 - 260, 120); diya(cx - 520, S - M0 - 170, 60); diya(cx + 520, S - M0 - 170, 60)
d = ImageDraw.Draw(img, 'RGBA')
for x in (cx - 280, cx + 280, cx - 760, cx + 760): flower(x, S - M0 - 200 - 40 * math.sin(x), 50, x)

# --- maps ---
paper = (0.5 * np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((S, S))) * np.exp(-((np.hypot(np.fft.fftfreq(S)[:, None], np.fft.fftfreq(S)[None, :])) * 8) ** 2))))
paper = paper / paper.std()
col = np.asarray(img).astype(float) * (1 + .012 * paper[..., None])
Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(f'{OUT}/lidtop_col.png')
fm = np.asarray(foil.filter(ImageFilter.GaussianBlur(1.5))).astype(float) / 255
im_ = np.asarray(ink.filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
hgt = .35 * paper + .6 * fm - .25 * im_
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)); dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0))
n = np.dstack([-dx, dy, np.ones_like(hgt)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8)).save(f'{OUT}/lidtop_nrm.png')
# glTF metal-roughness: G = roughness, B = metallic. Foil: shiny metal. Print: satin. Ivory margin: matte paper
rough = .78 - .12 * im_ - .4 * fm
metal = fm
mr = np.dstack([np.zeros_like(rough), rough, metal])
Image.fromarray((np.clip(mr, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/lidtop_mr.png')
print('lid art ok')
