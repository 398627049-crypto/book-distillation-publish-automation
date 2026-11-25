# -*- coding: utf-8 -*-
"""
封面与正文自检工具（阶段二/三复检用）：

1) 扫描中文正文里混入的英文词（列出行号与命中，供人工判断是否为允许的专有名词）
2) 检查书名是否在正文中出现
3) 检测封面图片尺寸（是否为 1024x1536 竖版）

用法:
  python cover_lint.py --text 笔记.md --book "书名" [--cover 封面.png]
"""
import argparse
import re
import sys

try:
    from PIL import Image
except ImportError:
    Image = None


def scan_english(path):
    hits = []
    with open(path, encoding='utf-8') as f:
        for no, line in enumerate(f, 1):
            for m in re.finditer(r'[A-Za-z]{2,}', line):
                token = m.group(0)
                # 跳过明显的 URL / 域名片段
                hits.append((no, token, line.strip()[:100]))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text', required=True, help='待检查的 markdown/txt 正文')
    ap.add_argument('--book', required=True, help='书名（检查是否出现）')
    ap.add_argument('--cover', default=None, help='可选的封面图路径（检查尺寸）')
    args = ap.parse_args()

    content = open(args.text, encoding='utf-8').read()
    key = args.book.replace('《', '').replace('》', '')
    print(f'书名 "{key}" 出现次数: {content.count(key)}')

    hits = scan_english(args.text)
    print(f'英文词命中 {len(hits)} 处（专有名词/URL 域名可保留，其余需改中文）:')
    for no, token, snippet in hits:
        print(f'  L{no}: {token}  |  {snippet}')

    if args.cover:
        if Image is None:
            print('未安装 Pillow，跳过图片尺寸检查')
        else:
            im = Image.open(args.cover)
            w, h = im.size
            ok = 'OK' if (w, h) == (1024, 1536) else '尺寸非 1024x1536，请检查'
            print(f'封面尺寸: {w}x{h} -> {ok}')


if __name__ == '__main__':
    main()
