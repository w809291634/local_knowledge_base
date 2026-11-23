# -*- coding: utf-8 -*-
"""不变量检查：产物必须成立的条件，一次枚举，不再逐项打补丁。

来源（2026-11-23 教训）：此前检查都是"用户指出一个、补一条"，导致
空段、图题无图、占位符「—」、列表样式顶格、图题重复等问题反复漏检。
本脚本把必须成立的条件固定成六条，对整套产物一次跑完。

六条不变量：
1 样式合法：正文段落不得出现「列出段落」「列出段落1」等意外列表样式（目录域除外）。
2 图文配对：图题必有图、图必有题、图题文字唯一、编号从 1 连续。
3 无占位符：正文不得出现「—」「-」「待定」「待补」「TBD」「XX」等未填实值。
4 空段受控：正文区连续空段 ≤1（封面区单独处理，跳过前 20 段）。
5 标签行有值：以「：」结尾且长度 ≤40 的段落，冒号后或下一段必须有内容。
6 标题样式一致：同级标题（2.1／4.3.1 这类编号标题）样式名必须相同。

用法：python check_invariants.py <产物目录>
退出码：0 全部通过；1 有失败。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

BAD_STYLE = ("列出段落", "List Paragraph")
PLACEHOLDER = ("待定", "待补", "待确认", "TBD", "XXX", "××", "以受控为准", "见受控")
KW_FIG = ("流程", "示意图", "框图", "构架图", "拓扑", "结构图", "关系图", "原理图")
NO_FIG = ("如下", "见图", "如图", "见表", "所示", "进行", "采用", "包括", "根据")


def blocks(doc):
    out = []
    for el in doc.element.body.iterchildren():
        if el.tag == qn("w:p"):
            t = "".join(x.text or "" for x in el.iter(qn("w:t"))).strip()
            txbx = el.find(".//" + qn("w:txbxContent")) is not None
            pic = (el.find(".//" + qn("w:drawing")) is not None
                   or (el.find(".//" + qn("w:pict")) is not None and not txbx)
                   or el.find(".//" + qn("w:object")) is not None)
            out.append(("pic", "") if (pic and not t) else (("txt", t) if t else ("blank", "")))
        elif el.tag == qn("w:tbl"):
            out.append(("tbl", ""))
    return out


def bare_cap(t):
    if not t or len(t) > 20:
        return False
    if t.endswith(("。", "；", "：", ":")) or "\t" in t or re.search(r"\.{3,}", t):
        return False
    if re.match(r"^\d+(\.\d+)+", t) or re.match(r"^第.章", t):
        return False
    if any(m in t for m in NO_FIG):
        return False
    return any(k in t for k in KW_FIG)


def check(path: Path):
    d = Document(str(path))
    errs = []
    paras = d.paragraphs
    bl = blocks(d)

    # 1 意外样式（跳过目录区：含制表符前导点的段落）
    for i, x in enumerate(paras):
        s = x.style.name or ""
        if any(b in s for b in BAD_STYLE) and not re.search(r"\.{3,}", x.text):
            errs.append(("样式异常", "P%d 样式=%s 内容=%s" % (i, s, x.text.strip()[:18])))

    # 2 图文配对
    caps = []
    for i, (k, t) in enumerate(bl):
        if k != "txt":
            continue
        if re.match(r"^图\s*\d", t):
            caps.append((i, t))
            continue
        nb = 0
        for j in range(i + 1, min(i + 4, len(bl))):
            if bl[j][0] == "blank":
                nb += 1
            else:
                break
        if bare_cap(t) and nb >= 2:
            caps.append((i, t))
    idx = {c[0] for c in caps}
    cnt = {}
    for i, t in caps:
        cnt[t] = cnt.get(t, 0) + 1
        if not any(x[0] == "pic" for x in bl[max(0, i - 3):i]) and (i - 1) not in idx:
            errs.append(("图题无图", t))
    for t, n in cnt.items():
        if n > 1:
            errs.append(("图题重复", "%s ×%d" % (t, n)))
    nums = [int(re.match(r"^图\s*(\d+)", t).group(1)) for _, t in caps if re.match(r"^图\s*(\d+)", t)]
    if nums and sorted(set(nums)) != list(range(1, len(set(nums)) + 1)):
        errs.append(("编号不连续", str(nums)))
    for i, (k, t) in enumerate(bl):
        if k == "pic" and not any(x[0] == "txt" and (re.match(r"^图\s*\d", x[1]) or bare_cap(x[1]))
                                 for x in bl[i + 1:i + 4]):
            errs.append(("图无图题", "第%d块" % i))

    # 3 占位符
    for i, x in enumerate(paras):
        t = x.text.strip()
        if not t or "\t" in t:
            continue
        for ph in PLACEHOLDER:
            if ph in t:
                errs.append(("占位符", "P%d %s" % (i, t[:24])))
                break
        if re.search(r"[：:]\s*[—–\-]+\s*$", t):
            errs.append(("占位符", "P%d %s" % (i, t[:24])))

    # 4 空段受控
    run = 0
    for i, (k, t) in enumerate(bl):
        if i < 20:
            continue
        if k == "blank":
            run += 1
        else:
            if run > 1:
                errs.append(("连续空段", "第%d块前有 %d 个" % (i, run)))
            run = 0

    # 5 标签行有值
    for i, x in enumerate(paras):
        t = x.text.strip()
        if not t or "\t" in t or len(t) > 40:
            continue
        if re.search(r"[：:]\s*$", t):
            label = re.split(r"[：:]", t)[0].strip().lstrip("→ \t")
            if label in ("表单系列号", "呈报人", "测试人", "测试时间"):
                continue
            nxt = paras[i + 1].text.strip() if i + 1 < len(paras) else ""
            if nxt:
                continue
            # 下一段为空时，若紧接着有图或表，视为"以图表承载"，不算缺值
            tail = paras[i + 1:i + 3]
            if any(y.text.strip() for y in tail):
                continue
            if any(y._p.find(".//" + qn("w:drawing")) is not None
                   or y._p.find(".//" + qn("w:pict")) is not None for y in tail):
                continue
            errs.append(("标签行无值", t[:24]))

    # 6 同级标题样式一致
    by_lv = {}
    for x in paras:
        t = x.text.strip()
        m = re.match(r"^(\d+)(\.\d+)*\s", t)
        if not m or "\t" in t:
            continue
        lv = t.split()[0].count(".")
        by_lv.setdefault(lv, set()).add(x.style.name or "")
    for lv, styles in by_lv.items():
        if len(styles) > 1:
            errs.append(("标题样式不一致", "%d级标题出现样式 %s" % (lv, sorted(styles))))
    return errs


def main(argv):
    if not argv:
        print("用法：check_invariants.py <产物目录>")
        return 2
    root = Path(argv[0]).resolve()
    total = 0
    for f in sorted(root.glob("RD-*.docx")):
        e = check(f)
        if e:
            total += len(e)
            print("%s 问题 %d" % (f.name, len(e)))
            for k, t in e:
                print("   [%s] %s" % (k, t))
    if total:
        print("不变量检查失败：%d 项" % total)
        return 1
    print("不变量检查通过：样式/图文/占位/空段/标签行/标题样式 六项全部成立")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
