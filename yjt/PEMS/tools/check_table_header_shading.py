# -*- coding: utf-8 -*-
"""表格底纹门禁（注册人 2026-11-21 确认）。

规则（见 reference-document-format-and-diagram-requirements.md「分类规则 -- 表格」
的「表头底纹与数据行底纹」）：
1. 除封面信息表外的每张正文表，**首行全部单元格**必须显式灰底，默认 `D9D9D9`；
2. **数据行不得有任何 `w:shd`**（旧灰底必须清掉，不能靠继承）；
3. 表内文字黑色：run 的 `w:color` 为空、`000000` 或 `auto`；
4. 例外：封面信息表（首格为「文件编号」）、RD-029「软件异常报告表」、
   RD-030「软件开发计划」表（含「项目里程碑计划」）保持模板原样，不参与判定。

用法：
    python check_table_header_shading.py <目录或文件...> [--fill D9D9D9]
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

COVER_KEY = "文件编号"
SKIP_MARKS = ("项目里程碑计划", "软件异常报告")
OK_COLORS = ("", "000000", "auto")


def _text(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def _is_cover(doc):
    kids = list(doc.element.body.iterchildren())
    for c in kids:
        if c.tag == qn("w:tbl") and COVER_KEY in _text(c):
            return c
    return None


def check_doc(path: Path, fill: str = "D9D9D9"):
    doc = Document(str(path))
    cover = _is_cover(doc)
    errors = []
    checked = 0
    for ti, table in enumerate(doc.tables):
        el = table._tbl
        if el is cover:
            continue
        if any(m in _text(el) for m in SKIP_MARKS):
            continue
        checked += 1
        for ri, tr in enumerate(el.findall(qn("w:tr"))):
            for tc in tr.findall(qn("w:tc")):
                tcPr = tc.find(qn("w:tcPr"))
                shd = tcPr.find(qn("w:shd")) if tcPr is not None else None
                if ri == 0:
                    if shd is None:
                        errors.append("%s 表%d 表头缺底纹（应为 %s）" % (path.name, ti + 1, fill))
                        continue
                    got = (shd.get(qn("w:fill")) or "").upper()
                    if got != fill.upper():
                        errors.append("%s 表%d 表头底纹为 %s，应为 %s"
                                      % (path.name, ti + 1, got or "空", fill))
                elif shd is not None:
                    got = (shd.get(qn("w:fill")) or "").upper()
                    errors.append("%s 表%d 数据行残留底纹 %s（数据行不得有 w:shd）"
                                  % (path.name, ti + 1, got or "空"))
                for r in tc.iter(qn("w:r")):
                    rPr = r.find(qn("w:rPr"))
                    c = rPr.find(qn("w:color")) if rPr is not None else None
                    val = (c.get(qn("w:val")) or "").lower() if c is not None else ""
                    if val not in OK_COLORS:
                        errors.append("%s 表%d 文字颜色 %s（应为黑色）" % (path.name, ti + 1, val))
    # 只有封面表／例外表时无正文表可判，属合法状态（如 RD-028），不报错
    return errors


def check(paths, fill="D9D9D9"):
    errors = []
    for raw in paths:
        p = Path(raw)
        files = [p] if p.is_file() else [x for x in sorted(p.iterdir())
                                         if x.suffix.lower() == ".docx"]
        for f in files:
            errors += check_doc(f, fill)
    return errors


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    fill = "D9D9D9"
    for a in argv:
        if a.startswith("--fill="):
            fill = a.split("=", 1)[1]
    errors = check(args, fill)
    if errors:
        print("表头底纹门禁失败：")
        for e in errors[:60]:
            print("  -", e)
        if len(errors) > 60:
            print("  ... 共 %d 条" % len(errors))
        return 1
    print("表头底纹门禁通过：表头 %s 灰底 / 数据行无底纹 / 文字黑色" % fill)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
