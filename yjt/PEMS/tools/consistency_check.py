# -*- coding: utf-8 -*-
"""
consistency_check —— 多文档一致性自检（配置驱动，通用）
======================================================
用法：
    python consistency_check.py --config config.json [--dir 产物目录]

config 相关字段：
{
  "check": {
    "docs": ["a.docx", "b.docx"],          # 可选：显式列出，或改用 --dir
    "key_pattern": "[A-Z]{2,3}-\\\\d{5}",   # 主键（型号）正则，可换项目
    "keywords": { "安全项名": ["关键字1","关键字2"], ... }
  }
}
输出：主键集合差集 + 关键字覆盖缺失。图与签署栏需人工核对。
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_ops import extract_text, convert_doc_to_docx


def text_of(path):
    if path.lower().endswith('.docx'):
        return extract_text(path)
    tmp = os.path.splitext(path)[0] + '__conv.docx'
    if not os.path.exists(tmp):
        convert_doc_to_docx(path, tmp)
    return extract_text(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--dir', default=None, help='目录下全部 doc/docx')
    args = ap.parse_args()
    with open(args.config, encoding='utf-8') as f:
        cfg = json.load(f)
    check = cfg.get('check', {})

    paths = []
    if args.dir:
        for f in sorted(os.listdir(args.dir)):
            if f.lower().endswith(('.doc', '.docx')):
                paths.append(os.path.join(args.dir, f))
    paths += list(check.get('docs', []))
    if not paths:
        print('未提供待检文档（--dir 或 config.check.docs）'); sys.exit(1)

    texts = {os.path.basename(p): text_of(p) for p in paths}
    print('=== 文档 ===')
    for k, v in texts.items():
        print('  %-50s %d 字符' % (k, len(v)))

    # 1) 主键集合差集
    pat = re.compile(check.get('key_pattern', r'[A-Z]{2,3}-\d{5}'))
    sets = {k: set(pat.findall(v)) for k, v in texts.items()}
    print('\n=== 主键集合 ===')
    for k, v in sets.items():
        head = ','.join(sorted(v)[:6]) + ('...' if len(v) > 6 else '')
        print('  %-50s %d 个: %s' % (k, len(v), head))
    names = list(sets)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = sets[names[i]], sets[names[j]]
            if a - b:
                print('  [差] %s 有而 %s 无 (%d): %s'
                      % (names[i], names[j], len(a - b), ','.join(sorted(a - b)[:10])))
            if b - a:
                print('  [差] %s 有而 %s 无 (%d): %s'
                      % (names[j], names[i], len(b - a), ','.join(sorted(b - a)[:10])))

    # 2) 关键字覆盖
    print('\n=== 关键字覆盖 ===')
    for label, kws in check.get('keywords', {}).items():
        miss = [k for k, v in texts.items() if not any(w in v for w in kws)]
        print('  %-16s 缺失于: %s' % (label, miss if miss else '（全部命中）'))

    print('\n提醒：图（框图/界面图）与签署栏脚本无法核对，需人工确认。')


if __name__ == '__main__':
    main()