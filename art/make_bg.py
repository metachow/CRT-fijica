"""Room background layer (v2): grimy whitewash wall over a green painted wainscot (墙裙), old 奖状 and a
credit-union wall calendar mostly out of frame, a worn 86-type socket with the TV plug, and a brown varnished
TV cabinet with a bull-nosed, round-cornered top, arched door panels and a VCD player in the open shelf.
Output: out/background.png (4K, opaque)."""
import math
import numpy as np
import skia
from PIL import Image, ImageFilter
from common import *
from paper import certificate, calendar, to_skimage
import make_vcd
import make_socket

WAIN = 820
CAB_TOP = 1878                 # back edge of the cabinet top, against the wall (TV stands here)
TOP_FRONT = 1968               # front edge of the top, middle section
NOSE = 50                      # height of the half-round front edge
CAB_L, CAB_R = 96, 3744        # extent of the FRONT edge
RX, RY = 340, 58               # rounded front corners: plan radius, and how tall the arc reads on screen
BODY_IN = 40                   # body is set back under the nose

# Perspective of the top. The eye sits above the frame (the TV's own top is seen from above), so the
# top recedes toward a vanishing point at the centre: its back edge against the wall is NARROWER than
# the front and the sides slant inward — no vertical cut where the cabinet meets the wall.
# Plan coords are in front-edge pixels: X across (0 = centre), d = depth back from the front edge.
HORIZON = -150
H0 = TOP_FRONT - HORIZON
Z0 = H0 * RX / RY - RX                              # eye distance that gives the RX:RY corner foreshortening
DEPTH = Z0 * (H0 / (CAB_TOP - HORIZON) - 1)          # front edge -> wall
HALF = (CAB_R - CAB_L) / 2
CXC = (CAB_L + CAB_R) / 2


def proj_scale(d):
    return Z0 / (Z0 + d)


BACK_L, BACK_R = CXC - HALF * proj_scale(DEPTH), CXC + HALF * proj_scale(DEPTH)


def px_per_cm(d):
    """Screen px per real cm for something standing at depth d (plan units back from the front edge).
    PX_PER_CM is measured on the TV face, which stands at the wall (d = DEPTH)."""
    return PX_PER_CM * proj_scale(d) / proj_scale(DEPTH)


PLAN_PER_CM = px_per_cm(0)     # plan units (= front-edge px) per cm, for sizes laid out in plan coords


def plan_coords(xx, yy):
    """Screen px lying on the top's plane -> plan (X, d)."""
    d = Z0 * H0 / np.maximum(yy - HORIZON, 1.0) - Z0
    return (xx - CXC) / proj_scale(d), d


def top_sdf(X, d):
    """Plan-space signed distance to the top outline: rounded front corners, square back into the wall."""
    qx = np.abs(X) - HALF + RX
    qy = np.abs(d - DEPTH) - DEPTH + RX
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - RX


def sdf_coverage(sdf):
    """Anti-aliased coverage from a field given in any units (normalised by its screen-space gradient)."""
    gy, gx = np.gradient(sdf)
    return np.clip(.5 - sdf / np.maximum(np.hypot(gx, gy), 1e-4), 0, 1)


# ------------------------------------------------------------------ wall
def wall_layer():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cream = np.array([214, 208, 192], np.float32) / 255
    mott = fbm(H, W, 480, 5, 11)
    plaster = fbm(H, W, 5, 2, 12)
    vert = np.asarray(Image.fromarray(fbm(H // 10, W, 6, 4, 14)).resize((W, H), Image.BICUBIC))
    wall = cream * (1 + .05 * mott + .02 * plaster + .025 * vert)[..., None]
    # damp / smoke stains: a big one top-left, a fainter one right
    for (cx, cy, rx, ry, k, sd) in [(160, -60, 560, 340, .12, 13), (3500, 120, 500, 420, .07, 15)]:
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        st = np.clip(1 - d, 0, 1) ** 1.3 * (.55 + .45 * fbm(H, W, 80, 3, sd))
        wall = wall * (1 - k * st[..., None]) + np.array([.05, .035, 0]) * st[..., None] * .6
    green = np.array([122, 152, 128], np.float32) / 255
    wain = green * (1 + .03 * fbm(H, W, 600, 4, 21) + .008 * plaster)[..., None]
    wain *= (1 + .05 * np.exp(-((yy - (WAIN + 160)) / 260) ** 2))[..., None]
    sc = np.clip(fbm(H, W, 36, 3, 22) - .3, 0, 1) * np.clip((yy - 1300) / 500, 0, 1)
    wain *= (1 - .22 * sc[..., None])
    chips = (fbm(H, W, 14, 2, 23) > .55) & (yy > 1500)
    wain = np.where(chips[..., None], wain * .85 + np.array([.72, .70, .64]) * .15, wain)
    img = np.where((yy < WAIN)[..., None], wall, wain)
    band = (yy >= WAIN - 2) & (yy < WAIN + 12)
    img[band] *= np.array([.62, .70, .66])
    img[(yy >= WAIN + 12) & (yy < WAIN + 15)] *= 1.04
    # dust darkening toward the cabinet, room light from upper-left, vignette
    img *= (1 - .10 * np.clip((yy - 1400) / 480, 0, 1))[..., None]
    light = 1.04 - .12 * (.6 * xx / W + .4 * yy / H)
    vig = 1 - .26 * (((xx - W / 2) / (W * .6)) ** 2 + ((yy - H * .45) / (H * .75)) ** 2)
    img *= (light * np.clip(vig, .66, 1))[..., None]
    return img


# ------------------------------------------------------------------ wall props
def place(c, arr, x, y, deg, shadow=True):
    h, w = arr.shape[:2]
    c.save(); c.rotate(deg, x + w / 2, y + h / 2)
    if shadow:
        c.drawRect(rect(x + 6, y + 9, x + w + 6, y + h + 9), paint(C(0, 0, 0, 70), blur=9))
    c.drawImage(to_skimage(arr), x, y, skia.SamplingOptions(skia.FilterMode.kLinear), paint())
    c.restore()


def tape(c, x, y, ang, w=54, h=18):
    c.save(); c.rotate(ang, x, y)
    c.drawRect(rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), paint(C(214, 196, 140, 120)))
    c.drawRect(rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), paint(C(120, 100, 60, 70), stroke=1.5))
    c.restore()


def wall_props(c):
    place(c, certificate(440, 320, 3, term="2001—2002学年度第二学期", year="2002年7月"), -80, -150, -1.6)
    place(c, certificate(440, 320, 8, honor="学习积极分子"), 150, 236, 1.1)
    tape(c, 360, 168, 32); tape(c, 156, 240, -35)
    place(c, calendar(), 3456, -290, 1.0)
    tape(c, 3470, 546, -30); tape(c, 3830, 550, 28, w=40)


SOCKET_AT = (96, 1420)         # plate top-left on the wall
PLUG_OUT = 3.5                 # cm the plug body stands off the plate


def socket(c):
    """86-type five-hole socket (separate component, make_socket.py) with the TV's 2-pin plug, its cord
    dropping behind the cabinet. 86 mm plate, at the wall plane."""
    s_wall = proj_scale(DEPTH)
    size = 8.6 * px_per_cm(DEPTH)
    k = size / make_socket.PLATE
    l, t = SOCKET_AT
    # how far the plug's rear face slides on screen toward/away from the vanishing point (perspective)
    grow = proj_scale(DEPTH - PLUG_OUT * PLAN_PER_CM) / s_wall - 1
    mx, my = l + 433 * k, t + 243 * k
    protrude = ((mx - CXC) * grow / k, (my - HORIZON) * grow / k)
    img, (ox, oy), (ex, ey) = make_socket.build(k, protrude)
    x0, y0 = l - ox, t - oy
    ex, ey = ex + x0, ey + y0
    c.drawCircle(l + size * .5 + 6, t + size * .45, size * .75, paint(C(40, 30, 10, 40), blur=50))   # hand grime on the wall
    c.drawImage(to_skimage(img), x0, y0, skia.SamplingOptions(skia.FilterMode.kLinear), paint())
    # cord: out of the strain relief toward the viewer, sagging down and back behind the cabinet top
    cable = skia.Path(); cable.moveTo(ex, ey)
    cable.cubicTo(ex - 30, ey + 60, ex - 30, ey + 200, ex + 50, CAB_TOP + 30)     # sags a little left, clear of the 3-pin slots
    sh = skia.Path(cable); sh.offset(16, 20)
    c.drawPath(sh, paint(C(20, 14, 6, 70), stroke=16, blur=7))
    c.drawPath(cable, paint(C(22, 22, 23), stroke=14))
    c.drawPath(cable, paint(C(255, 255, 255, 40), stroke=2.5))
    hi = skia.Path(cable); hi.offset(-3.5, 0)
    c.drawPath(hi, paint(C(255, 255, 255, 30), stroke=1.5))


# ------------------------------------------------------------------ cabinet
def cabinet_layer(img):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    X, d = plan_coords(xx + .5, yy + .5)

    # ---- top: true perspective outline, back edge clipped by the wall
    a_top = sdf_coverage(top_sdf(X, d)) * np.clip(yy + .5 - CAB_TOP, 0, 1)
    solid = a_top > .5
    has = solid.any(0)
    rows = np.arange(H)[:, None]
    ye = np.where(solid, rows, -1).max(0)                       # last solid row per column = front outline
    yn = np.clip(ye + 1, 0, H - 1); cols = np.arange(W)
    a1, a2 = a_top[np.clip(ye, 0, H - 1), cols], a_top[yn, cols]
    ye_f = ye + .5 + (a1 - .5) / np.maximum(a1 - a2, 1e-3)      # sub-pixel edge position
    ye_f = np.where(has, ye_f, -1e4)
    # plan position of that edge point -> how much its half-round nose turns away (front 0 .. side 1)
    Xe, de = plan_coords(cols + .5, np.maximum(ye_f, CAB_TOP))
    qx, qy = np.maximum(np.abs(Xe) - HALF + RX, 0), np.maximum(RX - de, 0)
    u = qx / np.maximum(np.hypot(qx, qy), 1e-6)
    nose_h = NOSE * proj_scale(de)

    wood = np.array([96, 56, 34], np.float32) / 255
    # top grain lives in PLAN space so it recedes with the surface
    pw, pd = int(2 * HALF) + 2, int(DEPTH) + 2
    p_streak = np.asarray(Image.fromarray(fbm(pd, pw // 14, 3, 4, 31)).resize((pw, pd), Image.BICUBIC))
    p_low = fbm(pd, pw, 700, 3, 32); p_fine = fbm(pd, pw, 120, 3, 33); p_dust = fbm(pd, pw, 30, 3, 37)
    xi = np.clip((X + HALF).astype(np.int32), 0, pw - 1); di = np.clip(d.astype(np.int32), 0, pd - 1)
    rings = np.sin(2 * math.pi * (d / 180 + 3.2 * p_low[di, xi])) * .5 + .5
    wh = wood * (1 + .14 * p_streak[di, xi] + .08 * (rings - .5) + .03 * p_fine[di, xi])[..., None]
    hstreak = np.asarray(Image.fromarray(fbm(H, W // 14, 3, 4, 31)).resize((W, H), Image.BICUBIC))
    low = fbm(H, W, 700, 3, 32)
    rings_s = np.sin(2 * math.pi * (yy / 30 + 3.2 * low)) * .5 + .5
    wh_s = wood * (1 + .14 * hstreak + .08 * (rings_s - .5) + .03 * fbm(H, W, 120, 3, 33))[..., None]
    vstreak = np.asarray(Image.fromarray(fbm(H // 14, W, 3, 4, 34)).resize((W, H), Image.BICUBIC))
    vr = np.sin(2 * math.pi * (xx / 34 + 3 * fbm(H, W, 500, 3, 36))) * .5 + .5
    wv = wood * (1 + .13 * vstreak + .07 * (vr - .5) + .03 * fbm(H, W, 90, 3, 35))[..., None]

    # top: grazing view of varnish -> brighter toward the front, soft reflection band, dust
    t = np.clip(1 - d / DEPTH, 0, 1)
    refl = .78 + .30 * t + .22 * np.exp(-((t - .6) / .18) ** 2) * (.8 + .2 * np.cos(xx / W * 3))
    top = wh * refl[..., None] * (1 + .03 * p_dust[di, xi])[..., None]
    # wall-side strip of the top sits in the wall's shade
    top *= (1 - .22 * np.exp(-np.clip(DEPTH - d, 0, None) / 60))[..., None]

    # half-round nose hanging from the front outline: cylinder shading, light from up-front
    off = yy + .5 - ye_f[None, :]
    v = np.clip(off / nose_h[None, :], 0, 1)
    a_nose = np.clip(nose_h[None, :] - off + .5, 0, 1) * (off > -1.5)
    phi = v * math.pi                                # 0 = facing up, pi/2 = facing viewer, pi = down
    diff = np.clip(np.cos(phi - math.radians(50)), 0, 1) ** 1.3
    spec = np.exp(-((phi - math.radians(42)) / .16) ** 2)
    nose_i = .26 + .95 * diff
    worn = np.clip(fbm(H, W, 18, 3, 38) - .25, 0, 1) * spec          # varnish rubbed off on the edge
    nose = wh_s * nose_i[..., None] + (.30 * spec)[..., None] + np.array([.18, .12, .06]) * worn[..., None]
    nose *= (1 - .45 * u[None, :] ** 2)[..., None]

    # body: set back under the nose (front face at depth BODY_IN), ends rounding away
    bl, br = body_x()
    nb = ye_f[None, :] + nose_h[None, :]
    a_body = np.clip(yy + .5 - (nb - 4), 0, 1) * np.clip(xx + .5 - bl, 0, 1) * np.clip(br - (xx + .5), 0, 1)
    body_sh = .50 + .22 * np.clip((yy - nb) / 70, 0, 1)
    end = np.clip(np.minimum(xx - bl, br - xx) / 220, 0, 1) ** .6
    body = wv * (body_sh * (.62 + .38 * end))[..., None]

    out = img.copy()
    # contact shadow on the wall along the back edge (ambient occlusion), fading at the corners
    above = np.clip(CAB_TOP - (yy + .5), 0, None)
    span = np.clip(np.minimum(xx - BACK_L, BACK_R - xx) / 40 + .5, 0, 1)
    ao = (.30 * np.exp(-above / 10) + .14 * np.exp(-above / 46)) * span * (yy < CAB_TOP)
    out *= (1 - ao[..., None])
    sil = np.zeros((H, W), np.float32)
    for a, col in ((a_body, body), (a_nose, nose), (a_top, top)):
        out = out * (1 - a[..., None]) + col * a[..., None]
        sil = np.maximum(sil, a)
    # the cabinet's shadow on the wall (key light upper-left -> falls right)
    sh = np.asarray(Image.fromarray((sil * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28)), np.float32) / 255
    sh = np.roll(sh, 36, axis=1) * (1 - sil) * np.clip((yy - CAB_TOP) / 50 + .3, 0, 1) * .30
    out *= (1 - sh[..., None])
    return out


def body_x():
    """Body ends are rounded like the top (offset BODY_IN), so its silhouette is where the end's side
    tangent sits, at depth RX — always tucked inside the top's outline."""
    s = proj_scale(RX)
    return CXC - (HALF - BODY_IN) * s, CXC + (HALF - BODY_IN) * s


SHELF_L, SHELF_R = CXC - 840, CXC + 840  # 47 cm opening: the 43 cm player + ~2 cm each side
SHELF_TOP = TOP_FRONT + NOSE + 10


def cabinet_details(c):
    nb = TOP_FRONT + NOSE
    bl, br = body_x()
    c.drawLine(BACK_L + 2, CAB_TOP + 1, BACK_R - 2, CAB_TOP + 1, paint(C(20, 10, 6, 190), stroke=2.5))
    # deep shadow tucked under the nose
    c.drawRect(rect(bl, nb - 2, br, nb + 18), paint(C(10, 4, 2, 150), blur=8))
    # open shelf: dark interior, inner side walls receding toward the vanishing point
    l, r = SHELF_L, SHELF_R
    c.drawRect(rect(l, nb + 10, r, H + 10), paint(shader=lin(0, nb, 0, H, [C(14, 8, 5), C(30, 18, 11)])))
    s_back = proj_scale(DEPTH - 20) / proj_scale(BODY_IN)
    for x0, col in ((l, C(60, 34, 20)), (r, C(48, 27, 16))):
        xb = CXC + (x0 - CXC) * s_back
        p = skia.Path(); p.moveTo(x0, nb + 10); p.lineTo(xb, nb + 10); p.lineTo(xb, H + 10); p.lineTo(x0, H + 10); p.close()
        c.drawPath(p, paint(col))
    c.drawRect(rect(l, nb + 10, r, nb + 40), paint(shader=lin(0, nb + 10, 0, nb + 40, [C(0, 0, 0, 170), C(0, 0, 0, 0)])))
    # doors with arched raised panels
    for (dl, dr) in [(bl + 6, l - 8), (r + 8, br - 6)]:
        c.drawLine(dl - 4, nb + 6, dl - 4, H, paint(C(16, 8, 4, 220), stroke=4))
        c.drawLine(dr + 4, nb + 6, dr + 4, H, paint(C(16, 8, 4, 220), stroke=4))
        pl, pr = dl + 60, dr - 60
        top_y, peak = nb + 74, nb + 44
        arch = skia.Path(); arch.moveTo(pl, H + 20); arch.lineTo(pl, top_y)
        arch.cubicTo(pl + (pr - pl) * .2, peak, pl + (pr - pl) * .8, peak, pr, top_y); arch.lineTo(pr, H + 20)
        c.drawPath(arch, paint(C(12, 6, 3, 170), stroke=7, blur=2.5))
        a2 = skia.Path(arch); a2.offset(3, 4)
        c.drawPath(a2, paint(C(255, 200, 150, 46), stroke=2.5))
    for kx in (l - 40, r + 40):
        ky = nb + 64
        c.drawCircle(kx + 3, ky + 5, 13, paint(C(0, 0, 0, 120), blur=4))
        c.drawCircle(kx, ky, 12, paint(shader=rad(kx - 4, ky - 4, 16, [C(250, 224, 150), C(170, 126, 50), C(100, 70, 24)], [0, .6, 1])))


# a standard 43 cm full-width player (the 12 cm disc only bounds the tray from below; the case width is what's
# standardised: 43 full / 36 compact / 30 mini), its front at the shelf front = the body's set-back plane
VCD_W = 43 * px_per_cm(BODY_IN)


def place_vcd(rgba):
    """The VCD player (separate component, make_vcd.py) standing in the open shelf, pushed to the front.
    Its top cover rises toward the horizon and disappears behind the shelf ceiling."""
    vcd, (ox, oy) = make_vcd.build(VCD_W, lid_depth=96, lid_inset=34)
    h, w = vcd.shape[:2]
    x0, y0 = int(round(CXC - VCD_W / 2 - ox)), int(round(SHELF_TOP + 14 - oy))
    lay = np.zeros((H, W, 4), np.float32)
    sy0, sx0 = max(0, -y0), max(0, -x0)
    sy1, sx1 = min(h, H - y0), min(w, W - x0)
    lay[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1] = vcd[sy0:sy1, sx0:sx1]
    yy = np.arange(H, dtype=np.float32)[:, None]
    inside = np.clip(yy + .5 - SHELF_TOP, 0, 1)                         # hidden above the shelf ceiling
    lay[..., 3] *= inside[:, 0][:, None]
    lay[..., :3] *= (.52 + .48 * np.clip((yy - SHELF_TOP) / 80, 0, 1))[..., None]   # in the shelf's shade
    sh = Image.fromarray((lay[..., 3] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    sh = np.roll(np.asarray(sh, np.float32) / 255, (-6, 10), (0, 1)) * .55 * inside
    shadow = np.zeros((H, W, 4), np.float32); shadow[..., 3] = sh
    return over(lay, over(shadow, rgba))


def build():
    img = wall_layer()
    rgba = np.concatenate([img, np.ones((H, W, 1), np.float32)], -1)
    s = surface(); c = s.getCanvas(); c.clear(C(0, 0, 0, 0))
    wall_props(c); socket(c)
    rgba = over(to_np(s), rgba)
    rgb = cabinet_layer(rgba[..., :3])
    rgba = np.concatenate([rgb, np.ones((H, W, 1), np.float32)], -1)
    s2 = surface(); c2 = s2.getCanvas(); c2.clear(C(0, 0, 0, 0))
    cabinet_details(c2)
    rgba = over(to_np(s2), rgba)
    rgba = place_vcd(rgba)
    rgba[..., :3] *= (1 + .010 * grain(H, W, 99))[..., None]
    rgba[..., 3] = 1
    return rgba


if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    save_rgba(build(), "out/background.png")
    print("saved")
