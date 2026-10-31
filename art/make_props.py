"""Foreground props layer: things standing IN FRONT of the TV on the cabinet top (they must draw over
tv_frame.png). Each prop is its own component script; this places it with the cabinet's perspective.
Stack: background.png -> tv_frame.png -> props.png (-> doily.png).
Output: out/props.png (4K RGBA, transparent except the props and their shadows)."""
import math
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter
from common import *
from make_bg import CXC, H0, HORIZON, Z0, proj_scale, PLAN_PER_CM
import make_remote

REMOTE_AT = (667, 262)         # plan centre (X, d): screen x ~2573, between the TV's 频道 keys and POWER
REMOTE_ROT = 178               # plan direction of the IR end (deg; 0 = +X, 90 = toward the wall) -> at the TV;
                               # more turn than ~2 deg reads as the remote tipping over at this camera
REMOTE_LEN = 15.8 * PLAN_PER_CM  # body length in plan units: a 15.8 cm remote (fits the gap between 频道 and POWER)
REMOTE_BAG = True              # still in its protective sleeve (very much a thing)
# None = the scene's true camera (~10 deg above the top: a flat remote reads as a thin slab).
# An angle (deg) = a Duimon-style 'prop cheat': the prop alone is seen from that elevation so its face
# reads; it stays planted at the same spot/scale.
PROP_VIEW = 26                 # matched to a Gemini in-scene reference (face : length ~ 0.13, thin side wall)


class FlatCam:
    """Screen <-> plan mapping for something lying flat at height h above the cabinet top."""

    def __init__(self, Xc, dc, elev=None):
        self.Xc, self.dc, self.elev = Xc, dc, elev
        self.s = proj_scale(dc)
        self.xc, self.yc = CXC + Xc * self.s, HORIZON + H0 * self.s

    def to_screen(self, X, d, h):
        if self.elev is None:
            s = proj_scale(d)
            return CXC + X * s, HORIZON + (H0 - h) * s
        a = math.radians(self.elev)
        return (self.xc + (X - self.Xc) * self.s,
                self.yc - ((d - self.dc) * math.sin(a) + h * math.cos(a)) * self.s)

    def to_plan(self, xs, ys, h):
        if self.elev is None:
            d = Z0 * (H0 - h) / np.maximum(ys - HORIZON, 1) - Z0
            return (xs - CXC) / proj_scale(d), d
        a = math.radians(self.elev)
        X = self.Xc + (xs - self.xc) / self.s
        d = self.dc - ((ys - self.yc) / self.s + h * math.cos(a)) / math.sin(a)
        return X, d


def side_tone(r, v, u):
    """Side-wall luminance (0-255) at relative height r (0 table .. 1 face) of the two-part shell, after the
    side references: bottom edge tucks under into shadow, lower shell, the parting seam (dark groove with a
    lit lip below it), upper shell, then the rim rolling over into the face catches the light."""
    # profile measured off a Gemini in-scene reference (gemini-image-reference): 8 at the contact line, 17 tucked
    # under, 30 lower shell, a 2-px seam (dark groove + lit lip), 28 -> 36 upper shell, ~100 rolled rim
    lum = 9 + 9 * np.clip(r / .08, 0, 1)                                         # contact -> tuck-under
    lum = np.where(r > .26, 31 - 4 * np.clip((r - .26) / .28, 0, 1), lum)       # lower shell (lit from below by the varnish)
    lum = np.where((r > .54) & (r <= .585), 10, lum)                           # seam groove
    lum = np.where((r > .585) & (r <= .63), 42, lum)                           # its lit lip
    lum = np.where(r > .63, 27 + 10 * np.clip((r - .63) / .25, 0, 1), lum)     # upper shell
    lum = lum + 66 * np.exp(-((r - .95) / .045) ** 2)                          # face rolling over: rim highlight
    # battery end: moulded grip ribs on the lower shell, barely there
    ang = np.arctan2(u - make_remote.BW / 2, np.maximum(v - 880, 1e-3))
    notch = (v > 880) & (r > .3) & (r < .5) & (np.cos(ang * 30) > .7)
    lum = np.where(notch, lum * .8, lum)
    return lum


def place_remote(layer):
    BWr, BLr = make_remote.BW, make_remote.BL
    k = REMOTE_LEN / BLr                            # plan units per reference unit
    res = 2.5                                       # source px per plan unit
    top_img, kmask, (ox, oy) = make_remote.build_layers(k * res)
    top_img = np.stack([gaussian_filter(top_img[..., i], .8) for i in range(4)], -1)
    kmask = gaussian_filter(kmask, .8)
    pm = top_img.copy(); pm[..., :3] *= pm[..., 3:4]                 # premultiplied for clean filtering
    keys = pm.copy(); keys *= kmask[..., None] / np.maximum(top_img[..., 3:4], 1e-6)
    # key side colour = the key's own average colour, darkened (blurred so the rim stroke doesn't show)
    kcol = np.stack([gaussian_filter(top_img[..., i] * kmask, 4) for i in range(3)], -1)
    kcol /= np.maximum(gaussian_filter(kmask, 4), 1e-4)[..., None]
    kside = np.concatenate([kcol, kmask[..., None]], -1)
    bag_img = make_remote.bag(k * res) if REMOTE_BAG else None
    if bag_img is not None:
        bag_img[..., :3] *= bag_img[..., 3:4]
    T, KH = make_remote.THICK * k, make_remote.KEY_H * k
    def thick(v):                                   # wedge: thinner toward the IR end (v = 0)
        return T * (make_remote.THICK_IR + (1 - make_remote.THICK_IR) * np.clip(v / BLr, 0, 1))
    cxp, cdp = REMOTE_AT
    cam = FlatCam(cxp, cdp, PROP_VIEW)
    th = math.radians(REMOTE_ROT)
    e_len = np.array([math.cos(th), math.sin(th)]); e_w = np.array([math.sin(th), -math.cos(th)])

    hw, hl = (BWr / 2 + 60) * k, (BLr / 2 + 60) * k
    pts = [np.array([cxp, cdp]) + a * hw * e_w + b * hl * e_len for a in (-1, 1) for b in (-1, 1)]
    sx, sy = zip(*[cam.to_screen(p[0], p[1], h) for p in pts for h in (0, T + KH + 4)])
    x0, x1 = int(min(sx)) - 30, int(max(sx)) + 31
    y0, y1 = int(min(sy)) - 12, int(max(sy)) + 13
    bh, bw = y1 - y0, x1 - x0

    def coords(h, ssx, ssy):
        """Asset px/py + remote-local (u, v) for every supersample of the block, on the plane at height h
        (scalar, or a function of v for the wedge-shaped face: solved by fixed-point iteration)."""
        gy, gx = np.mgrid[0:bh * ssy, 0:bw * ssx].astype(np.float32)
        xs, ys = x0 + (gx + .5) / ssx, y0 + (gy + .5) / ssy
        hh = h if not callable(h) else h(BLr / 2)
        for _ in range(1 if not callable(h) else 3):
            X, d = cam.to_plan(xs, ys, hh)
            rx, rd = X - cxp, d - cdp
            u = BWr / 2 + (rx * e_w[0] + rd * e_w[1]) / k
            v = BLr / 2 - (rx * e_len[0] + rd * e_len[1]) / k
            if callable(h):
                hh = h(v)
        return ox + u * k * res - .5, oy + v * k * res - .5, u, v

    def down(a, ssx, ssy):
        return a.reshape(bh, ssy, bw, ssx).mean((1, 3))

    def look(img, cc, ssx, ssy, chans):
        px, py = cc[0], cc[1]
        out = [down(map_coordinates(img[..., i] if img.ndim == 3 else img, [py, px], order=1, cval=0), ssx, ssy) for i in chans]
        return np.stack(out, -1)

    blk = np.zeros((bh, bw, 4), np.float32)                       # premultiplied block
    def put(rgb, a):
        blk[..., :3] = blk[..., :3] * (1 - a[..., None]) + rgb * a[..., None]
        blk[..., 3] = blk[..., 3] * (1 - a) + a
    def put_pm(pmc):
        blk[..., :3] = blk[..., :3] * (1 - pmc[..., 3:4]) + pmc[..., :3]
        blk[..., 3] = blk[..., 3] * (1 - pmc[..., 3]) + pmc[..., 3]

    # shadow + contact darkening on the varnish (key light upper-left -> falls right/back)
    foot = look(top_img, coords(0, 1, 2), 1, 2, [3])[..., 0]
    sh = gaussian_filter(np.roll(foot, (-3, 12), (0, 1)), (3, 8)) * .55 + gaussian_filter(foot, 1.5) * .35
    put(np.zeros(3, np.float32), np.clip(sh, 0, .8))

    # body side wall: stack the silhouette from the table up to the (wedge) face
    n = max(10, int(T * 1.8))
    for i in range(n + 1):
        h = T * i / n
        cc = coords(h, 1, 2)
        tv = thick(cc[3])
        a = down(map_coordinates(top_img[..., 3], [cc[1], cc[0]], order=1, cval=0) * (h <= tv), 1, 2)
        u, v = down(cc[2], 1, 2), down(cc[3], 1, 2)
        r = np.clip(h / thick(v), 0, 1)
        lum = side_tone(r, v, u)
        rgb = np.stack([lum, lum, lum * 1.08], -1) / 255
        # IR end: smoked window in the end cap (dark red-black, glossy streak across its middle)
        ir = np.clip((26 - v) / 10, 0, 1) * ((r > .22) & (r < .86)) * (np.abs(u - BWr / 2) < BWr / 2 - 30)  # end cap only
        win = np.stack([16 + 30 * np.exp(-((r - .62) / .05) ** 2)] * 3, -1) * np.array([1.5, .55, .5]) / 255
        rgb = rgb * (1 - ir[..., None]) + win * ir[..., None]
        put(rgb.astype(np.float32), a)

    # face (keys flattened into it are hidden by the raised keys below)
    put_pm(look(pm, coords(thick, 2, 6), 2, 6, range(4)))
    # raised rubber keys: side walls, then the key tops
    nk = max(4, int(KH * 2))
    for i in range(1, nk + 1):
        t = KH * i / nk
        cc = coords(lambda v: thick(v) + t, 1, 2)
        ks = look(kside, cc, 1, 2, range(4))
        put(ks[..., :3] * (.28 + .22 * i / nk), ks[..., 3])                  # rubber skirt: in its own shadow
    put_pm(look(keys, coords(lambda v: thick(v) + KH, 2, 6), 2, 6, range(4)))

    # sleeve: over the remote where it lies, settling onto the varnish around it
    if bag_img is not None:
        hi = look(bag_img, coords(lambda v: thick(v) + KH + 1.5, 2, 6), 2, 6, range(4))
        lo = look(bag_img, coords(1.0, 2, 6), 2, 6, range(4))
        cov = gaussian_filter(look(top_img, coords(thick, 1, 2), 1, 2, [3])[..., 0], 2)[..., None]
        put_pm(hi * cov + lo * (1 - cov))
    straight = blk.copy(); straight[..., :3] /= np.maximum(blk[..., 3:4], 1e-6)
    layer[y0:y1, x0:x1] = over(straight, layer[y0:y1, x0:x1])
    return layer


def build():
    layer = np.zeros((H, W, 4), np.float32)
    return place_remote(layer)


if __name__ == "__main__":
    import os, sys
    os.makedirs("out", exist_ok=True)
    if len(sys.argv) > 1:
        PROP_VIEW = float(sys.argv[1])
    save_rgba(build(), "out/props.png")
    print("saved", "view =", PROP_VIEW)
