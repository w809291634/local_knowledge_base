# -*- coding: utf-8 -*-
"""正文连续性门禁：禁止把一句话拆成两个正文段。

背景（2026-11-24）：029 第五章/第八章从 PDF 复制来的正文被硬断行，
出现“…每一个功 / 能或性能…”“…才提 / 供。下面…”两段；docx 层合法，渲染后明显断句。

判据（只看正文段，跳过标题/目录/表格/图题/项目符号/标签行）：
当前段以汉字开头，且上一非空正文段不以句末标点（。！？；：、，,.!?;:）】》”’…]）结尾，
且两段都足够长（≥6 字），即判为断句。

用法：python check_text_continuity.py <产物目录>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_ops as ops

END_OK = tuple("。！？；：、，,.!?;:）)】》”’…]}")
START_BAD = ("●", "•", "图", "表", "注：", "注:", "第", "一、", "二、", "三、")


def is_body(p):
    t = p.text.strip()
    if not t or "\t" in p.text:
        return False
    st = (p.style.name or "").lower()
    if st.startswith(("heading", "toc", "caption")):
        return False
    if re.search(r"\.{4,}", t):
        return False
    if p._p.find(".//" + qn("w:pict")) is not None:
        return False
    if ops.has_field_code(p) or ops.has_section_break(p):
        return False
    if re.match(r"^(\d+(\.\d+)*\s|[一二三四五六七八九十]+、)", t):
        return False
    if ops.effective_outline_level(p) in (0, 1, 2):
        return False
    return True


def is_label(t):
    return len(t) < 40 and ("：" in t or ":" in t)


def check_doc(path: Path):
    errs = []
    prev = None
    for p in docx.Document(str(path)).paragraphs:
        if not is_body(p):
            if not p.text.strip():
                continue      # 空段不切断上下文
            prev = None
            continue
        t = p.text.strip()
        if len(t) < 10 or t.startswith(START_BAD):
            continue          # 短片段不覆盖“上一长段”，以便识别 A/短片段/B 的三段断句
        if prev is not None:
            pt = prev.text.strip()
            if (len(pt) >= 15 and not pt.endswith(END_OK) and "；" not in pt
                    and not ("图" in pt and len(pt) < 25)
                    and not (("、" in pt) and len(pt) < 30)
                    and not is_label(pt) and not is_label(t)
                    and re.match(r"^[\u4e00-\u9fff]", t)):
                errs.append("%s 疑似断句：「…%s」+「%s…」"
                            % (path.name, pt[-12:], t[:12]))
        prev = p
    return errs


def main(argv):
    if not argv:
        print("用法：check_text_continuity.py <产物目录>")
        return 2
    root = Path(argv[0])
    errs = []
    for f in sorted(root.glob("RD-*.docx")):
        if f.name.startswith("~$"):
            continue
        errs += check_doc(f)
    if errs:
        print("正文连续性门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("正文连续性门禁通过：未发现被拆断的正文句")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
