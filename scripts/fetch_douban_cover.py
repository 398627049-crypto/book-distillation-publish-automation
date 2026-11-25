# -*- coding: utf-8 -*-
"""从豆瓣图书抓取纯书封大图（1000px+，无电商促销水印）。

当当/京东商品主图为 JS 动态渲染或带促销水印，urllib 与 WebFetch 常拿不到干净
书封；豆瓣 subject 页的 <meta property="og:image"> 稳定可用，是纯书封最可靠来源。

用法：
  python fetch_douban_cover.py --sid 35546622 --out "D:/book-notes/置身事内-书封原图.jpg"
  python fetch_douban_cover.py --isbn 9787208171336 --out "D:/book-notes/置身事内-书封原图.jpg"

说明：
  --isbn 走 https://book.douban.com/isbn/<ISBN>/ 重定向到 subject 页；
  --sid  直接请求 https://book.douban.com/subject/<ID>/ ；
  两者二选一。若豆瓣反爬触发 403，脚本会提示改用浏览器打开 subject 页，
  从页面 <meta property="og:image"> 手动取 URL 后用 --url 兜底。

依赖：仅标准库（urllib / re / argparse），无需第三方包。
"""
import argparse
import re
import sys
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')


def fetch_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')


def extract_og_image(html):
    # 兼容两种属性顺序
    patterns = [
        r'property="og:image"\s+content="([^"]+)"',
        r'content="([^"]+)"\s+property="og:image"',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


def extract_title(html):
    m = re.search(r'<span property="v:itemreviewed">([^<]+)</span>', html)
    return m.group(1) if m else None


def download_image(url, out_path):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://book.douban.com/',
    })
    data = urllib.request.urlopen(req, timeout=25).read()
    with open(out_path, 'wb') as f:
        f.write(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sid', help='豆瓣 subject ID（数字）')
    ap.add_argument('--isbn', help='ISBN，脚本走 /isbn/ 重定向拿 subject 页')
    ap.add_argument('--url', help='直接给 og:image 图片 URL（豆瓣反爬时手动兜底）')
    ap.add_argument('--out', required=True, help='输出图片路径，如 <书名>-书封原图.jpg')
    args = ap.parse_args()

    if not (args.sid or args.isbn or args.url):
        ap.error('必须提供 --sid / --isbn / --url 之一')

    try:
        if args.url:
            cover = args.url
            print('使用直接提供的图片 URL')
        else:
            if args.isbn:
                page = 'https://book.douban.com/isbn/{}/'.format(args.isbn)
            else:
                page = 'https://book.douban.com/subject/{}/'.format(args.sid)
            html = fetch_html(page)
            title = extract_title(html)
            cover = extract_og_image(html)
            print('豆瓣页面:', page)
            print('书名:', title or '(未取到)')
            if not cover:
                print('ERROR: 未找到 og:image，豆瓣可能反爬；请用浏览器打开页面取图片 URL 后用 --url', file=sys.stderr)
                sys.exit(2)
            print('封面:', cover)

        size = download_image(cover, args.out)
        print('已保存: {} ({} bytes)'.format(args.out, size))

        # 尝试输出尺寸
        try:
            from PIL import Image
            im = Image.open(args.out)
            print('尺寸:', im.size)
        except ImportError:
            pass
    except Exception as e:
        print('ERROR: {}'.format(e), file=sys.stderr)
        print('若豆瓣反爬 403，改用浏览器打开 subject 页取 og:image 后传 --url', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
