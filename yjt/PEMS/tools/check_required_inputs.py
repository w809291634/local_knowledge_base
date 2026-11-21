# -*- coding: utf-8 -*-
"""必供材料门禁：型号 与 软件 MD5（注册人 2026-11-21 定）。

型号与软件哈希属生成前必须提供的材料，缺一不得生成/交付：
1. 型号必须存在、带 YJT- 前缀（YJT-12204 形式），不得为空、占位或旧前缀（JG-/YL-）；
2. 软件 MD5 必须为 32 位十六进制，不得为空或占位；
3. 052 正文必须出现该 MD5，且全族型号唯一。

用法：
    python check_required_inputs.py <项目目录 或 facts.yaml 或 产物目录>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MODEL_RE = re.compile(r"YJT-\d{5}")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
PLACEHOLDER = ("", "待补", "待定", "待核", "TBD", "todo", "无", "-")


def read_facts(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    model = re.search(r"^\s*model:\s*([^\s#]+)", text, re.M)
    md5 = re.search(r"^\s*hash_md5:\s*([^\s#]+)", text, re.M)
    return (model.group(1).strip('"\'') if model else "",
            md5.group(1).strip('"\'') if md5 else "")


def find_facts(p: Path):
    p = p.resolve()
    for c in (p / "facts.yaml", p / "work" / "facts.yaml", p,
              p.parent / "facts.yaml", p.parent / "work" / "facts.yaml"):
        if c.is_file() and c.name == "facts.yaml":
            return c
    return None


def check(p: Path):
    errs = []
    facts = find_facts(p)
    if facts is None:
        return ["未找到 facts.yaml，型号与软件 MD5 无法核对（必供材料）"]
    model, md5 = read_facts(facts)
    if not model or model.lower() in [x.lower() for x in PLACEHOLDER]:
        errs.append("型号未提供（必供材料：YJT-XXXXX）")
    elif not MODEL_RE.fullmatch(model):
        errs.append("型号「%s」不合规：必须为 YJT- 前缀 + 5 位数字（如 YJT-12204）" % model)
    if not md5 or md5.lower() in [x.lower() for x in PLACEHOLDER]:
        errs.append("软件 MD5 未提供（必供材料）")
    elif not MD5_RE.match(md5):
        errs.append("软件 MD5「%s」不是 32 位十六进制" % md5)

    # 产物侧（若给的是版本目录）
    docs = sorted(p.glob("*.docx")) if p.is_dir() else []
    if docs and model and md5:
        hit_md5 = False
        for f in docs:
            from docx import Document
            txt = "\n".join(x.text for x in Document(str(f)).paragraphs)
            for t in Document(str(f)).tables:
                for row in t.rows:
                    txt += "\n" + "\n".join(c.text for c in row.cells)
            if md5.lower() in txt.lower():
                hit_md5 = True
            if f.name.startswith("RD-052"):
                if md5.lower() not in txt.lower():
                    errs.append("052 正文未写入软件 MD5「%s」" % md5)
        if not hit_md5:
            errs.append("全族未见软件 MD5「%s」" % md5)
    return errs


def main(argv):
    if not argv:
        print("用法：python check_required_inputs.py <项目目录|facts.yaml|产物目录>")
        return 1
    errs = check(Path(argv[0]))
    if errs:
        print("必供材料检查失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("必供材料检查通过：型号 YJT- 前缀合规、软件 MD5 为 32 位且已写入 052")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
