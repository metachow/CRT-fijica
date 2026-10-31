"""Printed paper props for the wall: a 1990s/2000s-style 奖状 and a bank/credit-union wall calendar,
both rendered clean and then aged (yellowing, fading, stains, fly specks, a fold, dirty edges)."""
import math
import numpy as np
import skia
from PIL import Image, ImageFilter
from common import C, rect, rrect, paint, lin, rad, font, text_center, fbm, grain, SANS, SERIF


def _surf(w, h):
    return skia.Surface.MakeRaster(skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))


def _np(s):
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return a.astype(np.float32) / 255


def to_skimage(arr):
    a = (np.clip(arr, 0, 1) * 255 + .5).astype(np.uint8)
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)


# ---------------------------------------------------------------- 奖状
def _scroll_side(c, x0, y0, L, s):
    """One half of a gold acanthus-like scroll, growing to the right from (x0, y0)."""
    p = skia.Path(); p.moveTo(x0, y0)
    p.cubicTo(x0 + L * .28, y0 - 16 * s, x0 + L * .55, y0 + 16 * s, x0 + L * .86, y0 - 2 * s)
    p.cubicTo(x0 + L * .97, y0 - 8 * s, x0 + L * .97, y0 - 22 * s, x0 + L * .88, y0 - 22 * s)
    p.cubicTo(x0 + L * .82, y0 - 22 * s, x0 + L * .82, y0 - 13 * s, x0 + L * .88, y0 - 13 * s)
    leaves = []
    for k, (t, up) in enumerate([(.18, -1), (.36, 1), (.52, -1), (.68, 1)]):
        lx = x0 + L * t; ly = y0 + (6 * up) * s
        q = skia.Path(); q.moveTo(lx, ly)
        q.quadTo(lx + 10 * s, ly + up * 16 * s, lx + 22 * s, ly + up * 10 * s)
        q.quadTo(lx + 10 * s, ly + up * 4 * s, lx, ly)
        leaves.append(q)
    gold = C(214, 160, 40); white = C(255, 250, 228)
    c.drawPath(p, paint(gold, stroke=4.2 * s))
    c.drawPath(p, paint(white, stroke=1.6 * s))
    for q in leaves:
        c.drawPath(q, paint(gold)); c.drawPath(q, paint(white, stroke=1.1 * s))


def _scroll(c, cx, y, L, s=1.0):
    _scroll_side(c, cx, y, L, s)
    c.save(); c.translate(cx, 0); c.scale(-1, 1); c.translate(-cx, 0)
    _scroll_side(c, cx, y, L, s)
    c.restore()


def _peony(c, x, y, s=1.0):
    for ang in (200, 250, 300, 340):
        a = math.radians(ang)
        c.save(); c.translate(x + 22 * s * math.cos(a), y + 22 * s * math.sin(a)); c.rotate(ang + 90)
        c.drawOval(rect(-6 * s, -13 * s, 6 * s, 13 * s), paint(C(214, 120, 40)))
        c.restore()
    for k in range(9):
        a = k * 2 * math.pi / 9
        c.drawCircle(x + 11 * s * math.cos(a), y + 11 * s * math.sin(a), 9 * s, paint(C(222, 36, 32)))
    for k in range(6):
        a = k * 2 * math.pi / 6 + .3
        c.drawCircle(x + 6 * s * math.cos(a), y + 6 * s * math.sin(a), 6 * s, paint(C(196, 22, 24)))
    c.drawCircle(x, y, 5 * s, paint(C(250, 200, 80)))
    for k in range(3):
        c.drawCircle(x + (-26 + 26 * k) * s, y + 26 * s, 4 * s, paint(C(222, 36, 32)))


def _ribbon(c, cx, cy, s=1.0):
    red, dark = C(220, 30, 30), C(170, 16, 20)
    for m in (1, -1):
        c.save(); c.translate(cx + m * 34 * s, cy - 4 * s); c.rotate(m * 14)
        c.drawOval(rect(-40 * s, -15 * s, 40 * s, 15 * s), paint(red))
        c.drawOval(rect(-30 * s, -7 * s, 30 * s, 7 * s), paint(dark))
        c.restore()
        t = skia.Path(); t.moveTo(cx, cy)
        t.lineTo(cx + m * 96 * s, cy + 22 * s); t.lineTo(cx + m * 84 * s, cy + 32 * s); t.lineTo(cx + m * 92 * s, cy + 40 * s)
        t.lineTo(cx + m * 10 * s, cy + 12 * s); t.close()
        c.drawPath(t, paint(red))
    for k in range(10):
        a = k * 2 * math.pi / 10
        c.drawCircle(cx + 13 * s * math.cos(a), cy + 13 * s * math.sin(a), 8 * s, paint(dark))
    c.drawCircle(cx, cy, 12 * s, paint(C(206, 28, 28)))
    c.drawCircle(cx, cy, 5 * s, paint(dark))


def _emblem(c, cx, cy, r):
    """Generic gold sunburst rosette (deliberately not any official emblem)."""
    star = skia.Path()
    n = 32
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * .82
        a = -math.pi / 2 + i * math.pi / n
        (star.moveTo if i == 0 else star.lineTo)(cx + rr * math.cos(a), cy + rr * math.sin(a))
    star.close()
    c.drawPath(star, paint(C(150, 118, 46)))
    c.drawCircle(cx, cy, r * .66, paint(C(214, 176, 70)))
    c.drawCircle(cx, cy, r * .55, paint(C(214, 40, 32)))
    c.drawCircle(cx, cy, r * .55, paint(C(240, 200, 90), stroke=1.4))
    flower = skia.Path()
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        flower.addCircle(cx + r * .22 * math.cos(a), cy + r * .22 * math.sin(a), r * .16)
    c.drawPath(flower, paint(C(244, 206, 96)))
    c.drawCircle(cx, cy, r * .1, paint(C(214, 40, 32)))


def _handwrite(c, s, x, y, size, seed, color=C(32, 40, 88)):
    rng = np.random.default_rng(seed)
    f = font(size, "400", SERIF)
    for ch in s:
        sz = size * (1 + rng.uniform(-.06, .06))
        f.setSize(sz)
        c.save(); c.translate(x, y + rng.uniform(-1.4, 1.4)); c.rotate(rng.uniform(-5, 5))
        c.drawString(ch, 0, 0, f, paint(color))
        c.restore()
        x += f.measureText(ch) * (0.94 + rng.uniform(-.04, .06))


def certificate(w=440, h=320, seed=0, name="李小明", honor="三好学生", year="2003年1月", term="2002—2003学年度第一学期"):
    s = _surf(w, h); c = s.getCanvas()
    c.drawPaint(paint(shader=lin(0, 0, w, 0,
        [C(232, 108, 18), C(242, 150, 16), C(255, 232, 0), C(255, 240, 12), C(255, 232, 0), C(242, 150, 16), C(232, 108, 18)],
        [0, .12, .32, .5, .68, .88, 1])))
    for xx, sw in [(.075, 3.2), (.098, 2), (.118, 2)]:
        for x in (xx * w, (1 - xx) * w):
            c.drawLine(x, 0, x, h, paint(C(255, 255, 250), stroke=sw))
    # hollow red title with the rosette between the two characters
    tf = font(h * .155, "900")
    for ch, cx in (("奖", w * .30), ("状", w * .70)):
        text_center(c, ch, cx + 2, h * .225 + 2, tf, paint(C(190, 30, 24, 120)))
        text_center(c, ch, cx, h * .225, tf, paint(C(222, 28, 26), stroke=5))
        text_center(c, ch, cx, h * .225, tf, paint(C(255, 250, 236)))
    _emblem(c, w * .5, h * .145, h * .085)
    _scroll(c, w * .5, h * .285, w * .33, h / 320)
    _peony(c, w * .19, h * .74, h / 380); _peony(c, w * .81, h * .74, h / 380)
    _scroll(c, w * .5, h * .9, w * .34, h / 400)
    _ribbon(c, w * .5, h * .885, h / 420)
    # filled in by hand
    _handwrite(c, name + " 同学：", w * .2, h * .41, h * .052, seed)
    _handwrite(c, "在" + term + "中", w * .25, h * .50, h * .046, seed + 1)
    _handwrite(c, "被评为", w * .2, h * .585, h * .046, seed + 2)
    text_center(c, honor, w * .52, h * .68, font(h * .085, "900", SERIF), paint(C(30, 30, 40)), spacing=h * .02)
    _handwrite(c, "特发此状，以资鼓励。", w * .25, h * .76, h * .044, seed + 3)
    _handwrite(c, "红旗小学", w * .62, h * .8, h * .042, seed + 4)
    _handwrite(c, year, w * .62, h * .85, h * .038, seed + 5)
    sx, sy = w * .7, h * .81
    c.drawCircle(sx, sy, h * .075, paint(C(214, 24, 30, 175), stroke=2.6))
    st = skia.Path()
    for i in range(10):
        rr = h * .03 if i % 2 == 0 else h * .012
        a = -math.pi / 2 + i * math.pi / 5
        (st.moveTo if i == 0 else st.lineTo)(sx + rr * math.cos(a), sy + rr * math.sin(a))
    st.close(); c.drawPath(st, paint(C(214, 24, 30, 175)))
    return age(_np(s), seed, fold=True)


# ---------------------------------------------------------------- calendar
def _landscape(w, h, seed):
    """Small photographic-ish river valley for the calendar photo (numpy)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    sky = np.stack([.70 + .1 * yy / h, .78 + .06 * yy / h, .84 - .02 * yy / h], -1)
    img[:] = sky
    def ridge(base, amp, scale, s):
        n = fbm(1, w, scale, 4, s)[0]
        return base + amp * n
    layers = [(h * .30, h * .12, 90, (.48, .58, .60), 1), (h * .42, h * .10, 70, (.30, .44, .34), 2), (h * .55, h * .06, 50, (.20, .34, .20), 3)]
    tex = fbm(h, w, 6, 3, seed + 9)
    for base, amp, sc, col, k in layers:
        r = ridge(base, amp, sc, seed + k)
        m = yy >= r[None, :]
        shade = np.array(col) * (1 + .18 * tex[..., None] + .08 * fbm(h, w, 20, 3, seed + 10 + k)[..., None])
        img = np.where(m[..., None], shade, img)
        # aerial haze at the ridge line
        haze = np.exp(-np.clip(yy - r[None, :], 0, None) / 18) * m * .35
        img = img * (1 - haze[..., None]) + np.array([.80, .84, .86]) * haze[..., None]
    river_top = h * .74 + 10 * fbm(1, w, 120, 3, seed + 20)[0]
    rv = yy >= river_top[None, :]
    water = np.array([.52, .62, .62]) * (1 + .08 * fbm(h, w, 4, 2, seed + 21)[..., None]) + .1 * np.sin(yy / 2.3)[..., None] * .2
    img = np.where(rv[..., None], water, img)
    bank = (np.abs(yy - river_top[None, :]) < 3)
    img[bank] *= .7
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.8))
    a = np.asarray(im, np.float32) / 255
    return np.concatenate([a, np.ones((h, w, 1), np.float32)], -1)


LUNAR_MAR_2003 = {1: "廿九", 2: "三十", 3: "二月", 6: "惊蛰", 8: "妇女节", 12: "植树节", 21: "春分"}
_DAYS = "初一 初二 初三 初四 初五 初六 初七 初八 初九 初十 十一 十二 十三 十四 十五 十六 十七 十八 十九 二十 廿一 廿二 廿三 廿四 廿五 廿六 廿七 廿八 廿九 三十".split()


def calendar(w=380, h=840, seed=40):
    """March 2003 sheet (1 Mar 2003 = Saturday; 正月初一 = 1 Feb 2003, 二月初一 = 3 Mar 2003)."""
    s = _surf(w, h); c = s.getCanvas()
    c.drawPaint(paint(C(250, 248, 240)))
    ph = 430
    land = _landscape(w - 24, ph - 24, seed)
    c.drawImage(to_skimage(land), 12, 12)
    red = C(212, 30, 30); ink = C(30, 30, 30)
    c.drawString("3", 18, ph + 66, font(64, "900"), paint(red))
    c.drawString("月", 62, ph + 60, font(24, "900", SERIF), paint(red))
    c.drawString("MARCH", 62, ph + 32, font(14, "700"), paint(C(120, 120, 120)))
    rt = "2003  癸未年"; f = font(18, "700", SERIF)
    c.drawString(rt, w - 18 - f.measureText(rt), ph + 34, f, paint(ink))
    rt2 = "农历 正月 — 二月"; f2 = font(13, "400", SERIF)
    c.drawString(rt2, w - 18 - f2.measureText(rt2), ph + 58, f2, paint(C(90, 90, 90)))
    gx0, gy0 = 14, ph + 100; cw = (w - 28) / 7; rh = 44
    hf = font(15, "700", SERIF)
    for i, ch in enumerate("日一二三四五六"):
        text_center(c, ch, gx0 + cw * (i + .5), gy0, hf, paint(red if i in (0, 6) else ink))
    nf = font(25, "700"); lf = font(10, "400", SERIF); sf = font(14, "700")
    def lunar(d):
        return LUNAR_MAR_2003.get(d, _DAYS[d - 3] if d >= 3 else "")
    col, row = 6, 0
    for d in range(1, 30):
        cx = gx0 + cw * (col + .5); cy = gy0 + 36 + row * rh
        colr = red if col in (0, 6) or d in (8, 12) else ink
        if row == 4 and d in (23, 24):
            # 23/30 and 24/31 share a cell, as on real wall calendars
            c.drawString(str(d), cx - 22, cy - 4, sf, paint(colr))
            c.drawString(str(d + 7), cx + 2, cy + 10, sf, paint(colr))
            c.drawLine(cx + 6, cy - 18, cx - 6, cy + 10, paint(C(120, 120, 120), stroke=1))
        else:
            text_center(c, str(d), cx, cy, nf, paint(colr))
            text_center(c, lunar(d), cx, cy + 13, lf, paint(red if d in (6, 8, 12, 21) or col in (0, 6) else C(90, 90, 90)))
        col += 1
        if col == 7:
            col, row = 0, row + 1
    fy = gy0 + 36 + 5 * rh + 6
    c.drawLine(14, fy - 20, w - 14, fy - 20, paint(C(200, 200, 200), stroke=1))
    c.drawCircle(34, fy, 11, paint(C(206, 40, 30), stroke=3))
    c.drawCircle(34, fy, 4, paint(C(206, 40, 30)))
    c.drawString("城关农村信用合作社  敬赠", 54, fy + 5, font(14, "700", SERIF), paint(C(170, 30, 30)))
    return age(_np(s), seed, fold=False, fade=.22)


# ---------------------------------------------------------------- ageing
def age(arr, seed, fold=False, fade=.18):
    h, w = arr.shape[:2]
    rgb = arr[..., :3]
    lum = (rgb @ np.array([.3, .59, .11]))[..., None]
    rgb = rgb * .7 + lum * .3                                     # print fading
    rgb = rgb * np.array([1.0, .93, .78])                         # yellowing
    paper = np.array([.86, .78, .60])
    rgb = rgb * (1 - fade) + paper * fade
    st = np.clip(fbm(h, w, 70, 4, seed + 1) * 1.6 - .25, 0, 1)    # water / grease stains
    rgb *= 1 - .20 * st[..., None] * np.array([.55, .75, 1.0])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy])
    edge = np.exp(-d / 9) * (.6 + .4 * fbm(h, w, 15, 3, seed + 2))
    rgb *= 1 - .32 * edge[..., None]                              # dirty, handled edges
    rgb *= (1 - .12 * yy / h)[..., None]                          # dust settles at the top/bottom lip
    rng = np.random.default_rng(seed + 3)
    sp = np.zeros((h, w), np.float32)                             # fly specks (sparse, soft, brownish)
    n = int(w * h / 7000)
    sp[rng.integers(0, h, n), rng.integers(0, w, n)] = 1
    sp = np.asarray(Image.fromarray((sp * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.7)), np.float32) / 255 * 3
    rgb *= 1 - np.clip(sp, 0, .6)[..., None] * np.array([.8, .85, .95])
    if fold:
        fy = int(h * .5) + rng.integers(-6, 6)
        rgb[fy - 1:fy + 1] *= .82
        rgb[fy + 1:fy + 3] *= 1.05
        rgb[fy - 14:fy - 1] *= np.linspace(1, .95, 13)[:, None, None]
    rgb *= (1 + .02 * grain(h, w, seed + 4))[..., None]
    out = np.concatenate([np.clip(rgb, 0, 1), arr[..., 3:4]], -1)
    # small torn corner
    c = rng.integers(0, 4); tsz = rng.integers(8, 18)
    tri = (xx + yy) < tsz if c == 0 else ((w - 1 - xx) + yy) < tsz if c == 1 else (xx + (h - 1 - yy)) < tsz if c == 2 else ((w - 1 - xx) + (h - 1 - yy)) < tsz
    out[tri, 3] = 0
    return out
