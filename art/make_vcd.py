"""Standalone prop: a late-90s black VCD player (front panel replicated from a period Samsung-style unit).
Drawn in REFERENCE units = pixels of the reference photo with the panel's top-left at (0, 0), so every
element can be measured straight off the photo; build() scales it to any size. The brand is invented
(BRAND) like the rest of the scene.
Output (standalone run): out/vcd.png + out/vcd_preview.png."""
import numpy as np
import skia
from common import *

BRAND = "HUAYIN"
PW, PH = 1595, 330             # front panel size (reference px)
FEET = ((70, 255), (1350, 1525))
FOOT_H = 30
TEAL = (70, 226, 214)
TEAL_DIM = (44, 150, 146)


def latin(size, bold=True, italic=False, family="Arial"):
    st = skia.FontStyle(700 if bold else 400, skia.FontStyle.kNormal_Width,
                        skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant)
    f = skia.Font(skia.Typeface.MakeFromName(family, st), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def grey(v, a=255):
    return C(v, v, v, a)


def bevel_rr(c, l, t, r, b, rad_, top, bot, hi=110, lo=0, well=None):
    """Raised plastic part: optional dark well around it, vertical face gradient, lit top edge."""
    if well is not None:
        c.drawRRect(rrect(l - well, t - well, r + well, b + well, rad_ + well), paint(grey(8)))
    c.drawRRect(rrect(l, t, r, b, rad_), paint(shader=lin(0, t, 0, b, [grey(top), grey((top + bot) // 2), grey(bot)], [0, .12, 1])))
    c.drawLine(l + rad_, t + 1, r - rad_, t + 1, paint(grey(hi, 200), stroke=1.6))
    c.drawLine(l + 1, t + rad_, l + 1, b - rad_, paint(grey(hi, 70), stroke=1.2))
    if lo:
        c.drawLine(l + rad_, b - .8, r - rad_, b - .8, paint(grey(lo, 200), stroke=1.4))


# ------------------------------------------------------------------ seven-segment VFD digits
_SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd",
        "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcfgd"}


def seg_digit(c, ch, x, y, h, col, ghost=True, skew=.12):
    """Italic 7-seg digit, (x, y) = bottom-left of the cell. Unlit segments faintly visible (real VFDs)."""
    w, t = h * .5, h * .12
    def P(px, py):
        return (x + px + skew * (h - py), y - h + py)
    segs = {
        "a": [(t * .6, 0), (w - t * .6, 0), (w - t * 1.5, t), (t * 1.5, t)],
        "d": [(t * 1.5, h - t), (w - t * 1.5, h - t), (w - t * .6, h), (t * .6, h)],
        "g": [(t * 1.2, h / 2), (t * 1.8, h / 2 - t / 2), (w - t * 1.8, h / 2 - t / 2), (w - t * 1.2, h / 2), (w - t * 1.8, h / 2 + t / 2), (t * 1.8, h / 2 + t / 2)],
        "f": [(0, t * .6), (t, t * 1.5), (t, h / 2 - t * .7), (t * .4, h / 2 - t * .2), (0, h / 2 - t * .5)],
        "b": [(w, t * .6), (w, h / 2 - t * .5), (w - t * .4, h / 2 - t * .2), (w - t, h / 2 - t * .7), (w - t, t * 1.5)],
        "e": [(0, h / 2 + t * .5), (t * .4, h / 2 + t * .2), (t, h / 2 + t * .7), (t, h - t * 1.5), (0, h - t * .6)],
        "c": [(w, h / 2 + t * .5), (w, h - t * .6), (w - t, h - t * 1.5), (w - t, h / 2 + t * .7), (w - t * .4, h / 2 + t * .2)],
    }
    lit = _SEG.get(ch, "")
    for k, pts in segs.items():
        p = skia.Path(); p.moveTo(*P(*pts[0]))
        for q in pts[1:]:
            p.lineTo(*P(*q))
        p.close()
        if k in lit:
            c.drawPath(p, paint(C(*col, 120), blur=3.5))
            c.drawPath(p, paint(C(*col)))
        elif ghost:
            c.drawPath(p, paint(C(*col, 7)))
    return w


def vfd_text(c, s, x, y, h, col):
    for ch in s:
        if ch == ":":
            for yy in (y - h * .3, y - h * .7):
                c.drawCircle(x + 4 + .12 * h * .5, yy, h * .065, paint(C(*col)))
            x += 10
        else:
            x += seg_digit(c, ch, x, y, h, col) + h * .18


# ------------------------------------------------------------------ icons
def icon(c, kind, cx, cy, s, p):
    def tri(x0, dirn=1, sc=1.0):
        q = skia.Path(); q.moveTo(x0, cy - s * sc); q.lineTo(x0 + dirn * s * 1.5 * sc, cy); q.lineTo(x0, cy + s * sc); q.close()
        c.drawPath(q, p)
    if kind == "play":
        tri(cx - s * .6)
    elif kind == "pause":
        c.drawRect(rect(cx - s * .75, cy - s, cx - s * .25, cy + s), p)
        c.drawRect(rect(cx + s * .25, cy - s, cx + s * .75, cy + s), p)
    elif kind == "stop":
        c.drawRect(rect(cx - s * .85, cy - s * .85, cx + s * .85, cy + s * .85), p)
    elif kind == "prev":
        c.drawRect(rect(cx - s * 1.7, cy - s * .8, cx - s * 1.4, cy + s * .8), p)
        tri(cx - s * .1, -1, .8); tri(cx + s * 1.1, -1, .8)
    elif kind == "next":
        tri(cx - s * 1.1, 1, .8); tri(cx + s * .1, 1, .8)
        c.drawRect(rect(cx + s * 1.4, cy - s * .8, cx + s * 1.7, cy + s * .8), p)


# ------------------------------------------------------------------ panel parts
def lid(c, depth, inset):
    """Top cover seen from above: narrows toward the back (perspective), lit front chamfer, a seam."""
    if depth <= 0:
        return
    p = skia.Path(); p.moveTo(4, 0); p.lineTo(PW - 4, 0); p.lineTo(PW - inset, -depth); p.lineTo(inset, -depth); p.close()
    c.drawPath(p, paint(shader=lin(0, -depth, 0, 0, [grey(50), grey(40), grey(33)], [0, .6, 1])))
    c.save(); c.clipPath(p, doAntiAlias=True)
    c.drawPaint(paint(shader=lin(0, 0, PW, 0, [C(255, 255, 255, 0), C(255, 255, 255, 14), C(255, 255, 255, 0)], [.1, .45, .9])))
    sy = -depth * .14
    c.drawLine(0, sy, PW, sy, paint(grey(14, 220), stroke=1.6))
    c.drawLine(0, sy + 1.6, PW, sy + 1.6, paint(grey(90, 90), stroke=1))
    c.restore()
    c.drawLine(inset, -depth + .5, PW - inset, -depth + .5, paint(grey(70, 120), stroke=1))


def feet(c):
    for l, r in FEET:
        c.drawOval(rect(l - 10, PH + FOOT_H - 8, r + 10, PH + FOOT_H + 10), paint(C(0, 0, 0, 150), blur=8))
        body = skia.Path(); body.addRect(rect(l, PH - 4, r, PH + FOOT_H - 6))
        body.addOval(rect(l, PH + FOOT_H - 14, r, PH + FOOT_H + 2))
        c.drawPath(body, paint(shader=lin(l, 0, r, 0,
            [grey(70), grey(150), grey(232), grey(250), grey(180), grey(105), grey(150), grey(200), grey(90)],
            [0, .08, .2, .26, .4, .6, .75, .9, 1])))
        c.drawRect(rect(l, PH - 4, r, PH + 6), paint(C(0, 0, 0, 170), blur=3))          # under-panel shade


def body(c):
    c.drawRRect(rrect(0, 0, PW, PH, 7), paint(shader=lin(0, 0, 0, PH, [grey(44), grey(30), grey(25), grey(21)], [0, .05, .5, 1])))
    c.drawRRect(rrect(1, 1, PW - 1, PH - 1, 6), paint(shader=lin(0, 0, 0, PH, [grey(150, 200), grey(60, 60), grey(0, 0), grey(110, 140)], [0, .02, .5, 1]), stroke=2))
    # very soft sheen across the panel (satin plastic)
    c.drawRRect(rrect(0, 0, PW, PH, 7), paint(shader=rad(PW * .35, -PH * .4, PW * .7, [C(255, 255, 255, 14), C(255, 255, 255, 0)])))


def left_section(c):
    text_center(c, BRAND, 128, 72, latin(31), paint(grey(0, 150), blur=1), spacing=2.4)
    text_center(c, BRAND, 127, 71, latin(31), paint(shader=lin(0, 48, 0, 72, [grey(208), grey(176), grey(150)])), spacing=2.4)
    text_center(c, "电源", 110, 112, font(15, "500"), paint(grey(214)))
    c.drawRRect(rrect(60, 129, 160, 179, 4), paint(C(0, 0, 0, 160), blur=4))
    bevel_rr(c, 62, 127, 157, 173, 3, 54, 22, hi=130, lo=12, well=2.5)
    c.drawLine(102, 150, 118, 150, paint(grey(80), stroke=1.6))
    text_center(c, "STANDBY", 193, 137, latin(7, bold=False), paint(grey(150)))
    c.drawCircle(193, 148, 6, paint(grey(6)))
    c.drawCircle(193, 148, 4.2, paint(shader=rad(192, 147, 5, [C(110, 40, 36), C(46, 14, 14)])))
    # format logos + codec
    c.save(); c.translate(72, 263); c.skew(-.18, 0)
    vf = latin(36, italic=False)
    c.drawString("VCD", 0, 0, vf, paint(grey(10), stroke=4))
    c.drawString("VCD", 0, 0, vf, paint(shader=lin(0, -28, 0, 0, [grey(250), grey(205)])))
    c.restore()
    c.drawRRect(rrect(70, 267, 146, 281, 2), paint(grey(225)))
    text_center(c, "VIDEO CD", 108, 278.5, latin(11), paint(grey(18)), spacing=.6)
    text_center(c, "COMPACT", 214, 238, latin(7), paint(grey(215)))
    df = skia.Font(skia.Typeface.MakeFromName("Times New Roman", skia.FontStyle.Bold()), 36)
    text_center(c, "disc", 206, 266, df, paint(grey(225), stroke=1.4))
    c.drawRect(rect(177, 270, 236, 282), paint(grey(225), stroke=1.2))
    text_center(c, "DIGITAL VIDEO", 206.5, 279.5, latin(7.5), paint(grey(225)))
    c.drawString("MPEG-1", 265, 265, latin(18, bold=False), paint(grey(208)))


def tray(c):
    c.drawRRect(rrect(424, 46, 1139, 154, 5), paint(grey(7)))
    c.drawRRect(rrect(429, 51, 1134, 149, 3), paint(C(0, 0, 0, 200), blur=3))
    bevel_rr(c, 430, 50, 1133, 147, 3, 46, 26, hi=125, lo=14)
    c.drawLine(424, 158, 1139, 158, paint(grey(62, 220), stroke=1.4))                 # lip under the door
    c.save(); c.translate(781, 103); c.skew(-.2, 0)
    vf = latin(33)
    w = vf.measureText("VCD")
    c.drawString("VCD", -w / 2 + 1, 1.2, vf, paint(grey(0, 200)))
    c.drawString("VCD", -w / 2, 0, vf, paint(shader=lin(0, -24, 0, 0, [grey(232), grey(196), grey(150)], [0, .5, 1])))
    c.restore()
    text_center(c, "VIDEO COMPACT DISC PLAYER", 781, 122, latin(13.5, bold=False), paint(grey(216)), spacing=1.4)


def vfd(c):
    c.drawRRect(rrect(427, 172, 1139, 301, 4), paint(grey(5)))
    c.drawRRect(rrect(433, 178, 1133, 295, 2), paint(shader=lin(0, 178, 0, 295, [C(20, 22, 24), C(9, 10, 11), C(6, 7, 8)], [0, .3, 1])))
    c.save(); c.clipRRect(rrect(433, 178, 1133, 295, 2), doAntiAlias=True)
    # VFD contents
    q = skia.Path(); q.moveTo(612, 216); q.lineTo(625, 224); q.lineTo(612, 232); q.close()
    c.drawPath(q, paint(C(*TEAL, 110), blur=3)); c.drawPath(q, paint(C(*TEAL)))
    seg_digit(c, "1", 718, 242, 28, TEAL)
    vfd_text(c, "0:00", 800, 242, 28, TEAL)
    text_center(c, "TRACK", 662, 261, latin(12, bold=False), paint(C(*TEAL_DIM)))
    text_center(c, "TIME", 923, 261, latin(12, bold=False), paint(C(*TEAL_DIM)))
    c.drawLine(708, 258, 718, 258, paint(C(*TEAL_DIM, 160), stroke=1.4))
    # smoked-glass reflections
    c.drawPaint(paint(shader=lin(433, 178, 760, 295, [C(255, 255, 255, 0), C(255, 255, 255, 16), C(255, 255, 255, 0)], [.25, .4, .55])))
    c.drawRect(rect(433, 178, 1133, 184), paint(C(0, 0, 0, 120), blur=3))
    c.restore()
    c.drawRRect(rrect(433, 178, 1133, 295, 2), paint(grey(70, 120), stroke=1))


def transport(c):
    c.drawRRect(rrect(1180, 65, 1550, 165, 5), paint(grey(6)))
    kinds = ["play", "pause", "stop", "prev", "next"]
    names = ["播放", "暂停", "停止", "上一首", "下一首"]
    lab = font(14.5)
    for i, (k, n) in enumerate(zip(kinds, names)):
        x0 = 1184 + i * 72.8
        bevel_rr(c, x0, 69, x0 + 70, 128, 2.5, 56, 30, hi=135, lo=12)
        icon(c, k, x0 + 35, 99, 8.5, paint(grey(212)))
        c.drawRRect(rrect(x0, 132, x0 + 70, 161, 2), paint(shader=lin(0, 132, 0, 161, [grey(52), grey(40)])))
        c.drawLine(x0 + 2, 133, x0 + 68, 133, paint(grey(100, 160), stroke=1))
        text_center(c, n, x0 + 35, 152, lab, paint(grey(226)))


def round_button(c, cx, cy, r):
    c.drawCircle(cx, cy, r + 3.5, paint(grey(6)))
    c.drawCircle(cx + 1, cy + 2.5, r, paint(C(0, 0, 0, 180), blur=2.5))
    c.drawCircle(cx, cy, r, paint(shader=rad(cx - r * .35, cy - r * .45, r * 1.5, [grey(66), grey(32), grey(18)], [0, .55, 1])))
    c.drawCircle(cx, cy, r - .8, paint(shader=lin(0, cy - r, 0, cy + r, [grey(140, 150), grey(0, 0), grey(0, 0)], [0, .4, 1]), stroke=1.2))


def right_section(c):
    lab = font(14.5); lp = paint(grey(214))
    text_center(c, "菜单", 1208, 226, lab, lp)
    text_center(c, "设置", 1279, 226, lab, lp)
    text_center(c, "快进 / 快退", 1395, 205, lab, lp)
    text_center(c, "耳机", 1518, 226, lab, lp)
    round_button(c, 1208, 259, 17)
    round_button(c, 1279, 259, 17)
    # shuttle pad
    cx, cy = 1395, 259
    c.drawCircle(cx, cy, 46, paint(grey(6)))
    c.drawCircle(cx, cy, 43, paint(shader=rad(cx - 14, cy - 18, 64, [grey(78), grey(40), grey(22)], [0, .5, 1])))
    c.drawCircle(cx, cy, 42, paint(shader=lin(0, cy - 42, 0, cy + 42, [grey(150, 160), grey(0, 0), grey(0, 0), grey(90, 90)], [0, .35, .8, 1]), stroke=1.4))
    c.drawCircle(cx, cy, 33, paint(shader=rad(cx - 8, cy - 10, 44, [grey(46), grey(22)])))
    for a in (45, 135, 225, 315):
        v = np.radians(a)
        c.drawLine(cx + 11 * np.cos(v), cy + 11 * np.sin(v), cx + 42 * np.cos(v), cy + 42 * np.sin(v), paint(grey(8), stroke=2))
    c.drawCircle(cx, cy, 10, paint(grey(10)))
    c.drawCircle(cx, cy, 7, paint(shader=rad(cx - 2, cy - 2, 9, [grey(70), grey(28)])))
    ap = paint(grey(150))
    for dirn, x in ((-1, cx - 26), (1, cx + 20)):
        for k in range(2):
            x0 = x + k * 6 * (1 if dirn > 0 else 1)
            q = skia.Path()
            if dirn < 0:
                q.moveTo(x0, cy); q.lineTo(x0 + 6, cy - 4); q.lineTo(x0 + 6, cy + 4)
            else:
                q.moveTo(x0 + 6, cy); q.lineTo(x0, cy - 4); q.lineTo(x0, cy + 4)
            q.close(); c.drawPath(q, ap)
    # headphone jack: brass bezel, black socket
    jx, jy = 1518, 263
    c.drawCircle(jx, jy, 21, paint(grey(6)))
    c.drawCircle(jx, jy, 19, paint(shader=lin(jx - 19, jy - 19, jx + 19, jy + 19, [C(236, 206, 140), C(176, 138, 64), C(98, 74, 30), C(190, 158, 90)], [0, .4, .75, 1])))
    c.drawCircle(jx, jy, 12.5, paint(grey(8)))
    c.drawCircle(jx, jy, 8.5, paint(shader=rad(jx - 2, jy - 2, 10, [grey(160), grey(70)]), stroke=2.2))
    c.drawCircle(jx, jy, 5, paint(grey(0)))


def build(width, lid_depth=60, lid_inset=40, pad=24):
    """Render the player so the FRONT PANEL is `width` px wide.
    lid_depth / lid_inset = how much of the top cover shows and how much it narrows (reference px).
    Returns (straight-alpha float RGBA, (x, y) of the panel's top-left inside the image)."""
    k = width / PW
    top = lid_depth + pad
    w = int(np.ceil((PW + 2 * pad) * k)); h = int(np.ceil((top + PH + FOOT_H + pad) * k))
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c = s.getCanvas(); c.clear(C(0, 0, 0, 0))
    c.scale(k, k); c.translate(pad, top)
    feet(c); lid(c, lid_depth, lid_inset); body(c)
    left_section(c); tray(c); vfd(c); transport(c); right_section(c)
    img = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    img = img.astype(np.float32) / 255
    img[..., :3] *= (1 + .018 * grain(h, w, 61))[..., None]                 # moulded-plastic grain
    return img, (pad * k, top * k)


if __name__ == "__main__":
    import os
    from PIL import Image
    os.makedirs("out", exist_ok=True)
    img, _ = build(PW)
    save_rgba(img, "out/vcd.png")
    bg = Image.new("RGBA", (img.shape[1], img.shape[0]), (180, 140, 100, 255))
    bg.alpha_composite(Image.open("out/vcd.png"))
    bg.convert("RGB").save("out/vcd_preview.png")
    print("saved", img.shape)
