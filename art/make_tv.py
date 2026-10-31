"""TV housing layer: silver early-2000s Chinese family CRT (side speakers, lower control strip).
Output: out/tv_frame.png (4K RGBA, transparent screen cutout + transparent surroundings, includes cast shadows)."""
import numpy as np
import skia
from common import *

FACE = (430, 40, 3410, 1790); FACE_R = 34
BEV = 46
SPK_L = (470, 98, 790, 1734)
SPK_R = (3050, 98, 3370, 1734)
STRIP = (680, 1782, 3160, 1880)
BRAND = "XINGHUI"


def face_path():
    p = skia.Path()
    p.addRRect(rrect(*FACE, FACE_R))
    s = skia.Path(); s.addRRect(rrect(*STRIP, 16))
    return skia.Op(p, s, skia.PathOp.kUnion_PathOp)


def perforation_shader():
    t = 9
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(t, t, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c = s.getCanvas(); c.clear(C(0, 0, 0, 0))
    c.drawCircle(4.5, 5.2, 2.5, paint(C(235, 233, 227, 110)))   # lit lower lip of each hole
    c.drawCircle(4.5, 4.5, 2.3, paint(C(34, 33, 31, 245)))
    return s.makeImageSnapshot().makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat)


def speaker(c, box):
    l, t, r, b = box
    rr = rrect(l, t, r, b, 18)
    c.drawRRect(rr, paint(shader=lin(0, t, 0, b, [C(150, 147, 139), C(134, 131, 124), C(118, 115, 109)], [0, .5, 1])))
    c.save(); c.clipRRect(rr, doAntiAlias=True)
    # inner shadow on top / left (recessed panel, light from upper-left)
    frame = skia.Path(); frame.addRect(rect(l - 200, t - 200, r + 200, b + 200))
    hole = skia.Path(); hole.addRRect(rrect(l + 5, t + 8, r + 2, b + 3, 18))
    frame = skia.Op(frame, hole, skia.PathOp.kDifference_PathOp)
    c.drawPath(frame, paint(C(20, 20, 18, 150), blur=7))
    # perforated grille
    g = rrect(l + 20, t + 22, r - 20, b - 22, 10)
    c.save(); c.clipRRect(g, doAntiAlias=True)
    c.drawPaint(paint(shader=perforation_shader()))
    c.restore()
    c.restore()
    # lower/right lip highlight
    c.drawRRect(rrect(l + 1, t + 1, r - 1, b - 1, 17),
                paint(shader=lin(0, t, 0, b, [C(0, 0, 0, 90), C(0, 0, 0, 0), C(255, 255, 255, 120)], [0, .5, 1]), stroke=2.2))


def controls(c):
    lab = font(15, "500"); labp = paint(C(84, 82, 78))
    hi = paint(C(255, 255, 255, 110))
    cy = 1846
    def label(s, cx, y=1817):
        text_center(c, s, cx, y + 1.2, lab, hi)
        text_center(c, s, cx, y, lab, labp)
    # --- front AV input: a RECESSED bay holding a black insert; on it, protruding nickel RCA barrels with the
    #     colour-coded insulator INSIDE each barrel around the centre socket (video yellow, L white, R red)
    label("AV输入", 880)
    wl, wt, wr, wb = 808, 1825, 952, 1868
    c.drawRRect(rrect(wl, wt, wr, wb, 6), paint(shader=lin(0, wt, 0, wb, [C(20, 20, 21), C(32, 32, 34), C(38, 38, 40)])))
    c.save(); c.clipRRect(rrect(wl, wt, wr, wb, 6), doAntiAlias=True)          # inner shadow under the top lip
    frame = skia.Path(); frame.addRect(rect(wl - 40, wt - 40, wr + 40, wb + 40))
    frame = skia.Op(frame, skia.Path().addRRect(rrect(wl + 1, wt + 5, wr - 1, wb + 3, 6)), skia.PathOp.kDifference_PathOp)
    c.drawPath(frame, paint(C(0, 0, 0, 200), blur=4))
    c.restore()
    c.drawRRect(rrect(wl, wt, wr, wb, 6), paint(shader=lin(0, wt, 0, wb, [C(30, 28, 26, 220), C(0, 0, 0, 0), C(255, 255, 255, 160)], [0, .5, 1]), stroke=1.6))
    tag = skia.Font(skia.Typeface.MakeFromName("Arial", skia.FontStyle.Bold()), 8.5)
    for i, (col, name) in enumerate([((226, 184, 24), "VIDEO"), ((236, 236, 230), "L"), ((206, 40, 34), "R")]):
        x = 836 + 44 * i; y = cy + 5
        text_center(c, name, x, wt + 11.5, tag, paint(C(214, 214, 210)))
        c.drawCircle(x + 1.2, y + 2.4, 11.5, paint(C(0, 0, 0, 170), blur=2))                           # shadow on the insert
        c.drawCircle(x, y - 1.6, 10.5, paint(shader=lin(x - 10, 0, x + 10, 0, [C(150, 150, 148), C(96, 96, 94), C(60, 60, 58)])))  # barrel side (seen from above)
        c.drawCircle(x, y, 10.5, paint(shader=rad(x - 4, y - 5, 15, [C(246, 246, 242), C(178, 178, 174), C(104, 104, 100)], [0, .45, 1])))  # nickel face
        c.drawCircle(x, y, 10.5, paint(C(48, 48, 46, 200), stroke=.9))
        c.drawCircle(x, y, 7.4, paint(C(30, 30, 30)))                                                   # barrel mouth
        c.drawCircle(x, y + .6, 6.6, paint(shader=rad(x - 2, y - 2, 8, [C(*[min(255, int(v * 1.12)) for v in col]), C(*col), C(*[int(v * .55) for v in col])], [0, .5, 1])))  # insulator
        c.drawCircle(x, y + .6, 6.6, paint(C(0, 0, 0, 120), stroke=1.2, blur=.8))                       # it sits inside the barrel
        c.drawCircle(x, y + .6, 2.5, paint(C(10, 10, 10)))                                              # centre socket
        c.drawCircle(x - .6, y, .8, paint(C(220, 200, 150, 200)))
    # --- IR receiver window: smoked red acrylic with the receiver module visible behind it
    label("遥控接收", 1140)
    il, it, ir_, ib = 1104, cy - 12, 1176, cy + 12
    c.drawRect(rect(il - 1.5, it - 1.5, ir_ + 1.5, ib + 1.5), paint(C(52, 50, 46)))                      # cut in the panel
    c.drawLine(il - 1.5, ib + 2.2, ir_ + 1.5, ib + 2.2, paint(C(255, 255, 255, 120), stroke=1.2))
    c.drawRect(rect(il, it, ir_, ib), paint(shader=lin(0, it, 0, ib, [C(58, 10, 12), C(30, 4, 6), C(46, 8, 10)], [0, .55, 1])))
    c.save(); c.clipRect(rect(il, it, ir_, ib), doAntiAlias=True)
    c.drawRect(rect(1124, cy - 9, 1158, cy + 10), paint(C(18, 2, 4), blur=1.6))                         # receiver can + PCB, blurred by the tint
    c.drawRect(rect(il, cy + 6, ir_, ib), paint(C(70, 34, 12, 70)))
    c.drawCircle(1141, cy - 1, 6.5, paint(shader=rad(1139, cy - 3, 7, [C(150, 50, 46), C(64, 12, 12), C(30, 4, 6)], [0, .5, 1])))  # its lens dome
    c.drawCircle(1139, cy - 3.5, 1.6, paint(C(255, 200, 190, 110)))
    c.drawRect(rect(il, it, ir_, it + 5), paint(C(0, 0, 0, 120), blur=2.5))                              # recess shadow under the top edge
    p = skia.Path(); p.moveTo(il, it); p.lineTo(il + 34, it); p.lineTo(il + 18, ib); p.lineTo(il, ib); p.close()
    c.drawPath(p, paint(shader=lin(il, it, il + 30, ib, [C(255, 255, 255, 40), C(255, 255, 255, 4)]), blur=2))   # room reflection on the gloss
    c.restore()
    c.drawLine(il + 1, it + 1, ir_ - 1, it + 1, paint(C(255, 220, 215, 90), stroke=1))                   # polished edges
    c.drawLine(il + 1, ib - .8, ir_ - 1, ib - .8, paint(C(220, 70, 60, 120), stroke=1.2))
    label("电源指示", 1260)
    c.drawCircle(1260, cy, 11, paint(C(70, 255, 110, 80), blur=6))
    c.drawCircle(1260, cy, 6, paint(C(40, 40, 38)))
    c.drawCircle(1260, cy, 4.6, paint(shader=rad(1259, cy - 1, 5, [C(210, 255, 210), C(40, 200, 70)])))

    # --- piano-key style buttons standing PROUD of the strip (~3 mm). Seen from slightly above: the key's
    #     upper side shows as a thin lit band, the face sits a touch lower, a short shadow falls down-right.
    def key(x0, x1, y0, y1, lift=2.6, chrome=True):
        """Square-edged raised key. chrome: polished, so its face is a squashed reflection of the room —
        bright ceiling at the top, a dark horizon band, the warm cabinet below. Otherwise the housing plastic."""
        c.drawRect(rect(x0 + 1.5, y0 + lift + 2, x1 + 2.5, y1 + lift + 3.5), paint(C(30, 28, 24, 150), blur=2.6))   # cast shadow
        if not chrome:
            c.drawRect(rect(x0, y0, x1, y1 + lift), paint(shader=lin(0, y0, 0, y1 + lift, [C(216, 213, 204), C(150, 147, 140)])))
            c.drawLine(x0, y0 + .7, x1, y0 + .7, paint(C(250, 248, 240, 230), stroke=1.2))                          # upper side catches the light
            fy0, fy1 = y0 + lift, y1 + lift
            c.drawRect(rect(x0, fy0, x1, fy1), paint(shader=lin(0, fy0, 0, fy1, [C(196, 193, 184), C(178, 175, 167), C(160, 157, 150)], [0, .5, 1])))
            c.drawLine(x0, fy0 + .5, x1, fy0 + .5, paint(C(255, 255, 250, 150), stroke=1))
            c.drawLine(x0 + .5, fy0, x0 + .5, fy1, paint(C(255, 255, 250, 90), stroke=1))
            c.drawLine(x0, fy1 - .6, x1, fy1 - .6, paint(C(64, 62, 58, 210), stroke=1.2))
            return
        c.drawRect(rect(x0, y0, x1, y1 + lift), paint(shader=lin(0, y0, 0, y0 + lift, [C(255, 255, 255), C(206, 208, 212)])))  # upper side
        fy0, fy1 = y0 + lift, y1 + lift
        c.drawRect(rect(x0, fy0, x1, fy1), paint(shader=lin(0, fy0, 0, fy1,
                   [C(236, 238, 241), C(198, 201, 206), C(118, 120, 126), C(72, 72, 76), C(132, 120, 104), C(196, 190, 180)],
                   [0, .3, .46, .54, .68, 1])))
        c.drawRect(rect(x0, fy0, x1, fy1), paint(shader=lin(x0, 0, x1, 0,
                   [C(255, 255, 255, 0), C(255, 255, 255, 40), C(255, 255, 255, 0), C(0, 0, 0, 20)], [0, .25, .5, 1])))   # window glint across
        c.drawLine(x0, fy0 + .5, x1, fy0 + .5, paint(C(255, 255, 255, 240), stroke=1))                              # sharp edge highlight
        c.drawLine(x0, fy1 - .5, x1, fy1 - .5, paint(C(40, 40, 42, 220), stroke=1))
        c.drawLine(x0 + .5, fy0, x0 + .5, fy1, paint(C(255, 255, 255, 110), stroke=1))
        c.drawLine(x1 - .5, fy0, x1 - .5, fy1, paint(C(60, 60, 64, 160), stroke=1))
    kw, gap = 62, 4
    for gx, names in [(1700, ["菜单", "音量－", "音量＋"]), (2140, ["TV/AV", "频道－", "频道＋"])]:
        total = 3 * kw + 2 * gap
        x0 = gx - total / 2
        c.drawRect(rect(x0 - 4, cy - 12, x0 + total + 4, cy + 12), paint(C(96, 92, 85)))
        c.drawLine(x0 - 4, cy + 12.5, x0 + total + 4, cy + 12.5, paint(C(255, 255, 255, 110), stroke=1.2))
        for i, n in enumerate(names):
            kx = x0 + i * (kw + gap)
            key(kx, kx + kw, cy - 10, cy + 8)
            label(n, kx + kw / 2)
    # --- power: a big rectangular key with POWER printed on it
    label("电  源", 2960)
    c.drawRect(rect(2898, cy - 19, 3022, cy + 19), paint(C(96, 92, 85)))
    c.drawLine(2898, cy + 19.5, 3022, cy + 19.5, paint(C(255, 255, 255, 110), stroke=1.2))
    key(2902, 3018, cy - 17, cy + 13, chrome=False)
    text_center(c, "POWER", 2960, cy + 7.4, font(14, "700"), paint(C(70, 68, 64)))


def build():
    s = surface(); c = s.getCanvas(); c.clear(C(0, 0, 0, 0))
    fp = face_path()

    # ---- cast shadows (wall behind, cabinet top below)
    sh = skia.Path(fp); sh.offset(64, 40)
    c.drawPath(sh, paint(C(0, 0, 0, 150), blur=46))
    c.drawRRect(rrect(560, 1858, 3280, 1900, 20), paint(C(0, 0, 0, 160), blur=12))
    c.drawRRect(rrect(470, 1862, 3370, 1894, 16), paint(C(0, 0, 0, 120), blur=8))

    # ---- top of the cabinet shell, seen slightly from above
    top = skia.Path(); top.moveTo(596, 0); top.lineTo(3244, 0); top.lineTo(3384, 44); top.lineTo(456, 44); top.close()
    c.drawPath(top, paint(shader=lin(0, 0, 0, 44, [C(104, 103, 99), C(150, 148, 143)])))

    # ---- front face
    l, t, r, b = FACE
    face = rrect(*FACE, FACE_R)
    c.drawRRect(face, paint(shader=lin(0, t, 0, b, [C(204, 200, 190), C(186, 182, 172), C(158, 154, 146)], [0, .5, 1])))
    # metallic-paint sheen: broad soft highlight upper-left, falloff lower-right
    c.save(); c.clipRRect(face, doAntiAlias=True)
    c.drawPaint(paint(shader=rad(1100, 260, 1900, [C(255, 252, 244, 70), C(255, 252, 244, 0)])))
    c.drawPaint(paint(shader=lin(0, 0, W, H, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(40, 30, 20, 40)], [0, .55, 1])))
    c.restore()
    c.drawRRect(face, paint(shader=lin(l, 0, r, 0, [C(0, 0, 0, 46), C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 52)], [0, .1, .9, 1])))
    c.drawRRect(rrect(l + 3, t + 3, r - 3, b - 3, FACE_R - 3),
                paint(shader=lin(0, t, 0, b, [C(255, 255, 255, 170), C(255, 255, 255, 0), C(0, 0, 0, 0), C(0, 0, 0, 110)], [0, .06, .9, 1]), stroke=6))
    c.drawRRect(face, paint(C(58, 57, 54, 220), stroke=2))

    speaker(c, SPK_L); speaker(c, SPK_R)

    # ---- badges and branding
    c.save(); c.translate(842, 121); c.skew(-0.22, 0)
    f = font(36, "900")
    c.drawString("数码超平", 1.5, 1.5, f, paint(C(255, 255, 255, 120)))
    c.drawString("数码超平", 0, 0, f, paint(shader=lin(0, -32, 0, 4, [C(176, 40, 36), C(120, 18, 20)])))
    c.restore()
    small = font(15, "700")
    c.drawString("DIGITAL  SUPER FLAT", 1012, 120, small, paint(C(120, 118, 112)))
    rf = font(22, "700")
    s1 = "丽音  NICAM STEREO"
    c.drawString(s1, 3000 - rf.measureText(s1), 121, rf, paint(C(112, 110, 105)))
    # nameplate: a black-anodised aluminium badge proud of the face by ~1 mm; heavy wide letters in BRUSHED
    # silver (horizontal hairlines) nearly fill it, so the black shows only between letters and as a thin border
    bf = font(38, "900"); sp = 2.5
    tw = sum(bf.measureText(ch) for ch in BRAND) + sp * (len(BRAND) - 1)
    cap = -min(r.top() for r in bf.getBounds(bf.textToGlyphs(BRAND)))
    by = (1739 + 1776) / 2 + cap / 2                                                                  # centred between ring and strip
    # the black plate is die-cut along the letters: it starts at the FIRST letter's own left strokes and ends at the
    # LAST letter's right strokes (each row's outermost ink), black in between, all grown by a thin margin m
    m = 2.6
    glyphs, x = [], 1920 - tw / 2
    for ch in BRAND:
        g = bf.getPath(bf.textToGlyphs(ch)[0]); g.offset(x, by); glyphs.append(g)
        x += bf.measureText(ch) + sp
    def ink_edge(g, side, ss=8, step=.25):
        """Outermost ink x of glyph path g on each row (side -1 = left edge, +1 = right edge), from an
        ss-times supersampled raster -> one clean polyline (no stacks of unioned copies, no slivers)."""
        r = g.getBounds(); w, h = int(r.width() * ss) + 4, int(r.height() * ss) + 4
        sf = skia.Surface.MakeRaster(skia.ImageInfo.MakeA8(w, h)); cv = sf.getCanvas(); cv.clear(skia.ColorTRANSPARENT)
        cv.scale(ss, ss); cv.translate(-r.left() + 2 / ss, -r.top() + 2 / ss); cv.drawPath(g, skia.Paint(AntiAlias=True))
        a = sf.makeImageSnapshot().toarray(colorType=skia.kAlpha_8_ColorType).reshape(h, w)
        pts = []
        for y in np.arange(r.top(), r.bottom() + 1e-3, step):
            row = a[min(h - 1, int((y - r.top()) * ss + 2))]
            xs = np.nonzero(row > 127)[0]
            if len(xs):
                xi = xs[0] if side < 0 else xs[-1]
                pts.append((r.left() + (xi + (0 if side < 0 else 1) - 2) / ss, y))
        return pts
    left, right = ink_edge(glyphs[0], -1), ink_edge(glyphs[-1], 1)
    core = skia.Path(); core.moveTo(*left[0])
    for q in left[1:]:
        core.lineTo(*q)
    for q in reversed(right):
        core.lineTo(*q)
    core.close()
    grow = skia.Paint(); grow.setStyle(skia.Paint.kStrokeAndFill_Style); grow.setStrokeWidth(2 * m); grow.setStrokeJoin(skia.Paint.kRound_Join)
    plate = skia.Path(); grow.getFillPath(core, plate)
    plate = skia.Simplify(plate)                    # stroking leaves overlapping inner contours -> keep the outline only
    pb_ = plate.getBounds(); pl, pr, pt, pb = pb_.left(), pb_.right(), pb_.top(), pb_.bottom()
    sh = skia.Path(plate); sh.offset(1.2, 2.4)
    c.drawPath(sh, paint(C(40, 34, 26, 140), blur=1.8))                                               # stands off the face
    c.drawPath(plate, paint(shader=lin(0, pt, 0, pb, [C(36, 36, 38), C(17, 17, 19), C(10, 10, 11)], [0, .3, 1])))
    c.save(); c.clipPath(plate, doAntiAlias=True)                                                     # cut edge, lit top-left
    c.drawPath(plate, paint(shader=lin(pl, pt, pl + 40, pb, [C(215, 215, 218, 210), C(120, 120, 124, 120), C(60, 60, 62, 90)]), stroke=2.2))
    c.restore()
    text_center(c, BRAND, 1920, by - .7, bf, paint(C(255, 255, 255, 150)), spacing=sp)                 # lit top edge of the letters
    c.saveLayer()
    text_center(c, BRAND, 1920, by, bf, paint(shader=lin(0, by - cap, 0, by, [C(222, 223, 226), C(198, 199, 203), C(176, 177, 182)], [0, .5, 1])), spacing=sp)
    c.drawPaint(paint(shader=lin(pl, 0, pr, 0, [C(255, 255, 255, 0), C(255, 255, 255, 46), C(255, 255, 255, 0), C(255, 255, 255, 30), C(255, 255, 255, 0)],
                                 [0, .3, .5, .72, 1]), blend=skia.BlendMode.kSrcATop))                 # broad sheen of the brushing
    rng = np.random.default_rng(4)
    for y in np.arange(pt, pb, .55):                                                                  # hairlines
        v = int(rng.choice([255, 40])); a = int(rng.uniform(14, 60))
        x0 = pl + rng.uniform(-20, 40)
        c.drawLine(x0, y, x0 + rng.uniform(120, tw + 40), y, paint(C(v, v, v, a), stroke=.5, blend=skia.BlendMode.kSrcATop))
    c.restore()

    # ---- lower control strip (protrudes slightly)
    sl, st, sr, sb = STRIP
    strip = rrect(*STRIP, 16)
    c.drawRRect(strip, paint(shader=lin(0, st, 0, sb, [C(198, 194, 184), C(178, 174, 165), C(140, 137, 129)], [0, .45, 1])))
    c.drawLine(sl + 14, st + 2, sr - 14, st + 2, paint(C(255, 255, 255, 170), stroke=2.5))
    c.drawRRect(strip, paint(C(58, 57, 54, 210), stroke=2))
    c.drawRRect(rrect(sl + 2, st + 2, sr - 2, sb - 2, 14), paint(shader=lin(0, st, 0, sb, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 90)], [0, .7, 1]), stroke=4))
    controls(c)


    img = to_np(s)
    # paint grain + gentle global light falloff (upper-left key light)
    solid = img[..., 3] > 0.97
    n = 1 + 0.016 * grain(H, W, 1) + 0.012 * fbm(H, W, 260, 4, 2)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    light = 1.035 - 0.07 * (0.55 * xx / W + 0.45 * yy / H)
    img[..., :3] = np.where(solid[..., None], img[..., :3] * (n * light)[..., None], img[..., :3])
    return img


if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    img = build()
    save_rgba(img, "out/tv_frame.png")
    print("saved")
