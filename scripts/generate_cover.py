import math
from PIL import Image, ImageDraw, ImageFont

SIZE = 1400
PAPER = (246, 223, 199)
INK = (28, 27, 26)
INK_SOFT = (74, 69, 63)
RED = (179, 34, 42)
RULE = (201, 169, 138)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

def F(path, sz):
    return ImageFont.truetype(path, sz)

img = Image.new("RGB", (SIZE, SIZE), PAPER)
d = ImageDraw.Draw(img)

def ctext(y, text, font, fill, tracking=0):
    if tracking == 0:
        bbox = d.textbbox((0, 0), text, font=font)
        d.text(((SIZE - (bbox[2] - bbox[0])) / 2 - bbox[0], y), text, font=font, fill=fill)
        return
    widths = [d.textbbox((0, 0), ch, font=font)[2] for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (SIZE - total) / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking

# frame
frame_m = 46
d.rectangle([frame_m, frame_m, SIZE - frame_m, SIZE - frame_m], outline=INK, width=4)
d.rectangle([frame_m + 16, frame_m + 16, SIZE - frame_m - 16, SIZE - frame_m - 16], outline=INK, width=1)

# subtle column rules
for i in range(1, 6):
    x = int(SIZE / 6 * i)
    d.line([(x, 90), (x, SIZE - 90)], fill=RULE, width=2)

# top kicker - big, bold, ink, tracked caps
kicker_font = F(SERIF_B, 46)
ctext(118, "CADA MAÑANA", kicker_font, INK, tracking=10)

d.rectangle([120, 205, SIZE - 120, 213], fill=INK)
d.rectangle([120, 223, SIZE - 120, 227], fill=INK)

# ---------- illustration: newspaper stack + coffee cup + cigarette + smoke ----------
cx = SIZE / 2

# newspaper stack (three offset rectangles)
stack_w, stack_h = 628, 29
stack_cy = 755
for i, off in enumerate([26, 13, 0]):
    y = stack_cy + off
    x0 = cx - stack_w / 2 + (i * 10 - 10)
    x1 = cx + stack_w / 2 + (i * 10 - 10)
    d.rectangle([x0, y, x1, y + stack_h], fill=PAPER, outline=INK, width=4)
    # fold rule + a few text-hint lines on the top paper only
    if off == 0:
        d.line([(x0 + 24, y + 8), (x1 - 24, y + 8)], fill=INK, width=3)

# coffee cup (left of center)
cup_cx, cup_top, cup_h, cup_w_top, cup_w_bot = cx - 168, 528, 213, 224, 188
cup_bottom = cup_top + cup_h
# saucer
d.ellipse([cup_cx - cup_w_top/2 - 26, cup_bottom - 14, cup_cx + cup_w_top/2 + 26, cup_bottom + 34], fill=INK)
# cup body (trapezoid)
d.polygon([
    (cup_cx - cup_w_top/2, cup_top),
    (cup_cx + cup_w_top/2, cup_top),
    (cup_cx + cup_w_bot/2, cup_bottom),
    (cup_cx - cup_w_bot/2, cup_bottom),
], fill=INK)
# coffee surface (red accent ellipse)
d.ellipse([cup_cx - cup_w_top/2 + 14, cup_top - 12, cup_cx + cup_w_top/2 - 14, cup_top + 24], fill=RED)
# handle
handle_cx = cup_cx + cup_w_top/2 + 51
d.ellipse([handle_cx - 51, cup_top + 45, handle_cx + 51, cup_top + 148], outline=INK, width=24)

def smoke(path_points, base_w):
    n = len(path_points)
    for i in range(n - 1):
        x0, y0 = path_points[i]
        x1, y1 = path_points[i + 1]
        w = max(2, base_w * (1 - i / n))
        d.line([(x0, y0), (x1, y1)], fill=INK_SOFT, width=int(w))

def smoke_path(x0, y0, height, amp, turns, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        y = y0 - height * t
        x = x0 + amp * math.sin(t * turns * math.pi) * (0.4 + 0.6 * t)
        pts.append((x, y))
    return pts

# smoke from coffee
smoke(smoke_path(cup_cx, cup_top - 24, 250, 36, 2.4), 15)

# cigarette (right of center, resting diagonally on the stack)
cig_x0, cig_y0 = cx + 60, stack_cy - 30
cig_x1, cig_y1 = cx + 372, stack_cy - 172
CW = 22  # cigarette body width (slim, not matchstick-thick)

def cig_pt(t):
    return (cig_x0 + (cig_x1 - cig_x0) * t, cig_y0 + (cig_y1 - cig_y0) * t)

# ink outline stroke (slightly wider, drawn first)
d.line([cig_pt(0), cig_pt(0.9)], fill=INK, width=CW + 5)
# white paper body
d.line([cig_pt(0.005), cig_pt(0.895)], fill=PAPER, width=CW)
# tan/cork filter band near the mouth end
filt_a, filt_b = cig_pt(0.0), cig_pt(0.22)
d.line([filt_a, filt_b], fill=(184, 138, 90), width=CW)
d.line([filt_a, filt_b], fill=INK, width=CW + 5)
d.line([cig_pt(0.008), cig_pt(0.212)], fill=(184, 138, 90), width=CW - 5)
# thin ink ring separating filter from paper body
ring = cig_pt(0.22)
perp = (-(cig_y1 - cig_y0), (cig_x1 - cig_x0))
plen = (perp[0] ** 2 + perp[1] ** 2) ** 0.5
pux, puy = perp[0] / plen, perp[1] / plen
d.line([(ring[0] - pux * CW / 2, ring[1] - puy * CW / 2),
        (ring[0] + pux * CW / 2, ring[1] + puy * CW / 2)], fill=INK, width=4)
# grey ash tip at the very end
ash = cig_pt(0.93)
d.ellipse([ash[0] - CW / 2 - 2, ash[1] - CW / 2 - 2, ash[0] + CW / 2 + 2, ash[1] + CW / 2 + 2], fill=(150, 145, 138))
# small glowing ember (subtler than before, not a big match-head ball)
ember = cig_pt(0.885)
d.ellipse([ember[0] - 11, ember[1] - 11, ember[0] + 11, ember[1] + 11], fill=RED)
# smoke from cigarette
smoke(smoke_path(cig_x1, cig_y1 - 15, 280, 33, 2.1), 12)

# ---------- wordmark plate ----------
plate_top, plate_bot = 900, 1150
d.rectangle([90, plate_top, SIZE - 90, plate_bot], fill=INK)
word_font = F(SERIF_B, 190)
bbox = d.textbbox((0, 0), "CMNEWS", font=word_font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((SIZE - w) / 2 - bbox[0], (plate_top + plate_bot) / 2 - h / 2 - bbox[1]), "CMNEWS", font=word_font, fill=PAPER)
d.rectangle([90, plate_bot + 14, SIZE - 90, plate_bot + 20], fill=RED)

# ---------- bottom strap ----------
strap_text = "GEOPOLÍTICA · ECONOMÍA · DEPORTES · CIENCIA"
strap_size = 40
while True:
    strap_font = F(SERIF_B, strap_size)
    bbox = d.textbbox((0, 0), strap_text, font=strap_font)
    if bbox[2] - bbox[0] <= SIZE - 260 or strap_size <= 24:
        break
    strap_size -= 2
ctext(SIZE - 195, strap_text, strap_font, INK, tracking=3)

d.rectangle([120, SIZE - 108, SIZE - 120, SIZE - 102], fill=INK)
d.rectangle([120, SIZE - 90, SIZE - 120, SIZE - 86], fill=INK)

img.save("/workspace/cmnews-podcast/cover-v2.jpg", quality=95)
print("saved", img.size)
