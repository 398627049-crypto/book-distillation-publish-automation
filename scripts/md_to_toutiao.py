# -*- coding: utf-8 -*-
"""
把拆书笔记 markdown 转成头条友好纯文本正文：
保留全部内容深度，去 markdown 符号，表格转标签行。

用法:
  python md_to_toutiao.py --src 笔记.md --dst 正文.txt --title "AI蒸馏《书名》高保真拆书笔记"
"""
import argparse
import re


def strip_md(s):
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'\*(.+?)\*', r'\1', s)          # italic
    s = re.sub(r'`(.+?)`', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)  # links -> text
    return s


def convert(lines, title):
    out = []
    in_code = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            out.append(line)
            i += 1
            continue

        # markdown 表格
        if (re.match(r'^\s*\|?[\s:\-\|]+\|[\s:\-\|]*$', line)
                and '---' in line and i > 0 and '|' in lines[i - 1]):
            i += 1
            continue
        if line.strip().startswith('|') and i + 1 < len(lines) and '---' in lines[i + 1]:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            out.append('● ' + ' ｜ '.join(strip_md(c) for c in cells))
            i += 1
            if i < len(lines) and '---' in lines[i]:
                i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                out.append('   ' + ' ｜ '.join(strip_md(c) for c in cells))
                i += 1
            out.append('')
            continue

        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            text = strip_md(m.group(2))
            if len(m.group(1)) == 1:   # H1 主标题由 title 提供，避免重复
                i += 1
                continue
            out.append('')
            out.append('【' + text + '】')
            i += 1
            continue

        if line.strip().startswith('>'):
            content = strip_md(line.strip().lstrip('>').strip())
            if content:
                out.append('　' + content)
            i += 1
            continue

        if re.match(r'^\s*---+\s*$', line):
            out.append('——————————')
            i += 1
            continue

        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if m:
            indent = '　' if len(m.group(1)) >= 2 else ''
            out.append(indent + '· ' + strip_md(m.group(3)))
            i += 1
            continue

        out.append(strip_md(line))
        i += 1

    res = []
    blank = 0
    for ln in out:
        if ln.strip() == '':
            blank += 1
            if blank > 2:
                continue
        else:
            blank = 0
        res.append(ln)
    return title + '\n\n' + '\n'.join(res).strip() + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='输入 markdown 笔记')
    ap.add_argument('--dst', required=True, help='输出头条正文 txt')
    ap.add_argument('--title', required=True, help='文章标题，如 AI蒸馏《书名》高保真拆书笔记')
    args = ap.parse_args()

    with open(args.src, encoding='utf-8') as f:
        lines = f.read().splitlines()
    final = convert(lines, args.title)
    with open(args.dst, 'w', encoding='utf-8') as f:
        f.write(final)
    print('written:', args.dst)
    print('chars:', len(final))


if __name__ == '__main__':
    main()
