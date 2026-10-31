"""Wall prop: a 2000s Chinese 86-type five-hole socket (五孔插座: a universal 2-pin pair over a GB 3-pin
set) with the TV's straight-head 2-pin flat plug (直头两极扁插) pushed into the top pair.
Drawn front-on in REFERENCE units = px of the 4x reference crop with the plate's top-left at (0, 0)
(plate 880 units = 86 mm). build() scales it. Aged: ivory yellowing, grime where hands go.
Output (standalone run): out/socket.png + out/socket_preview.png."""
import math
import numpy as np
import skia
from common import *

PLATE = 880                    # 86 mm
PLATE_R = 64
PANEL = (160, 110, 720, 790)   # the inset module (portrait)
PAIR = ((338, 243), (528, 243))  # 2-pin universal holes (round part centres)
EARTH = (431, 508)
LOWER = ((356, 658), (506, 658))
BRAND = "HUASHENG"
IVORY = (238, 235, 224)


def shade(rgb, k, a=255):
    return C(*[int(np.clip(v * k, 0, 255)) for v in rgb], a)


def hole(c, path):
    """Dark opening with a soft inner depth and a lit lower lip."""
    lip = skia.Path(path); lip.offset(0, 4)
    c.drawPath(lip, paint(C(255, 252, 240, 170)))
    c.drawPath(path, paint(C(30, 27, 23)))
    c.save(); c.clipPath(path, doAntiAlias=True)
    c.drawPath(path, paint(C(70, 64, 56), stroke=6, blur=3))
    c.restore()


def pair_hole(c, cx, cy, side):
    """Universal 2-pin hole: round part toward the outside, flat-pin slot on the inner side."""
    p = skia.Path(); p.addCircle(cx, cy, 33)
    sx = cx + side * 31
    q = skia.Path(); q.addRRect(rrect(sx - 9, cy - 42, sx + 9, cy + 42, 4))
    hole(c, skia.Op(p, q, skia.PathOp.kUnion_PathOp))


def slot(c, cx, cy, length, width, deg):
    p = skia.Path(); p.addRRect(rrect(cx - width / 2, cy - length / 2, cx + width / 2, cy + length / 2, width / 2))
    p.transform(skia.Matrix.RotateDeg(deg, skia.Point(cx, cy)))
    hole(c, p)


def plate(c):
    c.drawRRect(rrect(14, 26, PLATE + 14, PLATE + 26, PLATE_R), paint(C(40, 30, 14, 90), blur=22))   # on the wall
    c.drawRRect(rrect(0, 0, PLATE, PLATE, PLATE_R), paint(shader=lin(0, 0, PLATE, PLATE, [shade(IVORY, 1.06), shade(IVORY, .99), shade(IVORY, .9)])))
    # pillowed rim: flat face in the middle, the outer band rolls off (lit top-left, shaded bottom-right)
    c.save(); c.clipRRect(rrect(0, 0, PLATE, PLATE, PLATE_R), doAntiAlias=True)
    c.drawRRect(rrect(46, 46, PLATE - 46, PLATE - 46, 30), paint(shade(IVORY, 1.0), blur=26))
    c.drawRRect(rrect(3, 3, PLATE - 3, PLATE - 3, PLATE_R - 3), paint(shader=lin(0, 0, PLATE, PLATE, [C(255, 255, 250, 200), C(255, 255, 250, 0), C(0, 0, 0, 0), C(70, 56, 30, 90)], [0, .35, .65, 1]), stroke=8, blur=4))
    c.restore()
    c.drawRRect(rrect(0, 0, PLATE, PLATE, PLATE_R), paint(C(120, 110, 88, 160), stroke=2))
    # inset module with a crisp groove
    l, t, r, b = PANEL
    c.drawRect(rect(l, t, r, b), paint(shader=lin(l, t, r, b, [shade(IVORY, 1.03), shade(IVORY, .98)])))
    c.drawRect(rect(l, t, r, b), paint(C(132, 122, 98, 200), stroke=3))
    c.drawLine(l + 3, t + 3, r - 3, t + 3, paint(C(255, 255, 248, 150), stroke=1.6))
    c.drawLine(l + 3, t + 3, l + 3, b - 3, paint(C(255, 255, 248, 150), stroke=1.6))
    f = skia.Font(skia.Typeface.MakeFromName("Arial", skia.FontStyle.Bold()), 30)
    c.drawString(BRAND, PLATE - 58 - f.measureText(BRAND), PLATE - 50 + 1.5, f, paint(C(255, 255, 248, 160)))
    c.drawString(BRAND, PLATE - 58 - f.measureText(BRAND), PLATE - 50, f, paint(C(150, 142, 122, 200)))


def openings(c):
    pair_hole(c, *PAIR[0], 1); pair_hole(c, *PAIR[1], -1)
    ex, ey = EARTH                                                  # earth slot on a little round boss
    c.drawCircle(ex + 2, ey + 4, 52, paint(C(90, 76, 50, 60), blur=5))
    c.drawCircle(ex, ey, 52, paint(shader=rad(ex - 18, ey - 20, 80, [shade(IVORY, 1.08), shade(IVORY, .96)])))
    slot(c, ex, ey, 76, 17, 0)
    slot(c, *LOWER[0], 86, 20, -30)
    slot(c, *LOWER[1], 86, 20, 30)


def plug_profile(z):
    """Cross-section scale along the plug axis (z: 0 at the pin face/wall .. 1 at the rear), after the
    reference: wide flange, taper, a waist of grip ridges, rounded shoulder, small rear cap."""
    z = np.asarray(z, np.float32)
    p = np.interp(z, [0, .06, .10, .34, .40, .76, .86, .94, 1.0], [1.0, 1.0, .96, .80, .74, .74, .66, .56, .44])
    ridges = (z > .40) & (z < .76)
    p = p + np.where(ridges, .045 * np.clip(np.sin((z - .40) / .36 * 5 * np.pi), 0, 1) ** .6, 0)
    return p


def plug(c, dx, dy):
    """Straight-head 2-pin flat plug in the top pair, seen down its own axis: the flange against the plate is
    the biggest outline, the body tapers toward the viewer, so the taper and the grip ridges read as
    concentric rings; the cord leaves the rear cap dead centre through a short strain relief. (dx, dy) =
    perspective slide of the rear end relative to the flange for the ~35 mm the body stands out."""
    mx = (PAIR[0][0] + PAIR[1][0]) / 2; my = PAIR[0][1] + 4
    HW, HH = 170, 116                                   # flange half-size (~33 x 23 mm)
    sp = skia.Path(); sp.addRRect(rrect(mx - HW, my - HH, mx + HW, my + HH, 52)); sp.offset(30, 38)
    c.drawPath(sp, paint(C(40, 30, 14, 130), blur=24))  # shadow on the plate (key light upper-left)
    n = 90
    zs = np.linspace(0, 1, n + 1)
    pr = plug_profile(zs)
    slope = -np.gradient(pr, zs) * HW / 358             # dr/dlength (>0: surface turned toward the viewer)
    L = np.array([-.45, -.6, .66]); L /= np.linalg.norm(L)   # key light: upper-left, in front
    def tone(ox, oy, sl):
        nv = np.array([ox, oy, sl]); nv /= np.linalg.norm(nv)
        dif = max(0.0, float(nv @ L))
        spec = max(0.0, float(nv @ (L + np.array([0, 0, 1])) / np.linalg.norm(L + np.array([0, 0, 1])))) ** 30
        return 13 + 62 * dif ** 1.3 + 90 * spec
    for z, sc, sl in zip(zs, pr, slope):                 # far (wall) -> near (rear end): painter's order
        cx, cy = mx + dx * z, my + dy * z
        hw, hh = HW * sc, HH * sc
        ul, br = tone(-.707, -.707, sl), tone(.707, .707, sl)
        c.drawRRect(rrect(cx - hw, cy - hh, cx + hw, cy + hh, 50 * sc),
                    paint(shader=lin(cx - hw, cy - hh, cx + hw, cy + hh, [grey(ul), grey((ul + br) / 2), grey(br)])))
    # rear cap: a shallow dome around the cord
    cx, cy = mx + dx, my + dy
    hw, hh = HW * pr[-1], HH * pr[-1]
    c.drawRRect(rrect(cx - hw, cy - hh, cx + hw, cy + hh, 50 * pr[-1]),
                paint(shader=rad(cx - hw * .35, cy - hh * .45, hw * 1.3, [grey(58), grey(34), grey(20)], [0, .45, 1])))
    # strain relief boot: short ribbed sleeve, coming toward the viewer and already bending down
    ex, ey = cx, cy
    for i in range(16):
        t = i / 15
        bx, by = ex + dx * .45 * t, ey + dy * .45 * t + 30 * t * t
        r = 40 - 16 * t
        v = 36 if i % 3 else 52
        c.drawCircle(bx, by, r, paint(shader=rad(bx - r * .45, by - r * .55, r * 1.5, [grey(v), grey(22), grey(11)], [0, .5, 1])))
    return ex + dx * .45, ey + dy * .45 + 30


def grey(v, a=255):
    v = int(np.clip(v, 0, 255))
    return C(v, v, v, a)


def build(scale=1.0, protrude=(-50, 53), pad=60, seed=3):
    """Returns (straight-alpha RGBA, origin = plate top-left in image px, cord exit point in image px)."""
    w = h = int(np.ceil((PLATE + 2 * pad) * scale))
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c = s.getCanvas(); c.clear(C(0, 0, 0, 0)); c.scale(scale, scale); c.translate(pad, pad)
    plate(c); openings(c)
    img0 = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).astype(np.float32) / 255
    # ageing on the plastic only (before the plug goes in): yellowing, grime around the holes and rim
    yy, xx = (np.mgrid[0:h, 0:w].astype(np.float32) / scale - pad)
    def blob(cx, cy, rx, ry):
        return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    dirt = (.55 * blob(433, 250, 260, 190) + .25 * blob(431, 600, 200, 200)) * (.6 + .4 * fbm(h, w, 40 * scale + 2, 3, seed))
    edge = np.clip(1 - np.minimum.reduce([xx, yy, PLATE - xx, PLATE - yy]) / 40, 0, 1) * (.5 + .5 * fbm(h, w, 20 * scale + 2, 3, seed + 1))
    rgb = img0[..., :3] * np.array([1.0, .985, .95])
    rgb *= 1 - (.16 * dirt + .14 * edge)[..., None] * np.array([.8, .9, 1.05])
    rgb *= (1 + .012 * grain(h, w, seed + 2))[..., None]
    img0[..., :3] = np.clip(rgb, 0, 1)
    # plug on top
    s2 = skia.Surface.MakeRaster(skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c2 = s2.getCanvas(); c2.clear(C(0, 0, 0, 0)); c2.scale(scale, scale); c2.translate(pad, pad)
    cord = plug(c2, *protrude)
    pl = s2.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).astype(np.float32) / 255
    out = over(pl, img0)
    return out, (pad * scale, pad * scale), ((cord[0] + pad) * scale, (cord[1] + pad) * scale)


if __name__ == "__main__":
    import os
    from PIL import Image
    os.makedirs("out", exist_ok=True)
    img, _, cord = build(.5)
    save_rgba(img, "out/socket.png")
    bg = Image.new("RGBA", (img.shape[1], img.shape[0]), (122, 152, 128, 255))
    bg.alpha_composite(Image.open("out/socket.png"))
    bg.convert("RGB").save("out/socket_preview.png")
    print("saved", img.shape, "cord exit", cord)
