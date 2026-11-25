# -*- coding: utf-8 -*-
"""把本地 PNG/JPG 图片以 CF_DIB 位图格式放入 Windows 系统剪贴板，
供头条编辑器 Ctrl+V 粘贴上传使用。"""
import sys
import io
from PIL import Image
import win32clipboard

path = sys.argv[1]
im = Image.open(path).convert('RGB')

# 转 BMP，取 DIB 部分（跳过 BMP 文件头 14 字节）
buf = io.BytesIO()
im.save(buf, format='BMP')
data = buf.getvalue()
dib = data[14:]

win32clipboard.OpenClipboard()
try:
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
finally:
    win32clipboard.CloseClipboard()

print(f'已放入剪贴板: {path} 尺寸 {im.size} DIB字节 {len(dib)}')
