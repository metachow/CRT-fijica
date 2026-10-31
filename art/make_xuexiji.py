"""Duimon-style console background: a 1990s Chinese keyboard 'learning computer' (学习机), replicated from a
top-down photo of a Subor SB-486D, laid out the way the Famicom background of the TM20 preset is: the machine's top
surface blown up to fill the frame, the monitor covering the middle (x 485..3354), so what reads is what the two
side strips show — brand mascot + Esc/Tab/Caps/Shift/Ctrl on the left, model name + LED panel/knob + numpad on
the right — plus full-width bands (back vents, the raised back deck, the keyboard deck).
Geometry is measured in REFERENCE px of the photo and mapped with K. Brand/model are invented (BRAND/MODEL).
Output: out/xuexiji_bg.png (4K, opaque)."""
import math
import numpy as np
import skia
from common import *

BRAND, BRAND_LATIN, MODEL = "金童", "JINTONG", "JT-486D"
SIDE_L, SIDE_R = 485, 3354     # the TM20 covers [SIDE_L, SIDE_R]; only the two side strips show

IVORY = (232, 227, 208)
IVORY_D = (212, 206, 186)
CAP_IV = ((236, 232, 214), (198, 192, 172), (44, 42, 38))      # ivory keycap: top, skirt, legend ink
CAP_GR = ((158, 154, 142), (118, 114, 104), (44, 42, 38))      # warm-grey keycap
RED = (214, 40, 46)
BLUE = (40, 112, 196)

# photo -> frame mapping (photo body spans x 110..1810, y 420..1150; keyboard deck starts at y 540)
K = 2.25
BX = (W - 1700 * K) / 2
DECK_Y = H - 610 * K            # top of the keyboard deck in the frame; above it: back deck + vents


def mx(rx):
    return (rx - 110) * K + BX


def my(ry):
    return (ry - 540) * K + DECK_Y


U = (1260 - 185) / 15 * K      # key pitch: the 15-unit main block spans photo x 185..1260
KH = 66 * K                    # key height
X0 = mx(185)                   # left edge of the main block
ROW = dict(f=my(640), num=my(750), q=my(822), a=my(897), z=my(968), bot=my(1042))
# the photo is rotated ~2.5 deg (right side higher), so the right-hand clusters are NOT taken from it: they sit on
# the main block's rows and on a unit grid, like any 101-key board
NAV_U, PAD_U = 15.25, 18.55    # column (in U) where the editing cluster / numpad start


# ------------------------------------------------------------------ keycaps
def keycap(c, l, t, w, h=KH, scheme=CAP_IV, path=None, face_path=None):
    """Tall cylindrical-profile cap seen from above: the top face sits back, the front skirt shows below it.
    Returns the top face rect (l, t, r, b) for legends."""
    top, skirt, _ = scheme
    body = path or skia.Path().addRRect(rrect(l, t, l + w, t + h, 14))
    sh = skia.Path(body); sh.offset(5, 10)
    c.drawPath(sh, paint(C(40, 34, 20, 110), blur=8))
    c.drawPath(body, paint(shader=lin(0, t, 0, t + h, [C(*[min(255, v + 10) for v in skirt]), C(*skirt), C(*[int(v * .82) for v in skirt])], [0, .6, 1])))
    if path is None:
        fl, ft, fr, fb = l + w * .1 if w < 2 * U else l + 18, t + 8, l + w - (w * .1 if w < 2 * U else 18), t + h * .74
        face = skia.Path().addRRect(rrect(fl, ft, fr, fb, 12))
    else:                                                  # caller-shaped cap (L-shaped Enter) with its own face
        face = face_path
        fb_ = face.getBounds(); fl, ft, fr, fb = fb_.left(), fb_.top(), fb_.right(), fb_.bottom()
    c.drawPath(face, paint(shader=rad((fl + fr) / 2, (ft + fb) / 2 + 10, max(fr - fl, fb - ft) * .75,
                                      [C(*[int(v * .96) for v in top]), C(*top), C(*[min(255, v + 8) for v in top])], [0, .7, 1])))
    c.drawPath(face, paint(C(255, 255, 250, 90), stroke=1.6))
    return fl, ft, fr, fb


def legend(c, s, x, y, size, col=(44, 42, 38), weight="500"):
    c.drawString(s, x, y, font(size, weight), paint(C(*col)))


def key(c, u, row_y, wu=1.0, label="", top_label="", scheme=CAP_IV, size=34, x=None):
    l = X0 + u * U if x is None else x
    fl, ft, fr, fb = keycap(c, l + 6, row_y, wu * U - 12, KH, scheme)
    ink = scheme[2]
    if top_label:
        legend(c, top_label, fl + 14, ft + 40, 32, ink)
        legend(c, label, fl + 14, fb - 12, 36, ink)
    elif label:
        legend(c, label, fl + 14, ft + 40 if len(label) > 1 else fb - 14, size if len(label) > 1 else 40, ink)
    return fl, ft, fr, fb


WUBI = {  # 86-version key radicals (abbreviated) + area code, printed blue on the letter keys
    "Q": ("金钅勹", "儿犭夕", "35"), "W": ("人亻八", "癶", "34"), "E": ("月彡乃", "用豕", "33"),
    "R": ("白手扌", "斤", "32"), "T": ("禾竹彳", "攵", "31"), "Y": ("言讠文", "方广", "41"),
    "U": ("立六辛", "门疒", "42"), "I": ("水氵小", "", "43"), "O": ("火灬米", "", "44"),
    "P": ("之辶廴", "冖", "45"), "A": ("工匚七", "戈", "15"), "S": ("木丁西", "", "14"),
    "D": ("大犬三", "古石", "13"), "F": ("土士二", "干寸雨", "12"), "G": ("王五一", "", "11"),
    "H": ("目上止", "卜", "21"), "J": ("日早虫", "刂", "22"), "K": ("口川", "", "23"),
    "L": ("田甲囗", "四车", "24"), "X": ("纟幺弓", "匕", "55"), "C": ("又巴马", "厶", "54"),
    "V": ("女刀九", "臼", "53"), "B": ("子耳了", "也阝", "52"), "N": ("已己巳", "乙尸心", "51"),
    "M": ("山由贝", "冂", "25"),
}


def letter_key(c, u, row_y, ch):
    fl, ft, fr, fb = key(c, u, row_y)
    legend(c, ch, fl + (fr - fl) * .5, fb - 12, 38, CAP_IV[2], "700")
    if ch in WUBI:
        a, b, n = WUBI[ch]
        legend(c, a, fl + 8, ft + 30, 22, BLUE)
        if b:
            legend(c, b, fl + 8, ft + 56, 22, BLUE)
        legend(c, n, fl + 8, fb - 14, 18, BLUE)


def well(c, l, t, r, b):
    """Slightly darker, shadowed base around a key cluster (the gaps between caps)."""
    c.drawRRect(rrect(l, t, r, b, 10), paint(C(186, 178, 156)))
    c.drawRRect(rrect(l, t, r, t + 30, 10), paint(shader=lin(0, t, 0, t + 30, [C(70, 60, 40, 120), C(0, 0, 0, 0)])))


# ------------------------------------------------------------------ body
def body(c):
    c.drawPaint(paint(C(*IVORY)))
    # back vents (full width, like the Famicom's ribbed top)
    vt, vb = 60, DECK_Y - 520
    x = 26
    while x + 18 <= W - 20:
        c.drawRRect(rrect(x, vt, x + 18, vb, 9), paint(C(150, 142, 122)))
        c.drawRRect(rrect(x, vt, x + 18, vb, 9), paint(shader=lin(x, 0, x + 18, 0, [C(40, 34, 20, 170), C(0, 0, 0, 0), C(255, 255, 250, 110)]), stroke=2))
        x += 46
    # raised back deck: a lit front lip, then the step down to the keyboard deck in shadow
    c.drawRect(rect(0, DECK_Y - 40, W, DECK_Y), paint(shader=lin(0, DECK_Y - 40, 0, DECK_Y, [C(*IVORY), C(*IVORY_D)])))
    c.drawLine(0, DECK_Y - 40, W, DECK_Y - 40, paint(C(255, 255, 250, 200), stroke=2.5))
    c.drawRect(rect(0, DECK_Y, W, DECK_Y + 60), paint(shader=lin(0, DECK_Y, 0, DECK_Y + 60, [C(90, 78, 52, 120), C(0, 0, 0, 0)])))


def back_deck(c):
    # mascot emblem + red brand (left strip)
    cx, cy = mx(205), my(470) - 120
    c.drawCircle(cx, cy, 112, paint(C(*RED)))
    c.drawCircle(cx, cy, 92, paint(C(246, 240, 226)))
    book = skia.Path()
    book.moveTo(cx - 62, cy - 4); book.quadTo(cx - 31, cy - 22, cx, cy - 2); book.quadTo(cx + 31, cy - 22, cx + 62, cy - 4)
    book.lineTo(cx + 62, cy + 46); book.quadTo(cx + 31, cy + 28, cx, cy + 48); book.quadTo(cx - 31, cy + 28, cx - 62, cy + 46); book.close()
    c.drawPath(book, paint(C(*RED)))
    c.drawLine(cx, cy - 2, cx, cy + 48, paint(C(246, 240, 226), stroke=4))
    st = skia.Path()
    for i in range(10):
        rr = 26 if i % 2 == 0 else 11
        a = -math.pi / 2 + i * math.pi / 5
        (st.moveTo if i == 0 else st.lineTo)(cx + rr * math.cos(a), cy - 50 + rr * math.sin(a))
    st.close(); c.drawPath(st, paint(C(230, 170, 30)))
    text_center(c, BRAND, cx, cy + 150, font(44, "900"), paint(C(*RED)))
    c.drawString(BRAND, SIDE_L + 70, cy + 64, font(190, "900"), paint(C(*RED)))         # wholly under the TM20 (no half glyph peeking)
    # cartridge flap (centre; under the monitor in the TM20 layout)
    l, t, r, b = mx(745), my(430) - 260, mx(1235), DECK_Y - 60
    c.drawRect(rect(l - 10, t - 10, r + 10, b + 10), paint(C(150, 140, 116)))
    c.drawRect(rect(l, t, r, b), paint(shader=lin(0, t, 0, b, [C(*IVORY), C(*IVORY_D)])))
    c.drawLine(l, t + 2, r, t + 2, paint(C(255, 255, 250, 180), stroke=2))
    tx = (l + r) / 2
    c.drawRRect(rrect(tx - 60, b - 34, tx + 60, b + 4, 6), paint(shader=lin(0, b - 34, 0, b, [C(*IVORY), C(*IVORY_D)])))
    for i in range(5):
        c.drawLine(tx - 40, b - 26 + i * 6, tx + 40, b - 26 + i * 6, paint(C(150, 140, 116), stroke=1.6))
    # name + model (right; the model sits in the visible strip)
    serif = font(78, "700", SERIF)
    rx = W - 70
    mw = serif.measureText(MODEL)
    c.drawString(MODEL, rx - mw, cy + 40, serif, paint(C(36, 34, 30)))
    nf = font(80, "500", SERIF)
    c.drawString("中英文电脑学习机", SIDE_R - 70 - nf.measureText("中英文电脑学习机"), cy + 40, nf, paint(C(36, 34, 30)))
    # gold italic latin brand on the keyboard deck (under the monitor)
    c.save(); c.translate(W / 2, DECK_Y + 130); c.skew(-.2, 0)
    gf = skia.Font(skia.Typeface.MakeFromName("Times New Roman", skia.FontStyle.Bold()), 96)
    w_ = gf.measureText(BRAND_LATIN)
    c.drawString(BRAND_LATIN, -w_ / 2 + 2, 3, gf, paint(C(80, 60, 20, 150)))
    c.drawString(BRAND_LATIN, -w_ / 2, 0, gf, paint(shader=lin(0, -70, 0, 0, [C(246, 214, 120), C(196, 150, 50), C(150, 110, 30)])))
    c.restore()


def keyboard(c):
    nav_x, pad_x = X0 + NAV_U * U, X0 + PAD_U * U
    rows = [ROW["num"], ROW["q"], ROW["a"], ROW["z"], ROW["bot"]]
    # cluster wells (the shadowed base between the caps), cut to the clusters' own key grid
    well(c, X0 - 14, ROW["f"] - 14, X0 + 14.81 * U + 14, ROW["f"] + KH + 14)
    well(c, X0 - 14, ROW["num"] - 14, X0 + 15 * U + 14, ROW["bot"] + KH + 14)
    well(c, nav_x - 14, ROW["f"] - 14, nav_x + 3 * U + 14, ROW["f"] + KH + 14)
    well(c, nav_x - 14, ROW["num"] - 14, nav_x + 3 * U + 14, ROW["q"] + KH + 14)
    well(c, nav_x + U - 14, ROW["z"] - 14, nav_x + 2 * U + 14, ROW["bot"])
    well(c, nav_x - 14, ROW["bot"] - 14, nav_x + 3 * U + 14, ROW["bot"] + KH + 14)
    well(c, pad_x - 14, ROW["num"] - 14, pad_x + 4 * U + 14, ROW["bot"] + KH + 14)

    G = CAP_GR
    # function row
    key(c, 0, ROW["f"] + 30, 1, "Esc", scheme=G)
    for i in range(4):
        key(c, 1.88 + i, ROW["f"], 1, f"F{i + 1}")
    for i in range(4):
        key(c, 6.42 + i, ROW["f"], 1, f"F{i + 5}", scheme=G)
    for i in range(4):
        key(c, 10.81 + i, ROW["f"], 1, f"F{i + 9}")
    for i, s in enumerate(["Pause", "Break", "Reset"]):
        key(c, NAV_U + i, ROW["f"], 1, s, scheme=G, size=26)
    # number row
    for i, (lo, hi) in enumerate([("`", "~"), ("1", "!"), ("2", "@"), ("3", "#"), ("4", "$"), ("5", "%"), ("6", "^"),
                                  ("7", "&"), ("8", "*"), ("9", "("), ("0", ")"), ("-", "_"), ("=", "+"), ("\\", "|")]):
        key(c, i, ROW["num"], 1, lo, hi)
    key(c, 14, ROW["num"], 1, "←", scheme=G)
    # letter rows
    key(c, 0, ROW["q"], 1.5, "Tab", scheme=G)
    for i, ch in enumerate("QWERTYUIOP"):
        letter_key(c, 1.5 + i, ROW["q"], ch)
    key(c, 11.5, ROW["q"], 1, "[", "{"); key(c, 12.5, ROW["q"], 1, "]", "}")
    key(c, 0, ROW["a"], 1.75, "Caps", scheme=G)
    for i, ch in enumerate("ASDFGHJKL"):
        letter_key(c, 1.75 + i, ROW["a"], ch)
    key(c, 10.75, ROW["a"], 1, ";", ":"); key(c, 11.75, ROW["a"], 1, "'", '"')
    # L-shaped Enter spanning the Q and A rows
    ent = skia.Path()
    ex0, ex1, ex2 = X0 + 13.5 * U + 6, X0 + 12.75 * U + 6, X0 + 15 * U - 6
    ent.moveTo(ex0, ROW["q"]); ent.lineTo(ex2, ROW["q"]); ent.lineTo(ex2, ROW["a"] + KH)
    ent.lineTo(ex1, ROW["a"] + KH); ent.lineTo(ex1, ROW["a"]); ent.lineTo(ex0, ROW["a"]); ent.close()
    face = skia.Path()
    face.moveTo(ex0 + 14, ROW["q"] + 8); face.lineTo(ex2 - 14, ROW["q"] + 8); face.lineTo(ex2 - 14, ROW["a"] + KH * .74)
    face.lineTo(ex1 + 14, ROW["a"] + KH * .74); face.lineTo(ex1 + 14, ROW["a"] + 8); face.lineTo(ex0 + 14, ROW["a"] + 8); face.close()
    keycap(c, 0, ROW["q"], 0, KH, G, path=ent, face_path=face)
    legend(c, "Enter", ex1 + 22, ROW["a"] + 70, 28, G[2])
    ax, ay = ex1 + 120, ROW["a"] + 60                              # the bent return arrow
    arr = skia.Path(); arr.moveTo(ax + 60, ay - 22); arr.lineTo(ax + 60, ay); arr.lineTo(ax, ay)
    pa = paint(C(*G[2]), stroke=3); pa.setStrokeJoin(skia.Paint.kMiter_Join); c.drawPath(arr, pa)
    hd = skia.Path(); hd.moveTo(ax - 2, ay); hd.lineTo(ax + 14, ay - 9); hd.lineTo(ax + 14, ay + 9); hd.close()
    c.drawPath(hd, paint(C(*G[2])))
    key(c, 0, ROW["z"], 2.25, "⇧ Shift", scheme=G, size=28)
    for i, ch in enumerate("ZXCVBNM"):
        letter_key(c, 2.25 + i, ROW["z"], ch)
    for i, (lo, hi) in enumerate([(",", "<"), (".", ">"), ("/", "?")]):
        key(c, 9.25 + i, ROW["z"], 1, lo, hi)
    key(c, 12.25, ROW["z"], 2.75, "⇧ Shift", scheme=G, size=28)
    key(c, 0, ROW["bot"], 1.5, "Ctrl", scheme=G)
    key(c, 2.5, ROW["bot"], 1.5, "Alt", scheme=G)
    key(c, 4, ROW["bot"], 6.75)
    key(c, 10.75, ROW["bot"], 1.25, "Alt", scheme=G)
    key(c, 13.25, ROW["bot"], 1.25, "Ctrl", scheme=G)
    # editing cluster + arrows, on the main rows and the cluster's own three columns
    for r, names in ((ROW["num"], ["Insert", "Home", "Page Up"]), (ROW["q"], ["Delete", "End", "Page Dn"])):
        for i, s in enumerate(names):
            key(c, NAV_U + i, r, 1, s, scheme=G, size=24)
    key(c, NAV_U + 1, ROW["z"], 1, "↑", scheme=G)
    for i, s in enumerate(["←", "↓", "→"]):
        key(c, NAV_U + i, ROW["bot"], 1, s, scheme=G)
    # numpad
    for i, s in enumerate(["Num", "/", "*", "−"]):
        key(c, PAD_U + i, rows[0], 1, s, scheme=G, size=28)
    for r, trio in ((1, [("7", "Home"), ("8", "↑"), ("9", "PgUp")]), (2, [("4", "←"), ("5", ""), ("6", "→")]),
                    (3, [("1", "End"), ("2", "↓"), ("3", "PgDn")])):
        for i, (d, sub) in enumerate(trio):
            fl, ft, fr, fb = key(c, PAD_U + i, rows[r], 1)
            legend(c, d, fl + 14, ft + 42, 40, CAP_IV[2])
            if sub:
                legend(c, sub, fl + 14, fb - 12, 22, CAP_IV[2])
    for r0, s in ((1, "+"), (3, "Enter")):                         # tall + and Enter
        l = pad_x + 3 * U + 6
        fl, ft, fr, fb = keycap(c, l, rows[r0], U - 12, rows[r0 + 1] + KH - rows[r0], G)
        legend(c, s, fl + 14, ft + 46 if s == "+" else fb - 20, 40 if s == "+" else 26, G[2])
    fl, ft, fr, fb = key(c, PAD_U, rows[4], 2)
    legend(c, "0", fl + 14, ft + 42, 40, CAP_IV[2]); legend(c, "Ins", fl + 14, fb - 12, 22, CAP_IV[2])
    fl, ft, fr, fb = key(c, PAD_U + 2, rows[4], 1)
    legend(c, ".", fl + 14, ft + 42, 40, CAP_IV[2]); legend(c, "Del", fl + 14, fb - 12, 22, CAP_IV[2])


def led_panel(c):
    """Sage-grey indicator strip (Num Lock / Caps / Power) and the round knob, top-right."""
    l, t, r, b = X0 + PAD_U * U, ROW["f"] - 16, X0 + (PAD_U + 2.75) * U, ROW["f"] + KH - 6   # over the numpad, on the F row
    c.drawRect(rect(l - 6, t - 6, r + 6, b + 6), paint(C(150, 146, 128)))
    c.drawRect(rect(l, t, r, b), paint(shader=lin(0, t, 0, b, [C(176, 186, 168), C(160, 170, 152)])))
    c.drawRect(rect(l, t, r, t + 14), paint(C(60, 60, 40, 60), blur=4))
    cw = (r - l) / 3
    for i, (s, on) in enumerate([("Num Lock", True), ("Caps", False), ("Power", True)]):
        x = l + i * cw
        if i:
            c.drawLine(x, t + 6, x, b - 6, paint(C(120, 126, 108), stroke=2))
        text_center(c, s, x + cw / 2, t + 62, skia.Font(skia.Typeface.MakeFromName("Arial", skia.FontStyle.Normal()), 22), paint(C(110, 116, 100)))
        lc = (60, 220, 90) if on else (60, 80, 60)
        c.drawRect(rect(x + cw / 2 - 18, t + 92, x + cw / 2 + 18, t + 104), paint(C(*lc)))
        if on:
            c.drawRect(rect(x + cw / 2 - 26, t + 86, x + cw / 2 + 26, t + 110), paint(C(*lc, 90), blur=8))
    kx, ky = X0 + (PAD_U + 3.5) * U, (t + b) / 2
    c.drawCircle(kx, ky, 70, paint(C(150, 146, 128)))
    c.drawCircle(kx, ky, 62, paint(C(60, 58, 52)))
    c.drawCircle(kx + 4, ky + 8, 48, paint(C(0, 0, 0, 120), blur=6))
    c.drawCircle(kx, ky, 46, paint(shader=rad(kx - 16, ky - 18, 70, [C(250, 246, 232), C(206, 200, 180), C(150, 144, 124)], [0, .5, 1])))


def build():
    s = surface(); c = s.getCanvas()
    body(c); back_deck(c); keyboard(c); led_panel(c)
    img = to_np(s)
    # moulded-plastic texture, yellowing (the classic beige-to-ivory drift), grime settling low
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tex = 1 + .012 * grain(H, W, 5) + .018 * fbm(H, W, 300, 4, 6)
    yellow = np.clip(fbm(H, W, 900, 3, 7) * .5 + .5, 0, 1)
    img[..., :3] *= tex[..., None]
    img[..., :3] *= (1 - .06 * yellow[..., None] * np.array([0, .3, 1.0]))
    img[..., :3] *= (1.03 - .06 * yy / H)[..., None]
    img[..., 3] = 1
    return img


if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    save_rgba(build(), "out/xuexiji_bg.png")
    print("saved")
