#!/usr/bin/env python3
"""ra-native.py — recover a near-native low-res frame from an upscaled RetroArch
screenshot, so crt-studio.html gets a clean source instead of a blurry re-downsample.

Usage:
    python ra-native.py <screenshot> [out.png] [--w 256] [--h 240]

What it does (and why):
  * RA saves the screenshot at the WINDOW resolution (e.g. 3840x2160), aspect-
    corrected with black bars. Feeding that to the tool and letting it bilinear-
    downsample to 240 lines does NOT reconstruct the native pixel grid (width ends
    up ~320, not 256; JPEG artifacts bake in). This script instead:
  * trims only SYMMETRIC edge black bars — a bar on BOTH sides of an axis is a real
    pillar/letterbox; a one-sided black region (e.g. Contra's black sky at the top)
    is game content and is KEPT.
  * area-resamples the cropped game area straight to the native W x H (default NES
    256x240). Area/box filtering recovers integer-scaled pixels near-exactly and is
    the right (ring-free) filter for the non-integer axis too.
  * writes PNG (lossless) — never re-encode to JPEG.
Then in crt-studio load this PNG and set native H = 240 (width follows 4:3 via the
tube's DC_ASPECT, same as RA).
"""
import sys
from PIL import Image
import numpy as np

BLACK = 24   # max-channel <= this counts as "black"

def bars(mask_edge):
    """length of the run of False (all-black) from the start of a 1-D bool array."""
    idx = np.where(mask_edge)[0]
    return int(idx[0]) if len(idx) else 0

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = {sys.argv[i]: sys.argv[i+1] for i in range(len(sys.argv)-1) if sys.argv[i].startswith("--")}
    if not args:
        print(__doc__); sys.exit(1)
    src = args[0]
    out = args[1] if len(args) > 1 else src.rsplit(".", 1)[0] + "_native.png"
    W = int(opts.get("--w", 256)); Hn = int(opts.get("--h", 240))

    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(int)
    H, Wpx, _ = a.shape
    mx = a.max(axis=2)
    col_has = (mx > BLACK).any(axis=0)   # column has any non-black pixel
    row_has = (mx > BLACK).any(axis=1)

    left  = bars(col_has); right = bars(col_has[::-1])
    top   = bars(row_has); bot   = bars(row_has[::-1])

    # only trim an axis if BOTH edges have a black bar (true pillar/letterbox);
    # otherwise keep the full extent (one-sided black is game content).
    x0, x1 = (left, Wpx - right) if (left > 0 and right > 0) else (0, Wpx)
    y0, y1 = (top,  H  - bot)    if (top  > 0 and bot   > 0) else (0, H)

    crop = im.crop((x0, y0, x1, y1))
    print(f"image {Wpx}x{H}  bars L{left} R{right} T{top} B{bot}")
    print(f"game area {crop.width}x{crop.height} (x{x0}..{x1}, y{y0}..{y1})  aspect {crop.width/crop.height:.3f}")
    print(f"vscale {crop.height/Hn:.3f}  hscale {crop.width/W:.3f}")

    native = crop.resize((W, Hn), Image.Resampling.BOX)
    native.save(out)
    print(f"wrote {out}  ({W}x{Hn}, PNG)")

if __name__ == "__main__":
    main()
