# -*- coding: utf-8 -*-
"""
通用书封增强：把一张真实书封原图做成头条竖版封面。
只用传入的这一张原图，不引入任何外部图片。

用法:
  python enhance_cover.py --src 原图.jpg --out 封面.png
  python enhance_cover.py --src 原图.jpg --out 封面.png --crop x0,y0,x1,y1

--crop 用于电商促销拼图：手动指定纯书封区域的像素坐标（左,上,右,下）。
不传 --crop 时自动检测白边裁切，适合纯白底书封。
"""
import argparse
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

CANVAS_W, CANVAS_H = 1024, 1536   # 头条竖版 2:3


def auto_crop(im):
    w, h = im.size
    px = im.load()

    def is_white(r, g, b):
        return r > 238 and g > 238 and b > 238 and (max(r, g, b) - min(r, g, b)) < 18

    col_count = [0] * w
    row_count = [0] * h
    for y in range(h):
        for x in range(w):
            if not is_white(*px[x, y]):
                col_count[x] += 1
                row_count[y] += 1
    ct = 6
    cols = [x for x in range(w) if col_count[x] > ct]
    rows = [y for y in range(h) if row_count[y] > ct]
    if not cols or not rows:
        return (0, 0, w, h)
    return (cols[0], rows[0], cols[-1] + 1, rows[-1] + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='书封原图路径')
    ap.add_argument('--out', required=True, help='输出封面路径(.png)')
    ap.add_argument('--crop', default=None, help='手动裁剪区 x0,y0,x1,y1（电商拼图用）')
    ap.add_argument('--height-ratio', type=float, default=0.82,
                    help='主体高度占画布比例，默认0.82；主体偏大溢出时调小(如0.78)')
    args = ap.parse_args()

    im = Image.open(args.src).convert('RGB')
    if args.crop:
        box = tuple(int(v) for v in args.crop.split(','))
        if len(box) != 4:
            raise SystemExit('--crop 需要 4 个数字: x0,y0,x1,y1')
        print(f'使用手动裁剪区: {box}')
    else:
        box = auto_crop(im)
        print(f'自动检测书封区域: {box} 尺寸 {box[2]-box[0]}x{box[3]-box[1]}')
    cover = im.crop(box)

    # 主体：高质量放大 + 增强
    target_h = int(CANVAS_H * args.height_ratio)
    scale = target_h / cover.height
    target_w = int(cover.width * scale)
    subject = cover.resize((target_w, target_h), Image.LANCZOS)
    subject = ImageEnhance.Contrast(subject).enhance(1.08)
    subject = ImageEnhance.Color(subject).enhance(1.10)
    subject = subject.filter(ImageFilter.UnsharpMask(radius=2.0, percent=150, threshold=3))
    subject = ImageEnhance.Sharpness(subject).enhance(1.25)

    # 背景：同一张书封放大铺满 + 强模糊 + 压暗去饱和
    bg = cover.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=60))
    bg = ImageEnhance.Color(bg).enhance(0.5)
    bg = ImageEnhance.Brightness(bg).enhance(0.78)

    canvas = bg.convert('RGB')

    # 柔光椭圆让主体中部突出
    mask = Image.new('L', (CANVAS_W, CANVAS_H), 0)
    md = ImageDraw.Draw(mask)
    cy = CANVAS_H // 2
    half = int(target_h * 0.62)
    md.ellipse([CANVAS_W // 2 - int(target_w * 0.95), cy - half,
                CANVAS_W // 2 + int(target_w * 0.95), cy + half], fill=85)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=80))
    canvas = Image.composite(bg, ImageEnhance.Brightness(bg).enhance(1.12), mask)

    # 主体投影（用主体自身做模糊，非外部图片）
    shadow = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    shadow_mask = subject.convert('L').point(lambda v: 120)
    shadow.putalpha(shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))

    sx = (CANVAS_W - target_w) // 2
    sy = (CANVAS_H - target_h) // 2
    canvas.paste(shadow, (sx + 10, sy + 16), shadow)
    canvas.paste(subject, (sx, sy))

    canvas.save(args.out, 'PNG', optimize=True)
    print(f'已生成封面: {args.out} 尺寸 {canvas.size}')


if __name__ == '__main__':
    main()
