# Paper, print and lining textures for the Praaniva kit box.
# Every texture tiles (noise is filtered in frequency space), and each colour map gets a matching normal map.
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, sys

OUT = sys.argv[1]
FONTS = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

def tile_noise(h, w, scale, aniso=1.0):
    """Tileable noise: white noise, low-passed in frequency space (so it wraps)."""
    n = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt((fx * aniso) ** 2 + fy ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * np.exp(-(f * scale) ** 2)))
    return (out - out.mean()) / (out.std() + 1e-9)

def paper_height(h, w):
    # cotton-rag paper: soft cloud, fine tooth, and long fibres running one way
    return (0.55 * tile_noise(h, w, 60) + 0.35 * tile_noise(h, w, 6) +
            0.25 * tile_noise(h, w, 14, aniso=6.0) + 0.12 * tile_noise(h, w, 2))

def normal_from_height(hgt, strength):
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * strength
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * strength
    n = np.dstack([-dx, dy, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8))

def tint(hgt, rgb, amount):
    base = np.array(rgb, float)[None, None, :]
    return np.clip(base * (1 + amount * hgt[..., None]), 0, 255)

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

IVORY, TERRA, MUSTARD, INK = hexrgb('#efe5d0'), hexrgb('#994131'), hexrgb('#b8973a'), hexrgb('#4e3c35')

# --- plain ivory paper (lid sides, base bottom, rims) ---
S = 1024
hp = paper_height(S, S)
Image.fromarray(tint(hp, IVORY, .018).astype(np.uint8)).save(f'{OUT}/paper_col.png')
normal_from_height(hp, 1.6).save(f'{OUT}/paper_nrm.png')

# --- terracotta lining (inside the box and lid) ---
hl = paper_height(S, S)
Image.fromarray(tint(hl, TERRA, .03).astype(np.uint8)).save(f'{OUT}/lining_col.png')
normal_from_height(hl, 1.4).save(f'{OUT}/lining_nrm.png')

# --- base walls: ivory, with a terracotta band and a mustard hairline near the foot (v = 0 at the bottom) ---
W, H = 1024, 512
hb = paper_height(H, W)
col = tint(hb, IVORY, .018)
ink = np.zeros((H, W))
def band(v0, v1, rgb, a=1.0):
    r0, r1 = int((1 - v1) * H), int((1 - v0) * H)
    col[r0:r1] = col[r0:r1] * (1 - a) + np.array(rgb) * a * (1 + .03 * hb[r0:r1, :, None])
    ink[r0:r1] = 1
band(.075, .155, TERRA)
band(.185, .195, MUSTARD)
Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(f'{OUT}/wall_col.png')
normal_from_height(hb - .6 * ink, 1.6).save(f'{OUT}/wall_nrm.png')

# --- the lid's top: border, corner stars, the name, letterpressed ---
LW, LH = 2048, 1514  # same aspect as the lid (0.3066 x 0.2266 m)
ht = paper_height(LH, LW)
img = Image.fromarray(tint(ht, IVORY, .018).astype(np.uint8))
mask = Image.new('L', (LW, LH), 0)   # where ink sits: pressed slightly into the paper
d, m = ImageDraw.Draw(img), ImageDraw.Draw(mask)
def both(fn, *a, **k):
    fill = k.pop('fill'); fn(d)(*a, fill=fill, **k); fn(m)(*a, fill=255, **k)
px = LW / 0.3066  # pixels per metre
def rect(inset, width, rgb):
    i = int(inset * px)
    both(lambda dd: dd.rectangle, [i, i, LW - i, LH - i], outline=None, fill=None) if False else None
    d.rectangle([i, i, LW - i, LH - i], outline=rgb, width=width); m.rectangle([i, i, LW - i, LH - i], outline=255, width=width)
rect(.012, 16, TERRA)
rect(.018, 5, TERRA)
def star(cx, cy, s, rgb):
    pts = []
    import math
    for k in range(8):
        r = s if k % 2 == 0 else s * .22
        a = k * math.pi / 4 - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=rgb); m.polygon(pts, fill=255)
c = int(.018 * px)
for cx, cy in [(c, c), (LW - c, c), (c, LH - c), (LW - c, LH - c)]:
    star(cx, cy, 34, MUSTARD)

f = lambda name, size: ImageFont.truetype(f'{FONTS}/{name}', size)
cx = int(LW * .37)  # the name sits left of the ribbon, which runs down at 76% of the width
def text(y, s, font, rgb, spacing=0):
    if spacing:
        widths = [d.textlength(ch, font=font) for ch in s]
        x = cx - (sum(widths) + spacing * (len(s) - 1)) / 2
        for ch, w in zip(s, widths):
            d.text((x, y), ch, font=font, fill=rgb, anchor='ls'); m.text((x, y), ch, font=font, fill=255, anchor='ls'); x += w + spacing
    else:
        d.text((cx, y), s, font=font, fill=rgb, anchor='ms', features=['liga']); m.text((cx, y), s, font=font, fill=255, anchor='ms')
text(470, 'सम्पूर्ण', f('tiro-devanagari-hindi-devanagari-400-normal.woff', 96), MUSTARD)
text(740, 'Praaniva', f('cormorant-garamond-latin-700-normal.woff', 250), TERRA)
y = 830
d.line([cx - 300, y, cx - 50, y], fill=MUSTARD, width=5); m.line([cx - 300, y, cx - 50, y], fill=255, width=5)
d.line([cx + 50, y, cx + 300, y], fill=MUSTARD, width=5); m.line([cx + 50, y, cx + 300, y], fill=255, width=5)
star(cx, y, 26, MUSTARD)
text(965, 'SAMPOORNA BOX', f('hind-latin-500-normal.woff', 50), INK, spacing=16)
text(1090, 'Diwali Pooja Kit', f('cormorant-garamond-latin-500-italic.woff', 84), hexrgb('#6e5a52'))

# ink soaks in a touch: soften its edge, let the paper grain show through it
arr = np.asarray(img).astype(float)
inkm = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255
arr = arr * (1 + .05 * ht[..., None] * inkm[..., None])
Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{OUT}/lidtop_col.png')
press = np.asarray(mask.filter(ImageFilter.GaussianBlur(2.5))).astype(float) / 255
normal_from_height(ht - 2.2 * press, 1.5).save(f'{OUT}/lidtop_nrm.png')

# --- the backdrop for the preview render only: a red cotton cloth ---
C = 1024
warp, weft = tile_noise(C, C, 1.5, aniso=40), tile_noise(C, C, 1.5, aniso=1 / 40)
yy, xx = np.mgrid[0:C, 0:C]
weave = np.sin(xx * np.pi / 4) * np.sin(yy * np.pi / 4)
hc = .5 * weave + .25 * warp + .25 * weft + .3 * tile_noise(C, C, 40)
Image.fromarray(tint(hc, hexrgb('#8f141c'), .07).astype(np.uint8)).save(f'{OUT}/cloth_col.png')
normal_from_height(hc, 2.0).save(f'{OUT}/cloth_nrm.png')
print('textures ok')
