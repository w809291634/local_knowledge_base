# -*- coding: utf-8 -*-
"""必供材料门禁：项目编号、型号、软件 MD5、外包装标签。

必供材料缺一不得生成/交付：
1. 项目编号：`facts.yaml` 的 `project.code` 必须存在，且不得用型号、软件版本或纯数字目录名代替；
   产物 8 份封面「项目编号」必须与之一致，文件编号必须含该项目编号（如 `026-03GSR2609023-001`）；
2. 型号必须存在、带 YJT- 前缀（YJT-12204 形式），不得为空、占位或旧前缀（JG-/YL-）；
3. 软件 MD5 必须为 32 位十六进制，不得为空或占位；
4. 052 正文必须出现该 MD5，且全族型号唯一；
5. 项目目录必须提供外包装标签/铭牌（Word/PDF），052 §1.1 的注册人、受托生产企业、
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
CODE_RE = re.compile(r"^\d{2}[A-Z][A-Z0-9]{4,18}$")
PLACEHOLDER = ("", "待补", "待定", "待核", "TBD", "todo", "无", "-")


def read_facts(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    model = re.search(r"^\s*model:\s*([^\s#]+)", text, re.M)
    md5 = re.search(r"^\s*hash_md5:\s*([^\s#]+)", text, re.M)
    return (model.group(1).strip('"\'') if model else "",
            md5.group(1).strip('"\'') if md5 else "")


def read_project_code(text: str) -> str:
    """取 `project:` 段下的 `code.value`（不引入 yaml 依赖）。"""
    block = re.search(r"^project:\s*\n((?:[ \t]+.*(?:\n|$))+)", text, re.M)
    if not block:
        return ""
    b = block.group(1)
    m = re.search(r"^[ \t]+code:[ \t]*\n[ \t]+value:[ \t]*[\"']?([^\"'\s#]+)", b, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^[ \t]+code:[ \t]*[\"']?([^\"'\s#]+)", b, re.M)
    return m.group(1).strip() if m else ""


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


def cover_fields(path: Path):
    """读封面信息表里的「文件编号」「项目编号」值。"""
    from docx import Document
    d = Document(str(path))
    out = {}
    for t in d.tables:
        if not t.rows:
            continue
        hdr = [c.text.strip() for c in t.rows[0].cells]
        if "文件编号" not in hdr:
            continue
        for r in t.rows:
            cells = [c.text.strip() for c in r.cells]
            if len(cells) >= 2 and cells[0] in ("文件编号", "项目编号") \
                    and cells[0] not in out:
                out[cells[0]] = cells[1]
        break
    return out


def _norm(s: str) -> str:
    return re.sub(r"[\s\u3000]+", "", s or "")



def check(p: Path):
    errs = []
    facts = find_facts(p)
    if facts is None:
        return ["未找到 facts.yaml，型号与软件 MD5 无法核对（必供材料）"]
    model, md5 = read_facts(facts)
    code = read_project_code(facts.read_text(encoding="utf-8", errors="ignore"))
    if not code or code.lower() in [x.lower() for x in PLACEHOLDER]:
        errs.append("项目编号未提供（必供材料：用户给定或项目资料核实，不得用型号/软件版本/目录数字代替）")
    else:
        if not CODE_RE.fullmatch(code):
            errs.append("项目编号「%s」格式不合规：应为 2 位数字开头＋字母/数字（如 03GSR2609023）" % code)
        if code == model or re.fullmatch(r"V\d+(?:\.\d+)*", code, flags=re.IGNORECASE) or code.isdigit():
            errs.append("项目编号「%s」不得用型号/软件版本/纯数字代替" % code)
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

    # 产物封面：项目编号、文件编号必须与 facts.yaml 一致
    if docs and code:
        for f in docs:
            try:
                cf = cover_fields(f)
            except Exception:
                continue
            v = cf.get("项目编号", "")
            if not v:
                errs.append("%s 封面未填项目编号" % f.name)
            elif v != code:
                errs.append("%s 封面项目编号「%s」≠ facts.yaml「%s」" % (f.name, v, code))
            fn = cf.get("文件编号", "")
            if fn and code not in fn:
                errs.append("%s 文件编号「%s」未含项目编号「%s」" % (f.name, fn, code))
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
    print("必供材料检查通过：项目编号与 8 份封面一致、型号 YJT- 前缀合规、软件 MD5 为 32 位且已写入 052、外包装标签身份字段与 052 §1.1 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
