"""Composite preview: background -> tv_frame -> props (-> doily). The tube/bezel/frame come from the shader, so a
preview optionally outlines where they will sit.  usage: python compose.py [nodoily] [outline]"""
import sys, os
from PIL import Image
from common import shader_frame, SCREEN_CENTER, TUBE_H, TUBE_ASPECT, BZL_W
bg = Image.open('out/background.png').convert('RGBA')
bg.alpha_composite(Image.open('out/tv_frame.png'))
if os.path.exists('out/props.png'):
    bg.alpha_composite(Image.open('out/props.png'))
if os.path.exists('out/doily.png') and 'nodoily' not in sys.argv:
    bg.alpha_composite(Image.open('out/doily.png'))
if 'outline' in sys.argv:                       # where the shader will draw: frame outer, bezel outer, tube
    from PIL import ImageDraw
    d = ImageDraw.Draw(bg)
    cx, cy = SCREEN_CENTER
    d.rectangle(shader_frame(), outline=(255, 0, 255, 255), width=3)
    for w_, col in ((BZL_W, (0, 200, 255, 255)), (0, (255, 220, 0, 255))):
        hh, hw = .5 * TUBE_H * (1 + 2 * w_), .5 * TUBE_H * (TUBE_ASPECT + 2 * w_)
        d.rectangle((cx - hw, cy - hh, cx + hw, cy + hh), outline=col, width=3)
name = 'preview' + ('_nodoily' if 'nodoily' in sys.argv else '')


def save(im, path):
    """An image viewer holding the file open (Windows) makes the save fail -> write next to it instead."""
    try:
        im.save(path)
    except OSError:
        alt = path.replace('.png', '_new.png')
        im.save(alt)
        print(f'{path} is locked (open in a viewer?) -> wrote {alt}')


save(bg.convert('RGB'), f'out/{name}_4k.png')
save(bg.convert('RGB').resize((1920, 1080), Image.LANCZOS), f'out/{name}_1080p.png')
for i, box in enumerate([(0, 0, 900, 700), (3000, 0, 3840, 900), (0, 1450, 1000, 2160), (3000, 1750, 3840, 2160), (300, 0, 1400, 300)]):
    bg.crop(box).convert('RGB').save(f'out/crop{i}.png')
