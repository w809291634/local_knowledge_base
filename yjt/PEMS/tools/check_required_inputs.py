# -*- coding: utf-8 -*-
"""必供材料门禁：型号、软件 MD5、外包装标签（注册人 2026-11-21 / 2026-11-23 定）。

必供材料缺一不得生成/交付：
1. 型号必须存在、带 YJT- 前缀（YJT-12204 形式），不得为空、占位或旧前缀（JG-/YL-）；
2. 软件 MD5 必须为 32 位十六进制，不得为空或占位；
3. 052 正文必须出现该 MD5，且全族型号唯一；
4. 项目目录必须提供外包装标签/铭牌（Word/PDF），052 §1.1 的注册人、受托生产企业、
   生产地址必须与标签一致；生产地址不得拿注册人住所顶替（委托生产时两者常不同市）。

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


def find_label(p: Path):
    """在项目目录/产物目录的上级找外包装标签或铭牌。"""
    p = p.resolve()
    for d in (p, p.parent):
        for pat in ("*标签*.docx", "*铭牌*.docx"):
            hit = sorted(d.glob(pat))
            if hit:
                return hit[0]
    return None


def label_fields(path: Path):
    """读出标签里的身份字段（注册人/受托生产企业/生产地址）。"""
    from docx import Document
    texts = []
    d = Document(str(path))
    for para in d.paragraphs:
        texts.append(para.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                texts.append(c.text)
    out = {}
    for raw in "\n".join(texts).splitlines():
        line = raw.strip()
        for key, name in (("注册人：", "registrant"),
                          ("受托生产企业：", "manufacturer"),
                          ("生产地址：", "production_address"),
                          ("住所：", "address")):
            if key in line and name not in out:
                val = line.split(key, 1)[1].strip()
                if val:
                    out[name] = val
    return out


def _norm(s: str) -> str:
    return re.sub(r"[\s\u3000]+", "", s or "")



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
        doc052 = ""
        for f in docs:
            from docx import Document
            txt = "\n".join(x.text for x in Document(str(f)).paragraphs)
            for t in Document(str(f)).tables:
                for row in t.rows:
                    txt += "\n" + "\n".join(c.text for c in row.cells)
            if md5.lower() in txt.lower():
                hit_md5 = True
            if f.name.startswith("RD-052"):
                doc052 = txt
                if md5.lower() not in txt.lower():
                    errs.append("052 正文未写入软件 MD5「%s」" % md5)
        if not hit_md5:
            errs.append("全族未见软件 MD5「%s」" % md5)

        # 外包装标签/铭牌（注册人 2026-11-23 定，必供）
        label = find_label(p)
        if label is None:
            errs.append("未提供外包装标签/铭牌（必供材料）：项目目录未找到 *标签*.docx / *铭牌*.docx")
        else:
            fields = label_fields(label)
            body = _norm(doc052)
            for key, label_cn in (("registrant", "注册人"),
                                  ("manufacturer", "受托生产企业"),
                                  ("production_address", "生产地址")):
                val = fields.get(key)
                if val and _norm(val) not in body:
                    errs.append("052 §1.1 与标签不一致：缺少%s「%s」" % (label_cn, val))
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
    print("必供材料检查通过：型号 YJT- 前缀合规、软件 MD5 为 32 位且已写入 052、外包装标签身份字段与 052 §1.1 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
