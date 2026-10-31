"""TV-light receptivity of the room art (SpillMask for dc-composite): how much light each background pixel
receives from the TV picture, 0..1. The shader multiplies it by the picture's blurred colour (DC_SPILL), so this
is geometry only: the tube is a Lambertian area light facing the viewer, placed in the cabinet's perspective
model (make_bg); receivers are what faces it —
  * the cabinet top in front of the set (and the props on it): E = sum cos_emit * cos_recv / r^2,
  * the upper half of the half-round front edge (it still faces up),
  * everything else (wall, the set's own face, the shelf, the VCD) only gets a faint room bounce:
    the screen faces away from / along them.
G channel = the glossy (varnished) cabinet top that is actually visible — not under the set or a prop — where
dc-composite mirrors the picture (GLOSS_*).
Output: out/spill.png (4K, RGB, linear: R = TV-light receptivity, G = glossy surface)."""
import numpy as np
from PIL import Image, ImageFilter
from common import W, H, SCREEN_CENTER, TUBE_H, TUBE_ASPECT
from make_bg import (CXC, HORIZON, H0, DEPTH, NOSE, CAB_TOP, proj_scale, plan_coords, top_sdf, sdf_coverage)

BOUNCE = 0.08          # faint room bounce everywhere (walls / ceiling re-scatter the TV light)
BOUNCE_REACH = 1100    # px


def screen_samples(nx=16, ny=12):
    """Tube as nx*ny patches on the set's face plane (d = DEPTH): plan X, height above the top, patch area."""
    s = proj_scale(DEPTH)
    cx, cy = SCREEN_CENTER
    hw, hh = .5 * TUBE_H * TUBE_ASPECT, .5 * TUBE_H
    xs = cx + (np.arange(nx) + .5) / nx * 2 * hw - hw
    ys = cy + (np.arange(ny) + .5) / ny * 2 * hh - hh
    X = (xs - CXC) / s
    Hh = H0 - (ys - HORIZON) / s
    XX, HH = np.meshgrid(X, Hh)
    return XX.ravel(), HH.ravel()


def top_irradiance(X, d):
    """Irradiance on the cabinet top at plan (X, d) from the tube (unnormalised)."""
    sx, sh = screen_samples()
    E = np.zeros_like(X)
    for x_s, h_s in zip(sx, sh):
        dz = DEPTH - d                                   # in front of the face plane (> 0)
        r2 = (X - x_s) ** 2 + dz ** 2 + h_s ** 2
        E += np.clip(dz, 0, None) * h_s / r2 ** 2        # cos_emit * cos_recv / r^2 = (dz/r)(h/r)/r^2
    return E


def build():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # cabinet top coverage, as drawn by make_bg
    X, d = plan_coords(xx + .5, yy + .5)
    a_top = sdf_coverage(top_sdf(X, d)) * np.clip(yy + .5 - CAB_TOP, 0, 1)

    # direct light on the top plane, on a coarse grid then upsampled (it is smooth)
    k = 8
    cy_, cx_ = np.mgrid[0:H // k, 0:W // k].astype(np.float32)
    Xc, dc = plan_coords(cx_ * k + k / 2, cy_ * k + k / 2)
    Ec = np.where((cy_ * k + k / 2 > CAB_TOP) & (dc > 0) & (dc < DEPTH), top_irradiance(Xc, dc), 0)
    Ec /= Ec.max()
    E = np.asarray(Image.fromarray(Ec.astype(np.float32)).resize((W, H), Image.BICUBIC), np.float32)
    E = np.clip(E, 0, 1)

    # half-round front edge: the rows just under the top's front outline; its upper half still faces up
    solid = a_top > .5
    ye = np.where(solid, np.arange(H)[:, None], -1).max(0)            # front outline per column
    cols = np.arange(W)
    has = ye > 0
    e_front = np.where(has, E[np.clip(ye - 2, 0, H - 1), cols], 0)
    _, d_front = plan_coords(cols + .5, np.maximum(ye, CAB_TOP + 1).astype(np.float32))
    nose_h = NOSE * proj_scale(np.clip(d_front, 0, None))
    v = (yy - ye[None, :]) / np.maximum(nose_h[None, :], 1)            # 0 at the top edge .. 1 at the bottom
    nose = np.where(has[None, :] & (v > 0) & (v < 1), np.clip(1 - v / .5, 0, 1) * e_front[None, :], 0)

    m = a_top * E + nose
    # the set itself stands on the top: its pixels get only the bounce
    tv = np.asarray(Image.open("out/tv_frame.png"), np.float32)[..., 3] / 255
    m *= 1 - tv
    # props on the top: their top faces sit on (just above) the plane -> same light as the top under them
    props_a = np.asarray(Image.open("out/props.png"), np.float32)[..., 3] / 255
    m = np.maximum(m, props_a * np.clip(E, 0, 1))
    # faint bounce everywhere
    dist = np.hypot(xx - SCREEN_CENTER[0], yy - SCREEN_CENTER[1])
    m = np.maximum(m, BOUNCE * np.exp(-dist / BOUNCE_REACH))
    m = np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)))
    gloss = a_top * (1 - tv) * (1 - props_a)
    g = np.asarray(Image.fromarray((np.clip(gloss, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)))
    return np.stack([m, g, np.zeros_like(m)], -1)


if __name__ == "__main__":
    Image.fromarray(build(), "RGB").save("out/spill.png", optimize=True)
    print("saved")
