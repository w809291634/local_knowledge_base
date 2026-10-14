# -*- coding: utf-8 -*-
"""
build_docs —— 通用文档生成入口（配置驱动，不含任何项目数据）
============================================================
用法：
    python build_docs.py --config config.json

config.json 结构（详见 config.example.json）：
{
  "tpl_dir": "模板目录(只读)",
  "out_dir": "输出目录_V1",
  "files":   { "key": ["模板文件名.docx", "输出文件名_V1.docx"] },
  "global_subs": [["旧串","新串"], ...],          # 全局词替换，长串在前
  "paras":   { "key": [ [匹配片段, 标签或null, 新正文, ["追加段落", ...]], ... ] },
  "tables":  { "key": [ [表序号, 表头行数, [数据行...], 表头覆盖或null, 首行覆盖或null] ] }
}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_ops import (open_template, paragraph_text, set_paragraph,
                      apply_substitutions, insert_paragraphs_after,
                      fill_table, save_doc, trim_cover_spacers,
                      ensure_cover_page_break, describe_blocks)


def build_one(key, files_cfg, cfg, verbose=False):
    tpl_name, out_name = files_cfg
    doc = open_template(os.path.join(cfg['tpl_dir'], tpl_name))
    if verbose:
        print(describe_blocks(doc))

    subs = [tuple(x) for x in cfg.get('global_subs', [])]
    para_map = cfg.get('paras', {}).get(key, [])

    # 1) 段落：段落级映射优先，其余走全局替换
    used = set()
    for p in doc.paragraphs:
        if not paragraph_text(p).strip():
            continue
        hit = None
        for i, item in enumerate(para_map):
            if i in used:
                continue
            match, label = item[0], item[1]
            text = item[2]
            extras = item[3] if len(item) > 3 else []
            if match in paragraph_text(p):
                hit = (label, text, extras)
                used.add(i)
                break
        if hit:
            set_paragraph(p, hit[1], hit[0])
            if hit[2]:
                insert_paragraphs_after(p, hit[2])
        else:
            apply_substitutions(p, subs)

    # 2) 表格：先按配置填充，再对未接管单元格做全局替换
    for item in cfg.get('tables', {}).get(key, []):
        idx, hrows, rows = item[0], item[1], item[2]
        htexts = item[3] if len(item) > 3 else None
        row0 = item[4] if len(item) > 4 else None
        fill_table(doc, idx, hrows, rows, htexts, row0)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    apply_substitutions(p, subs)

    # 3) 封面：清空段 + 保证独立成页
    trim_cover_spacers(doc, cfg.get('cover_first_cell', '文件编号'))
    ensure_cover_page_break(doc, cfg.get('cover_first_cell', '文件编号'))

    return save_doc(doc, cfg['out_dir'], out_name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--only', default=None, help='仅生成指定 key')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()
    with open(args.config, encoding='utf-8') as f:
        cfg = json.load(f)
    keys = [args.only] if args.only else list(cfg['files'].keys())
    for k in keys:
        out = build_one(k, cfg['files'][k], cfg, verbose=args.verbose)
        print('OK', out)


if __name__ == '__main__':
    main()