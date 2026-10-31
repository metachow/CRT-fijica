"""Optional top layer: the crocheted lace cover (钩针电视罩) that every family put on the TV.
Output: out/doily.png (4K RGBA, transparent except lace + its shadow on the TV)."""
import math
import numpy as np
import skia
from PIL import Image, ImageFilter
from common import *

X0, X1 = 408, 3432       # cloth spans slightly wider than the TV face (430..3410)
BAND_T, BAND_B = 34, 68
SC_DEPTH = 30


def cloth_path():
    p = skia.Path()
    p.moveTo(580, -10); p.lineTo(3260, -10); p.lineTo(3402, 40); p.lineTo(438, 40); p.close()
    p.addRect(rect(X0, BAND_T, X1, BAND_B))
    n = round((X1 - X0) / 112); sw = (X1 - X0) / n
    sc = skia.Path()
    for i in range(n):
        a = X0 + i * sw
        sc.moveTo(a, BAND_B - 1)
        sc.cubicTo(a + sw * 0.04, BAND_B + SC_DEPTH * 1.25, a + sw * 0.96, BAND_B + SC_DEPTH * 1.25, a + sw, BAND_B - 1)
        sc.close()
    p = skia.Op(p, sc, skia.PathOp.kUnion_PathOp)
    for m in (1, -1):  # tails drooping over both front corners
        cx = 1920
        pts = [(X0, BAND_T), (478, BAND_T), (478, 70), (452, 196), (428, 262), (410, 214), (X0, 120)]
        t = skia.Path(); t.moveTo(cx + m * (pts[0][0] - cx), pts[0][1])
        for x, y in pts[1:]:
            t.lineTo(cx + m * (x - cx), y)
        t.close()
        p = skia.Op(p, t, skia.PathOp.kUnion_PathOp)
    return p, n, sw


def build():
    s = surface(); c = s.getCanvas(); c.clear(C(0, 0, 0, 0))
    path, n, sw = cloth_path()
    c.drawPath(path, paint(shader=lin(0, -10, 0, 260, [C(238, 234, 222), C(248, 245, 236), C(236, 231, 218)], [0, .3, 1])))
    # picot dots around each scallop rim (part of the thread, drawn solid)
    solid = paint(C(246, 243, 233))
    for i in range(n):
        xc = X0 + (i + 0.5) * sw
        for k in range(7):
            ang = math.radians(18 + k * 24)
            c.drawCircle(xc - 0.49 * sw * math.cos(ang),
                         BAND_B - 2 + SC_DEPTH * 1.02 * math.sin(ang), 3.6, solid)

    clear = paint(C(0, 0, 0), blend=skia.BlendMode.kClear)
    # top surface mesh (seen at a grazing angle -> squashed ellipses)
    for j, y in enumerate(range(4, 38, 9)):
        off = 10 if j % 2 else 0
        for x in range(470 + off, 3380, 20):
            c.drawOval(rect(x - 6, y - 2.6, x + 6, y + 2.6), clear)
    # band: two staggered rows of small holes + a chain of diamonds
    for j, y in enumerate((44, 58)):
        off = 7 if j else 0
        for x in range(X0 + 10 + off, X1 - 6, 14):
            c.drawCircle(x, y, 3.4, clear)
    # scallop fans
    for i in range(n):
        xc = X0 + (i + 0.5) * sw
        c.drawCircle(xc, BAND_B + 2, 4.2, clear)
        for rr, cnt, hr in ((13, 5, 3.4), (23, 7, 3.0)):
            for k in range(cnt):
                ang = math.radians(20 + k * (140 / (cnt - 1)))
                c.drawCircle(xc - rr * math.cos(ang) * 1.9, BAND_B + rr * math.sin(ang) * 0.9, hr, clear)
    # tails: open mesh
    for m in (1, -1):
        for y in range(76, 250, 12):
            for x in range(414, 476, 12):
                xx = 1920 + m * (x + (6 if (y // 12) % 2 else 0) - 1920)
                c.drawCircle(xx, y, 3.2, clear)
    lace = to_np(s)

    # thread relief from the alpha mask (light from upper-left)
    a = lace[..., 3]
    b = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
    gx = np.zeros_like(b); gy = np.zeros_like(b)
    gx[:, 1:-1] = b[:, 2:] - b[:, :-2]; gy[1:-1] = b[2:] - b[:-2]
    shade = (1 + 0.9 * (0.7 * gx + 0.7 * gy)) * (0.86 + 0.14 * b)
    shade *= 1 + 0.03 * grain(H, W, 7)
    lace[..., :3] *= shade[..., None]
    # tails hang in shadow a little (they bend away from the light)
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    lace[..., :3] *= np.clip(1 - 0.12 * np.clip((yy - 80) / 180, 0, 1), 0, 1)[..., None]

    # cast shadow of the lace on the TV
    sh = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
    sh = np.asarray(sh, np.float32) / 255
    sh = np.roll(np.roll(sh, 7, axis=0), 3, axis=1) * 0.45
    shadow = np.zeros((H, W, 4), np.float32); shadow[..., 3] = sh
    return over(lace, shadow)


if __name__ == "__main__":
    save_rgba(build(), "out/doily.png")
    print("saved")
