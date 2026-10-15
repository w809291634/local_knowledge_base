# -*- coding: utf-8 -*-
"""
docx_ops —— Word 文档「模板就地替换」通用原语库
================================================
本模块只提供**可复用的原子操作**，不含任何项目数据。
项目差异全部通过参数 / 配置传入，从而保证「相同代码只写一份」。

依赖：python-docx
"""
import copy
import difflib
import hashlib
import re
import os
import struct

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.text.run import Run


# --------------------------------------------------------------------------
# 只读工具
# --------------------------------------------------------------------------
def paragraph_text(p):
    """取段落纯文本（含所有 run，忽略图内文字）"""
    return ''.join(t.text or '' for t in p._p.iter(qn('w:t')))


def has_field_code(p):
    """段落是否含域代码（目录 PAGEREF 等）；此类段落不可做 run 合并"""
    return bool(p._p.findall('.//' + qn('w:fldChar')) or
                p._p.findall('.//' + qn('w:instrText')))


def has_graphic(p):
    """段落是否含图形（DrawingML 或 VML）"""
    for tag in ('w:drawing', 'w:pict'):
        if p._p.findall('.//' + qn(tag)):
            return True
    return False


def has_section_break(p):
    """段落是否携带分节符（pPr/sectPr）"""
    pPr = p._p.find(qn('w:pPr'))
    return pPr is not None and pPr.find(qn('w:sectPr')) is not None


def find_cover_table(body, first_cell_text='文件编号'):
    """按「首行首格文本」定位封面信息表（浮动表）"""
    for tbl in body.findall(qn('w:tbl')):
        trs = tbl.findall(qn('w:tr'))
        if not trs:
            continue
        tcs = trs[0].findall(qn('w:tc'))
        if not tcs:
            continue
        cell0 = ''.join(t.text or '' for t in tcs[0].iter(qn('w:t'))).strip()
        if cell0 == first_cell_text:
            return tbl
    return None


def describe_blocks(doc):
    """打印块序列（段落/表格 + 编号/分节/图形标记），用于动手前摸清模板"""
    out = []
    for i, el in enumerate(doc.element.body, 1):
        if el.tag == qn('w:p'):
            pPr = el.find(qn('w:pPr'))
            flag = ''
            if pPr is not None:
                if pPr.find(qn('w:numPr')) is not None:
                    flag += 'NUM'
                if pPr.find(qn('w:sectPr')) is not None:
                    flag += 'SECT'
            if el.findall('.//' + qn('w:drawing')) or el.findall('.//' + qn('w:pict')):
                flag += 'IMG'
            txt = ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip()
            out.append('%3d P %-10s %s' % (i, flag, txt[:70]))
        elif el.tag == qn('w:tbl'):
            out.append('%3d TBL rows=%d' % (i, len(el.findall(qn('w:tr')))))
    return '\n'.join(out)


# --------------------------------------------------------------------------
# 段落替换
# --------------------------------------------------------------------------
def set_paragraph(p, text, label=None):
    """
    替换整段文字，保留原格式。
    - label=None ：整段替换为 text（沿用首个 run 的 rPr）。
    - label 非空：首个 run 写 label（保留其加粗等格式），正文写入第二个 run
                  （用于「加粗标签：正文」同段的模板）。
    """
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    if label is None:
        runs[0].text = text
        for r in runs[1:]:
            r.text = ''
        return
    runs[0].text = label
    if len(runs) >= 2:
        runs[1].text = text
        for r in runs[2:]:
            r.text = ''
    else:
        new_r = copy.deepcopy(runs[0]._r)
        p._p.append(new_r)
        Run(new_r, p).text = text


def apply_substitutions(p, subs):
    """
    段内全局词替换。subs 为 [(旧, 新), ...]，**长串应排在前面**。
    - 含域代码的段落跳过 run 合并，避免破坏目录。
    - 先按 run 替换；若整段仍残留关键词，再合并 run 后替换。
    """
    if not paragraph_text(p).strip():
        return
    for old, new in subs:
        if old and old in paragraph_text(p):
            for r in p.runs:
                if r.text:
                    r.text = r.text.replace(old, new)
    if has_field_code(p):
        return
    before = paragraph_text(p)
    after = before
    for old, new in subs:
        if old:
            after = after.replace(old, new)
    if after != before and p.runs:
        p.runs[0].text = after
        for r in p.runs[1:]:
            r.text = ''


def insert_paragraphs_after(p, texts, drop_numbering=True):
    """
    在段落 p 之后依次插入新段落；新段深拷贝自 p，
    - drop_numbering=True 时去掉自动编号（numPr），避免正文继承标题编号；
    - 沿用 p 末个 run 的 rPr，保持字号字体。
    """
    prev = p._p
    for txt in texts:
        new_p = copy.deepcopy(p._p)
        pPr = new_p.find(qn('w:pPr'))
        if pPr is not None and drop_numbering:
            numPr = pPr.find(qn('w:numPr'))
            if numPr is not None:
                pPr.remove(numPr)
        runs = new_p.findall(qn('w:r'))
        rPr = None
        if runs:
            last = runs[-1].find(qn('w:rPr'))
            if last is not None:
                rPr = copy.deepcopy(last)
        for r in runs:
            new_p.remove(r)
        for tag in (qn('w:bookmarkStart'), qn('w:bookmarkEnd')):
            for e in new_p.findall(tag):
                new_p.remove(e)
        r = OxmlElement('w:r')
        if rPr is not None:
            r.append(rPr)
        t = OxmlElement('w:t')
        t.set(qn('xml:space'), 'preserve')
        t.text = txt
        r.append(t)
        new_p.append(r)
        prev.addnext(new_p)
        prev = new_p


# --------------------------------------------------------------------------
# 表格填充
# --------------------------------------------------------------------------
def set_cell_text(cell, text):
    """写单元格：只保留一个段落、一个 run，避免残留旧内容"""
    ps = cell.paragraphs
    for extra in ps[1:]:
        extra._p.getparent().remove(extra._p)
    p = ps[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ''
    else:
        p.add_run(text)


def fill_table(doc, idx, header_rows, rows, header_texts=None, row0_texts=None):
    """
    填充第 idx 个表格（0 为封面表，通常不改）：
    - 保留前 header_rows 行表头，其余为数据行；
    - 数据行多于现存 → 深拷贝末行补足；少于 → 删除多余行；
    - header_texts / row0_texts 可选覆盖表头与首行文字。
    """
    t = doc.tables[idx]
    if row0_texts:
        for j, txt in enumerate(row0_texts):
            if j < len(t.rows[0].cells):
                set_cell_text(t.rows[0].cells[j], txt)
    if header_texts:
        hr = t.rows[header_rows - 1]
        for j, txt in enumerate(header_texts):
            if j < len(hr.cells):
                set_cell_text(hr.cells[j], txt)
    have = len(t.rows) - header_rows
    while have < len(rows):
        t._tbl.append(copy.deepcopy(t.rows[-1]._tr))
        have += 1
    while have > len(rows):
        t._tbl.remove(t.rows[-1]._tr)
        have -= 1
    for i, row in enumerate(rows):
        tr = t.rows[header_rows + i]
        for j, val in enumerate(row):
            if j < len(tr.cells):
                set_cell_text(tr.cells[j], str(val))


def clone_table_props(src_table, dst_table, drop_float=True):
    """把模板表的 tblPr 复制给新表（保留边框/单元格边距），可选去掉浮动定位"""
    tp = src_table._tbl.find(qn('w:tblPr'))
    if tp is None:
        return
    new_pr = copy.deepcopy(tp)
    if drop_float:
        f = new_pr.find(qn('w:tblpPr'))
        if f is not None:
            new_pr.remove(f)
    old = dst_table._tbl.find(qn('w:tblPr'))
    if old is not None:
        dst_table._tbl.replace(old, new_pr)
    else:
        dst_table._tbl.insert(0, new_pr)


# --------------------------------------------------------------------------
# 封面 / 分页
# --------------------------------------------------------------------------
def trim_cover_spacers(doc, first_cell_text='文件编号'):
    """删除封面表与首个正文块之间的纯空段；返回删除数"""
    body = doc.element.body
    cover = find_cover_table(body, first_cell_text)
    if cover is None:
        return 0
    started, removed = False, 0
    for el in list(body):
        if el is cover:
            started = True
            continue
        if not started:
            continue
        if el.tag == qn('w:p'):
            if has_section_break_el(el):
                break
            if ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip():
                break
            if el.findall('.//' + qn('w:br')) or el.findall('.//' + qn('w:drawing')):
                break
            body.remove(el)
            removed += 1
        elif el.tag == qn('w:tbl'):
            break
        else:
            continue          # ★ bookmark* 等：跳过而非 break
    return removed


def has_section_break_el(p_el):
    pPr = p_el.find(qn('w:pPr'))
    return pPr is not None and pPr.find(qn('w:sectPr')) is not None


def ensure_cover_page_break(doc, first_cell_text='文件编号'):
    """
    封面表后若无分节符/分页符，则紧随其后插入分页符，保证封面独立成页。
    返回是否插入。
    """
    body = doc.element.body
    cover = find_cover_table(body, first_cell_text)
    if cover is None:
        return False
    started = False
    for el in body:
        if el is cover:
            started = True
            continue
        if not started:
            continue
        if el.tag == qn('w:p'):
            if has_section_break_el(el):
                return False
            if el.findall('.//' + qn('w:br')):
                return False
            if ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip():
                break
        elif el.tag == qn('w:tbl'):
            break
    br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    r = OxmlElement('w:r')
    r.append(br)
    p = OxmlElement('w:p')
    p.append(r)
    cover.addnext(p)
    return True


def clean_body_keeping_section_breaks(doc, from_cover=True,
                                      first_cell_text='文件编号'):
    """
    清空封面之后的正文块，但**保留一个含分节符的段落**与文末 sectPr，
    以免页眉页脚及分节结构丢失（仅在「重建正文」方案下使用）。
    """
    body = doc.element.body
    cover = find_cover_table(body, first_cell_text) if from_cover else None
    started = cover is None
    kept_break = False
    for el in list(body):
        if el is cover:
            started = True
            continue
        if not started:
            continue
        if el.tag == qn('w:sectPr'):
            continue
        if el.tag == qn('w:p') and has_section_break_el(el):
            if not kept_break:
                for child in list(el):
                    if child.tag != qn('w:pPr'):
                        el.remove(child)
                kept_break = True
                continue
        body.remove(el)


def insert_page_break(paragraph_el):
    """在指定段落元素之后插入一个分页符段落"""
    br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    r = OxmlElement('w:r')
    r.append(br)
    p = OxmlElement('w:p')
    p.append(r)
    paragraph_el.addnext(p)


def trim_trailing_empty_paragraphs(doc, keep=1):
    """删除文末（最后一个块/sectPr 之前）的纯空段，避免渲染出末尾空白页。

    模板常在正文结束后遗留若干空段（元良 RD-026 末尾 4 个 → 第 5 页只有页眉）。
    keep=1 表示至少保留一个空段，维持段落标记。返回删除数。
    """
    body = doc.element.body
    # 文末 sectPr 之前的块序列
    blocks = [el for el in body if el.tag != qn('w:sectPr')]
    tail = []
    for el in reversed(blocks):
        if el.tag == qn('w:p') and not ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip() \
                and not el.findall('.//' + qn('w:br')) \
                and not el.findall('.//' + qn('w:drawing')) \
                and not el.findall('.//' + qn('w:pict')) \
                and not has_section_break_el(el):
            tail.append(el)
        else:
            break
    removed = 0
    for el in tail:
        if removed >= max(0, len(tail) - keep):
            break
        body.remove(el)
        removed += 1
    return removed


# --------------------------------------------------------------------------
# 图片：图题驱动的插图替换与校验
# 用法：specs = [(png, '图 1  xxx', anchor_heading, width_in), ...]
#      n = replace_figures(doc, specs)     # 删旧图 + 依序插入
#      drop_orphan_image_rels(doc)         # 清掉包内旧图残留（瘦身）
#      ok, rows = verify_figures(doc, [s[0] for s in specs])
# --------------------------------------------------------------------------
# 图片引用只有两种形态：DrawingML(a:blip@r:embed) 与 VML(v:imagedata@r:id)。
# 模板文档两者常混用（见 pitfalls.md「图片两种形式都要认」）——
# 只认 DrawingML 会漏图，甚至把仍被 VML 引用的图当成孤立件删掉。
# 注意：python-docx 的 nsmap 没有 v 前缀，VML 必须用 Clark 记法（{命名空间}标签）。
VML_NS = 'urn:schemas-microsoft-com:vml'
IMAGE_REF_TAGS = (
    (qn('a:blip'), qn('r:embed')),
    ('{%s}imagedata' % VML_NS, qn('r:id')),
)
TXBX = qn('w:txbxContent')          # 文本框内容容器（字体统一要跳过）
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff', '.emf', '.wmf')


def image_rids(p):
    """段落里全部图片引用的 rId（DrawingML + VML 都认）；文本框内的也算"""
    rids = []
    for tag, attr in IMAGE_REF_TAGS:
        for el in p._p.findall('.//' + tag):
            rid = el.get(attr)
            if rid:
                rids.append(rid)
    return rids


def has_inline_image(p):
    """段落是否含图片（DrawingML 或 VML）"""
    return bool(image_rids(p))


def iter_image_paragraphs(doc):
    """按文档顺序返回含图片的段落（两种图片形式都算）"""
    return [p for p in doc.paragraphs if has_inline_image(p)]


def paragraph_image_sha256(doc, p):
    """取段落内嵌图片的 sha256（图替换后的二进制校验用）"""
    rid = image_rids(p)[0]
    return hashlib.sha256(doc.part.related_parts[rid].blob).hexdigest()


def find_body_heading(doc, text):
    """按前缀在**正文**定位标题段落；跳过目录（toc 样式）段落。

    必须跳过目录：目录条目与正文标题同文本，简单前缀匹配会插错位置。
    """
    for p in doc.paragraphs:
        style = p.style.name if p.style else ''
        if style.lower().startswith('toc'):
            continue
        if paragraph_text(p).strip().startswith(text):
            return p
    return None


def clear_figures(doc, caption_prefix='图 '):
    """删除所有内联图片段落 + 紧随其后的居中图题段落，返回删除条数"""
    doomed = []
    for p in doc.paragraphs:
        if has_inline_image(p):
            doomed.append(p)
        elif paragraph_text(p).strip().startswith(caption_prefix) \
                and p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            doomed.append(p)
    for p in doomed:
        p._p.getparent().remove(p._p)
    return len(doomed)


def insert_figure_before(doc, anchor_para, img_path, caption, width_in,
                         caption_size_pt=10.5, caption_bold=True):
    """在 anchor 段落前插入「居中图片 + 居中图题」两个段落。

    doc.add_picture 只能追加到文末，这里靠 addprevious 把它挪到锚点前。
    """
    doc.add_picture(img_path, width=Inches(width_in))
    pic = doc.paragraphs[-1]
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    anchor_para._p.addprevious(pic._p)

    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in cap.runs:
        r.font.size = Pt(caption_size_pt)
        r.bold = caption_bold
    anchor_para._p.addprevious(cap._p)


def replace_figures(doc, specs, caption_size_pt=10.5):
    """重建全部插图：先清旧图，再按 specs 依序插到各锚点前。

    specs: [(png_path, caption, anchor_heading_text, width_in), ...]
    同一锚点会被插入多张时，按 specs 顺序依次排好。
    """
    clear_figures(doc)
    anchors = {}
    for _, _, anchor, _ in specs:
        if anchor not in anchors:
            t = find_body_heading(doc, anchor)
            if t is None:
                raise KeyError('未在正文找到锚点标题: %s' % anchor)
            anchors[anchor] = t
    for png, caption, anchor, width_in in specs:
        insert_figure_before(doc, anchors[anchor], png, caption, width_in, caption_size_pt)
    return len(specs)


def drop_orphan_image_rels(doc):
    """删除未被引用的图片关系（瘦身）。

    删段落不会连带删包内图片部件，残留旧图会让文件虚胖（曾 1.5MB→2.4MB）。
    python-docx 保存时只写出「可达」部件，所以断开关系即可，无需改 zip。

    ★ 判定「已引用」必须同时认 DrawingML 与 VML：只认 a:blip 会把 VML
      (v:imagedata) 正在用的图当成孤立件删掉，保存后图片丢失、引用悬空。
    """
    used = set()
    for p in doc.paragraphs:
        for rid in image_rids(p):
            rel = doc.part.rels.get(rid)
            if rel is not None:
                used.add(os.path.basename(rel.target_ref or ''))
    dropped = []
    for rid, rel in list(doc.part.rels.items()):
        base = os.path.basename(rel.target_ref or '')
        if base.startswith('image') and base.lower().endswith(IMAGE_EXTS) and base not in used:
            doc.part.drop_rel(rid)
            dropped.append(base)
    return dropped


def png_size(path):
    """读 PNG 头取 (宽, 高) 像素"""
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


def verify_figures(doc, expected_pngs):
    """校验图组：数量/顺序 + 二进制哈希 + 显示宽高比（防拉伸）。

    返回 (ok, rows)，rows 每项为 dict(png, sha_ok, ratio_ok, disp_w, disp_h, ratio)。
    """
    rows = []
    ok = True
    for p, png in zip(iter_image_paragraphs(doc), expected_pngs):
        blob = doc.part.related_parts[image_rids(p)[0]].blob
        sha_ok = hashlib.sha256(blob).hexdigest() == \
            hashlib.sha256(open(png, 'rb').read()).hexdigest()
        # VML 图没有 wp:inline/extent，无法核显示比例，只核二进制（避免误报崩溃）
        inl = p._p.findall('.//' + qn('wp:inline'))
        ext = inl[0].find(qn('wp:extent')) if inl else None
        if ext is None:
            ok = ok and sha_ok
            rows.append(dict(png=os.path.basename(png), sha_ok=sha_ok, ratio_ok=True,
                             disp_w=None, disp_h=None, ratio=None))
            continue
        cx, cy = int(ext.get('cx')), int(ext.get('cy'))
        pw, ph = png_size(png)
        ratio = cx / cy
        ratio_ok = abs(pw / ph - ratio) < 0.01          # 容差 1%
        ok = ok and sha_ok and ratio_ok
        rows.append(dict(png=os.path.basename(png), sha_ok=sha_ok, ratio_ok=ratio_ok,
                         disp_w=cx / 914400.0, disp_h=cy / 914400.0, ratio=ratio))
    if len(rows) != len(expected_pngs):
        ok = False
    return ok, rows


def assert_writable(path):
    """确认文件未被 Word/WPS 独占锁定；被占用时抛 IOError。

    python-docx 保存到被打开的 .docx 会报 PermissionError，且此时改动已丢，
    所以动笔前先探一次。
    """
    try:
        with open(path, 'rb+'):
            pass
    except OSError as e:
        raise IOError('目标文档被其它进程占用，请先关闭：%s' % path) from e


# --------------------------------------------------------------------------
# 段落缩进规范化 / 旧式图形清理
#   模板中常见「畸形首行缩进」：firstLine 远大于 2 字符（如 2040/3420 twip），
#   并常与负的 leftChars 同时出现 → 渲染成「首行缩进一大截、折行回到左边界」。
#   该缺陷在 06 项目模板、血糖仪 058/062、元良三个项目上均复现，故独立成原语。
#   注意：**不要把正文文字写进畸形段落**；应留空该段落，文字写入新建的正常段落。
# --------------------------------------------------------------------------
def normalize_paragraph_indent(doc, max_first_line=1440, first_line_chars=200,
                               first_line=480, drop_zero=False):
    """把畸形首行缩进规范化。返回 (修改数, 清理空段数)。

    - 段落有文字：仅替换 w:ind 为 (firstLineChars, firstLine)，保留其余格式；
    - 段落为空  ：drop_zero=True 时直接删除该空段，否则同样规范化。
    """
    from docx.oxml import OxmlElement
    fixed = dropped = 0
    for p in list(doc.paragraphs):
        pPr = p._p.find(qn('w:pPr'))
        if pPr is None:
            continue
        ind = pPr.find(qn('w:ind'))
        if ind is None:
            continue
        fl = ind.get(qn('w:firstLine'))
        lc = ind.get(qn('w:leftChars'))
        bad = (fl and abs(int(fl)) > max_first_line) or (lc and int(lc) < 0)
        if not bad:
            continue
        empty = not ''.join(t.text or '' for t in p._p.iter(qn('w:t'))).strip()
        if empty and drop_zero:
            p._p.getparent().remove(p._p)
            dropped += 1
            continue
        pPr.remove(ind)
        new = OxmlElement('w:ind')
        new.set(qn('w:firstLineChars'), str(first_line_chars))
        new.set(qn('w:firstLine'), str(first_line))
        # 按 schema，w:ind 须排在 w:rPr 之前
        rPr = pPr.find(qn('w:rPr'))
        if rPr is not None:
            rPr.addprevious(new)
        else:
            pPr.append(new)
        fixed += 1
    return fixed, dropped


def clear_legacy_shapes(doc, caption_prefixes=('图', '表'), drop_empty=True):
    """删除旧式 VML 图形段落（w:pict）及其紧随的图题段落。

    模板里继承的图常是 VML（不是 a:blip），`clear_figures` 抓不到；图题
    也可能是「图1 xxx」（无空格），不匹配 `图 ` 前缀。故本函数：
      1) 删掉所有含 w:pict 的段落；
      2) 删掉文本以 caption_prefixes 开头、且紧跟其后的图题段落。
    返回删除段数。
    """
    targets = []
    for i, p in enumerate(doc.paragraphs):
        if p._p.findall('.//' + qn('w:pict')):
            targets.append(p)
            continue
        t = paragraph_text(p).strip()
        if t and any(t.startswith(x) for x in caption_prefixes) and len(t) <= 40:
            prev = doc.paragraphs[i - 1] if i > 0 else None
            if prev is not None and (prev._p.findall('.//' + qn('w:pict'))
                                    or has_inline_image(prev)):
                targets.append(p)
    for p in targets:
        p._p.getparent().remove(p._p)
    return len(targets)


# --------------------------------------------------------------------------
# 文档级读写
# --------------------------------------------------------------------------
def open_template(path):
    return Document(path)


def save_doc(doc, out_dir, filename):
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, filename)
    doc.save(out)
    return out


def extract_text(path):
    """抽取正文 + 表格文本（用于一致性检查）；.doc 请先转换"""
    d = Document(path)
    lines = [p.text for p in d.paragraphs if p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip():
                    lines.append(c.text)
    return '\n'.join(lines)


def convert_doc_to_docx(src, dst, prefer=('Word.Application', 'KWPS.Application')):
    """用 Word/WPS COM 把 .doc 转为 .docx；两者都失败则抛异常"""
    import win32com.client as w
    last = None
    for prog in prefer:
        try:
            app = w.Dispatch(prog)
            app.Visible = False
            app.DisplayAlerts = 0
            d = app.Documents.Open(src, ReadOnly=True)
            d.SaveAs2(dst, FileFormat=16)
            d.Close(False)
            app.Quit()
            return dst
        except Exception as e:      # noqa: BLE001
            last = e
            continue
    raise RuntimeError('无法转换 .doc：%s' % last)


# ─────────────────────────────────────────────────────────────────────────────
# 域（Field）/ 目录（TOC）修复与分页一致性（详见 docx-fields-and-toc-repair.md、
# cover-pagination-and-sections.md 第 5/6 节）。四个函数互相独立，可单独调用。
# ─────────────────────────────────────────────────────────────────────────────

def toc_diagnose(doc):
    """诊断目录域健康度。
    返回 keys：
      balance        —— begin-end 差值，>0 表示域未闭合（如 RD-068 缺 end）
      toc_instr      —— 是否找到 TOC 指令（instrText）
      toc_has_begin  —— TOC 指令前是否有未被闭合的 begin（False → 指令裸露，如 RD-026）
      toc_has_separate —— TOC 指令后是否有 separate（False → 结果区未开始，指令会裸露）
      text_has_toc   —— 指令是否被误写成 <w:t> 普通文本
      toc_paras      —— 目录样式段落索引
      entry_has_field—— 目录条目是否含域（False → 纯文本目录，无超链接，如 RD-032）
    """
    from collections import Counter
    body = doc.element.body
    seq = []
    for el in body.iter():
        if el.tag == qn('w:fldChar'):
            seq.append(('fld', el.get(qn('w:fldCharType'))))
        elif el.tag == qn('w:instrText'):
            seq.append(('instr', el.text or ''))
        elif el.tag == qn('w:t'):
            seq.append(('t', el.text or ''))
    c = Counter(v for k, v in seq if k == 'fld')
    pos = [i for i, (k, v) in enumerate(seq) if k == 'instr' and 'TOC' in v]
    toc_instr = bool(pos)
    has_begin = has_sep = False
    if pos:
        i = pos[0]
        depth = 0
        for j in range(i - 1, -1, -1):          # 向前找未被闭合的 begin
            k, v = seq[j]
            if k == 'fld' and v == 'end':
                depth += 1
            elif k == 'fld' and v == 'begin':
                if depth == 0:
                    has_begin = True
                    break
                depth -= 1
        for j in range(i + 1, len(seq)):        # 向后找 separate（到首个 end 为止）
            k, v = seq[j]
            if k == 'fld' and v == 'separate':
                has_sep = True
                break
            if k == 'fld' and v == 'end':
                break
    tocs = [i for i, p in enumerate(doc.paragraphs)
            if (p.style.name or '').lower().startswith('toc')]
    return {
        'begin': c.get('begin', 0), 'separate': c.get('separate', 0), 'end': c.get('end', 0),
        'balance': c.get('begin', 0) - c.get('end', 0),
        'toc_instr': toc_instr,
        'toc_has_begin': has_begin,             # False → 指令裸露
        'toc_has_separate': has_sep,            # False → 结果区未开始
        'text_has_toc': any('TOC' in v for k, v in seq if k == 't'),
        'toc_paras': tocs,
        'entry_has_field': any(doc.paragraphs[i]._p.findall('.//' + qn('w:fldChar')) for i in tocs),
        'applicable': bool(pos) or bool(tocs),        # 本文档是否有目录（无目录 → healthy 为 None）
        'healthy': (None if not (pos or tocs) else
                    bool(pos and has_begin and has_sep and c.get('begin', 0) == c.get('end', 0))),
    }


def _fld_run(fld_type):
    r = OxmlElement('w:r')
    fc = OxmlElement('w:fldChar')
    fc.set(qn('w:fldCharType'), fld_type)
    r.append(fc)
    return r


def close_toc_field(doc):
    """外层 TOC 域缺 end 时，在目录末条目段落末尾补足；返回补的个数"""
    need = toc_diagnose(doc)['balance']
    if need <= 0:
        return 0
    tocs = toc_diagnose(doc)['toc_paras']
    if not tocs:
        return 0
    last = doc.paragraphs[max(tocs)]
    for _ in range(need):
        last._p.append(_fld_run('end'))
    return need


def fix_stray_toc_instruction(doc):
    """把误写成普通文本（w:t）的 TOC 指令转成真正的域：begin + instrText + separate"""
    for p in doc.paragraphs:
        for r in p._p.findall(qn('w:r')):
            t = r.find(qn('w:t'))
            if t is None or 'TOC' not in (t.text or ''):
                continue
            instr = t.text
            it = OxmlElement('w:instrText')
            it.set(qn('xml:space'), 'preserve')
            it.text = instr
            r.addprevious(_fld_run('begin'))
            r.addprevious(it)
            r.addprevious(_fld_run('separate'))
            t.text = ''          # 指令不再作为可见文本
            return instr
    return None


def normalize_toc_page_break(doc, pad_min=5):
    """目录末条目→正文首标题之间的垫片空段，改为 1 个显式分页符。返回(删除段数, 是否插入)"""
    ps = doc.paragraphs
    tocs = [i for i, p in enumerate(ps) if (p.style.name or '').lower().startswith('toc')]
    if not tocs:
        return 0, False
    last = max(tocs)
    first_body = None
    for i, p in enumerate(ps):
        if i <= last:
            continue
        pPr = p._p.find(qn('w:pPr'))
        if pPr is not None and pPr.find(qn('w:numPr')) is not None and paragraph_text(p).strip():
            first_body = i
            break
    if first_body is None:
        return 0, False
    empt = [p for p in ps[last + 1:first_body]
            if not paragraph_text(p).strip()
            and not p._p.findall('.//' + qn('w:br'))
            and not p._p.findall('.//' + qn('w:drawing'))
            and not p._p.findall('.//' + qn('w:pict'))
            and not p._p.findall('.//' + qn('w:fldChar'))        # ★ 只含域标记的段不能当空段删
            and not p._p.findall('.//' + qn('w:instrText'))]
    if len(empt) < pad_min:
        return 0, False
    keep = empt[0]
    for r in keep._p.findall(qn('w:r')):
        keep._p.remove(r)
    r = OxmlElement('w:r')
    br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    r.append(br)
    keep._p.append(r)
    n = 0
    for p in empt[1:]:
        p._p.getparent().remove(p._p)
        n += 1
    return n, True


def page_size_report(doc):
    """逐节报告页面尺寸/页边距，用于发现"某节被设成横向"导致的页宽不一致"""
    out = []
    for i, s in enumerate(doc.sections):
        e = s._sectPr
        sz = e.find(qn('w:pgSz'))
        mar = e.find(qn('w:pgMar'))
        out.append({
            'section': i + 1,
            'w': sz.get(qn('w:w')) if sz is not None else None,
            'h': sz.get(qn('w:h')) if sz is not None else None,
            'orient': sz.get(qn('w:orient')) if sz is not None else None,
            'margins': tuple(mar.get(qn('w:' + k)) if mar is not None else None
                             for k in ('left', 'right', 'top', 'bottom')),
        })
    return out


def unify_sections(doc, base=0):
    """把各节的 pgSz/pgMar 统一为第 base 节（默认封面节）的值；返回修改记录"""
    b = doc.sections[base]._sectPr
    b_sz, b_mar = b.find(qn('w:pgSz')), b.find(qn('w:pgMar'))
    fixed = []
    for i, s in enumerate(doc.sections):
        if i == base:
            continue
        e = s._sectPr
        sz = e.find(qn('w:pgSz'))
        if sz is None:
            sz = OxmlElement('w:pgSz')
            e.insert(0, sz)
        for k in ('w', 'h', 'orient'):
            bv = b_sz.get(qn('w:' + k)) if b_sz is not None else None
            if bv is None:
                if sz.get(qn('w:' + k)) is not None:
                    del sz.attrib[qn('w:' + k)]
            elif sz.get(qn('w:' + k)) != bv:
                sz.set(qn('w:' + k), bv)
                fixed.append('节%d pgSz.%s→%s' % (i + 1, k, bv))
        mar = e.find(qn('w:pgMar'))
        if mar is not None and b_mar is not None:
            for k in ('left', 'right', 'top', 'bottom'):
                bv = b_mar.get(qn('w:' + k))
                if bv is not None and mar.get(qn('w:' + k)) != bv:
                    mar.set(qn('w:' + k), bv)
                    fixed.append('节%d pgMar.%s→%s' % (i + 1, k, bv))
    return fixed


def clamp_images_to_text_width(doc, max_emu=None):
    """把所有内嵌图缩放到不超过正文宽度（保持纵横比）；返回缩放张数"""
    sec = doc.sections[0]
    if max_emu is None:
        max_emu = sec.page_width - sec.left_margin - sec.right_margin
    n = 0
    for sh in doc.inline_shapes:
        w, h = sh.width, sh.height
        if w and w > max_emu:
            ratio = max_emu / w
            sh.width = Emu(int(max_emu))
            sh.height = Emu(int(h * ratio))
            n += 1
    return n


def refresh_toc_via_word(path, save=True):
    """用 Word 更新目录域/字段（等价于在 Word 里 F9 /『更新目录』）。
    只能在装有 Word/WPS 的环境执行；不刷新则目录页码停留在旧值。"""
    import win32com.client as w
    app = w.Dispatch('Word.Application')
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        d = app.Documents.Open(path)
        for i in range(1, d.TablesOfContents.Count + 1):
            d.TablesOfContents(i).Update()
        d.Fields.Update()
        if save:
            d.Save()
        d.Close(False)
    finally:
        app.Quit()


def export_pdf_via_word(path, pdf_path):
    """LibreOffice 卡死时的兜底：用 Word 只读导出 PDF（得到的即 Word 自身分页）"""
    import win32com.client as w
    app = w.Dispatch('Word.Application')
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        d = app.Documents.Open(path, ReadOnly=True)
        pages = d.ComputeStatistics(2)          # 2 = wdStatisticPages
        d.ExportAsFixedFormat(pdf_path, 17)     # 17 = PDF
        d.Close(False)
        return pages
    finally:
        app.Quit()

# --------------------------------------------------------------------------
# 字体与字号统一（文档族级版式收口；详见 font-and-style-normalization.md）
#   三条实测必要性：
#     ① 必须删掉 rFonts 的 *Theme 属性，否则主题字体优先级高于显式 rFonts，改了不生效；
#     ② 必须单独遍历表格——doc.paragraphs **不含表格内段落**，漏了表格等于没统一；
#     ③ 必须同时改 styles.xml 的 Normal/Heading/Caption，否则用户在 Word 里新打字又回旧字体。
# --------------------------------------------------------------------------
THEME_FONT_ATTRS = ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'ctheme', 'cstheme')


def apply_rpr_font(rPr, east_asia=None, latin=None, sz=None):
    """在给定 `w:rPr` 上**就地**写字体槽与字号。

    ★ 不要为了复用 run 级函数而把 rPr `append` 到临时 `w:r` 上：lxml 的 append 是
      **移动**语义，会把 rPr 从样式元素里搬走，结果 Heading 的字号定义整段丢失，
      而且不报错、只在渲染时表现为"章标题变成正文大小"。
    """
    if east_asia or latin:
        rf = rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts')
            rPr.insert(0, rf)
        if latin:
            for at in ('ascii', 'hAnsi', 'cs'):
                rf.set(qn('w:' + at), latin)
        if east_asia:
            rf.set(qn('w:eastAsia'), east_asia)
        for at in THEME_FONT_ATTRS:
            if rf.get(qn('w:' + at)):
                del rf.attrib[qn('w:' + at)]
    if sz:
        for tag in ('w:sz', 'w:szCs'):
            el = rPr.find(qn(tag))
            if el is None:
                el = OxmlElement(tag)
                rPr.append(el)
            el.set(qn('w:val'), str(sz))
    return rPr


def style_font(doc, name, east_asia=None, latin=None, sz=None):
    """改样式默认值（Normal / Heading 1~4 / Caption / Body Text）。样式名不存在时返回 False。"""
    try:
        el = doc.styles[name]._element
    except KeyError:
        return False
    rPr = el.find(qn('w:rPr'))
    if rPr is None:
        rPr = OxmlElement('w:rPr')
        el.append(rPr)
    apply_rpr_font(rPr, east_asia, latin, sz)
    return True


def _in_textbox(el):
    anc = el.getparent()
    while anc is not None:
        if anc.tag == TXBX:
            return True
        anc = anc.getparent()
    return False


def iter_zone_paragraphs(doc, cover_first_cell='文件编号'):
    """按版式分区产出 (paragraph, zone)：
    cover / head / caption / table / body / hf（页眉页脚）。

    分区是字号统一的前提——标题、封面、页眉**只该改字体不该改字号**，
    否则章标题会和正文一样大、封面版式塌陷。
    """
    sect_i = next((i for i, p in enumerate(doc.paragraphs) if has_section_break(p)), 0)
    cover = find_cover_table(doc.element.body, cover_first_cell)
    for i, p in enumerate(doc.paragraphs):
        pPr = p._p.find(qn('w:pPr'))
        style = (p.style.name or '').lower()
        t = ''.join(x.text or '' for x in p._p.iter(qn('w:t')))
        t = re.sub(r'\s+', '', t or '')
        if i < sect_i:
            zone = 'cover'
        elif style.startswith('heading') or style.startswith('toc')                 or style.startswith('caption')                 or (pPr is not None and pPr.find(qn('w:numPr')) is not None):
            zone = 'head'
        elif t[:1] in ('图', '表') and len(t) <= 40:
            zone = 'caption'
        else:
            zone = 'body'
        yield p, zone
    for tb in doc.tables:
        z = 'cover' if tb._tbl is cover else 'table'
        for row in tb.rows:
            seen = set()
            for c in row.cells:
                if c._tc in seen:
                    continue
                seen.add(c._tc)
                for p in c.paragraphs:
                    yield p, z
    for s in doc.sections:
        for hf in (s.header, s.footer, s.first_page_header, s.first_page_footer,
                   s.even_page_header, s.even_page_footer):
            if hf is not None:
                for p in hf.paragraphs:
                    yield p, 'hf'


def unify_document_fonts(doc, east_asia='宋体', latin='Times New Roman',
                         body_sz=None, table_sz=None, caption_sz=None,
                         styles=('Normal', 'Heading 1', 'Heading 2', 'Heading 3',
                                 'Heading 4', 'Caption', 'Body Text'),
                         cover_first_cell='文件编号'):
    """统一整份文档字体，并按分区设字号（字号单位=半磅，None 表示该分区不动）。

    返回 (改字体的 run 数, 设字号的 run 数, 改的样式数)。文本框内的 run 一律跳过：
    那是表单/示意图的排版，改字号会撑破框。
    """
    sizes = {'body': body_sz, 'table': table_sz, 'caption': caption_sz}
    n_font = n_sz = 0
    for p, zone in iter_zone_paragraphs(doc, cover_first_cell):
        sz = sizes.get(zone)
        for r in p._p.findall(qn('w:r')):
            if _in_textbox(r):
                continue
            rPr = r.find(qn('w:rPr'))
            if rPr is None:
                rPr = OxmlElement('w:rPr')
                r.insert(0, rPr)
            apply_rpr_font(rPr, east_asia, latin, sz)
            n_font += 1
            if sz:
                n_sz += 1
    n_style = sum(1 for nm in styles
                  if style_font(doc, nm, east_asia, latin,
                                body_sz if nm == 'Normal' else None))
    return n_font, n_sz, n_style


# --------------------------------------------------------------------------
# 表格重建原语（fill_table 之外的两种结构改动）
# --------------------------------------------------------------------------
def table_grid_cols(tbl):
    """现有列数：**必须看 tblGrid**，不能用末行的 tc 数——合并单元格会让 tc 数少于列数，
    据此判断会漏调列，产出「表头 5 列、数据行 4 格」的错位表。"""
    grid = tbl.find(qn('w:tblGrid'))
    if grid is not None:
        return len(grid.findall(qn('w:gridCol')))
    trs = tbl.findall(qn('w:tr'))
    return len(trs[-1].findall(qn('w:tc'))) if trs else 0


def flatten_table_rows(tbl, keep_head=0):
    """去掉纵向合并与数据行的横向合并。

    克隆末行做新数据行时，若该带 `vMerge`，首个新行没有可继承的上方 tc，
    python-docx 读 `row.cells` 会直接抛
    `ValueError: no `tc` element at grid_offset=…`（不是内容错误，是遍历失败）。
    """
    for ri, tr in enumerate(tbl.findall(qn('w:tr'))):
        for tc in tr.findall(qn('w:tc')):
            tcPr = tc.find(qn('w:tcPr'))
            if tcPr is None:
                continue
            for vm in tcPr.findall(qn('w:vMerge')):
                tcPr.remove(vm)
            if ri >= keep_head:
                for gs in tcPr.findall(qn('w:gridSpan')):
                    tcPr.remove(gs)


def substitute_wt_nodes(p, subs):
    """段落级词替换的**图形安全**版本。

    `docx_ops.apply_substitutions` 在整段仍残留关键词时会走"合并 run"分支
    （`p.runs[0].text = after`），而 `run.text` 赋值会清空该 run 的其它子节点 ——
    含 `w:pict`/`w:drawing` 的段落（表单文本框、示意图）会被连带抹掉，且不报错。
    含图形的段落只用本函数：逐 `w:t` 节点替换，不合并 run。
    """
    graphic = bool(p._p.findall('.//' + qn('w:pict'))
                   or p._p.findall('.//' + qn('w:drawing')))
    if not graphic:
        apply_substitutions(p, subs)
        return False
    for t in p._p.iter(qn('w:t')):
        if not t.text:
            continue
        new = t.text
        for old, rep in subs:
            if old and old in new:
                new = new.replace(old, rep)
        if new != t.text:
            t.text = new
            t.set(qn('xml:space'), 'preserve')
    return True


def release_orphan_word_locks(match=(), verbose=False):
    """释放"被杀掉的导出脚本"留下的无头 Word 锁。

    场景：用 Word COM 导 PDF 的脚本被中途终止 → finally 不执行 → WINWORD 仍开着产物文件，
    下一轮生成器写同名文件直接 PermissionError。判据要保守：**只处理 Visible=False 的实例**
    （用户自己开的 Word 一定是可见的），且只关闭文件名命中 match 前缀的文档，
    用 SaveChanges=0 不写盘（Word 在导出期会给文档打临时改动，写回去等于污染产物）。
    返回 (关闭的文档数, 是否退出实例)。
    """
    import win32com.client as w
    try:
        app = w.GetActiveObject('Word.Application')
    except Exception:
        return 0, False
    if getattr(app, 'Visible', True):
        return 0, False                       # 用户正在用：不动
    closed = 0
    for d in list(app.Documents):
        nm = d.Name
        if match and not any(str(nm).startswith(m) for m in match):
            continue
        d.Close(SaveChanges=0)
        closed += 1
        if verbose:
            print('closed', nm)
    quit_ok = False
    try:
        if app.Documents.Count == 0:
            app.Quit()
            quit_ok = True
    except Exception:
        pass
    return closed, quit_ok


# --------------------------------------------------------------------------
# 版式闸门：分页 / 标题树 / 图文同页 / 渲染判据
# --------------------------------------------------------------------------

_NUM_HEADING_RE = re.compile(
    r'^(第\s*[0-9一二三四五六七八九十百]+\s*[章节篇部分]'      # 第X章 / 第X节
    r'|\d+(?:\.\d+){0,2}\s'                                    # 1 / 1.1 / 1.1.1
    r'|\d+(?:\.\d+){1,2}(?=[^\d.\-]))')                        # 1.1名称；排除 1.1-（图号）
_CAPTION_RE = re.compile(r'^([图表]\s*[\d\-.]|\d+(?:\.\d+)*-\d+)')  # 图1 / 表2-1 / 2.7-1 流程图


def _style_outline_map(doc):
    """{styleId: (显示名, 样式自带 outlineLvl 或 None, basedOn)}。"""
    m = {}
    for s in doc.styles.element.findall(qn('w:style')):
        nm = s.find(qn('w:name'))
        ol = s.find('.//' + qn('w:outlineLvl'))
        bo = s.find(qn('w:basedOn'))
        m[s.get(qn('w:styleId'))] = (
            nm.get(qn('w:val')) if nm is not None else '?',
            int(ol.get(qn('w:val'))) if ol is not None else None,
            bo.get(qn('w:val')) if bo is not None else None)
    return m


def effective_outline(p_el, smap, _depth=0):
    """段落生效大纲级别：直接 pPr 优先，否则沿样式链；None = 正文级。

    必须沿链判定（§34）：值常在样式里而不在段落自己手上。
    """
    pPr = p_el.find(qn('w:pPr'))
    if pPr is None:
        return None
    direct = pPr.find(qn('w:outlineLvl'))
    if direct is not None:
        v = int(direct.get(qn('w:val')))
        return None if v > 8 else v
    st = pPr.find(qn('w:pStyle'))
    sid = st.get(qn('w:val')) if st is not None else None
    while sid and sid in smap and _depth <= 8:
        name, ol, based = smap[sid]
        if ol is not None:
            return None if ol > 8 else ol
        sid = based
        _depth += 1
    return None


def sect_breaks_page_el(p_el):
    """段落携带的分节符（pPr/sectPr）是否换页；type=continuous 不换页，缺省按 nextPage（§39）。"""
    pPr = p_el.find(qn('w:pPr'))
    sect = pPr.find(qn('w:sectPr')) if pPr is not None else None
    if sect is None:
        return False
    typ = sect.find(qn('w:type'))
    val = (typ.get(qn('w:val')) or 'nextPage') if typ is not None else 'nextPage'
    return val != 'continuous'


def chapter_pad_map(doc):
    """`[(章标题元素, 其前连续顶页空段元素列表)]`——`pagination_audit.chapter_pad` 与
    `pagination_repair('drop_chapter_pad')` **共用**这一份判据（§8 第 4 步：查改同源）。

    边界与 audit 一致：只看封面信息表之后（封面留白不算顶页，§42）；lvl==0 才算章标题；
    往回连续数空段，遇分节符载体段（它前面的空段属于上一节）整条作废；<2 段不算缺陷。
    **含域代码的空段（`fldChar`/`instrText`）不是回车**：目录区的 `end`/`separate` 常常单独占一段，
    删掉就留下没闭合的 TOC 域（实测 RD-068 begin/separate 各 6、end 只有 5 → Word 刷新时
    把 `TOC \\o` 指令裸露在页面上），所以它必须让整条链作废，而不只是"这一跳不删"。
    """
    smap = _style_outline_map(doc)
    kids = list(doc.element.body.iterchildren())
    etxt = lambda el: ''.join(t.text or '' for t in el.iter(qn('w:t')))
    egra = lambda el: bool(el.findall('.//' + qn('w:drawing'))
                           or el.findall('.//' + qn('w:pict')))
    efld = lambda el: bool(el.findall('.//' + qn('w:fldChar'))
                           or el.findall('.//' + qn('w:instrText')))
    cover_end = len(kids)
    for k, c in enumerate(kids):
        if c.tag.split('}')[-1] == 'tbl' and '文件编号' in etxt(c):
            cover_end = k
            break
    hits = []
    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p' or i < cover_end or effective_outline(c, smap) != 0:
            continue
        pads, j = [], i - 1
        while j >= 0 and kids[j].tag.split('}')[-1] == 'p' \
                and not etxt(kids[j]).strip() and not egra(kids[j]):
            # 分节符载体 / 域代码载体 → 整条作废（前面的空段不归本章管）
            if kids[j].find('.//' + qn('w:sectPr')) is not None or efld(kids[j]):
                pads = []
                break
            pads.append(kids[j])
            j -= 1
        if len(pads) >= 2:
            hits.append((c, pads))
    return hits


def pagination_audit(doc, cover_texts=()):
    """分页 / 标题树体检（只读）。返回 dict，各项为空即通过。

    对应 pitfalls §23 §24 §25 §38 §39 §41。`cover_texts` 传封面区文档名
    （归一化去空白后比较），用于识别"封面短行被写成一级标题"。
    """
    smap = _style_outline_map(doc)
    body = doc.element.body
    kids = list(body.iterchildren())
    # 以下三个 helper 作用于 CT_P 元素（库内 paragraph_text/has_graphic 收 Paragraph 对象）
    etxt = lambda el: ''.join(t.text or '' for t in el.iter(qn('w:t')))
    egra = lambda el: bool(el.findall('.//' + qn('w:drawing'))
                           or el.findall('.//' + qn('w:pict')))

    def flag(el, tag):
        """布尔型 pPr 子元素：必须判 w:val，写成 val="0"/"false" 是**关闭**。"""
        if el is None:
            return False
        e = el.find(qn(tag))
        if e is None:
            return False
        v = (e.get(qn('w:val')) or '1').strip().lower()
        return v not in ('0', 'false', 'off', 'none')

    def in_field(el):
        """段落是否落在某个域内（目录/索引条目自带编号文本与页码，§41 必须先排除）。"""
        if el.findall('.//' + qn('w:fldChar')) or el.findall('.//' + qn('w:instrText')):
            return True
        st = el.find('.//' + qn('w:pStyle'))
        sid = st.get(qn('w:val')) if st is not None else ''
        nm = smap.get(sid, ('', None, None))[0]
        return nm.startswith('TOC') or nm.startswith('目录')

    out = dict(hard_page_breaks=0, stacked_breaks=[], redundant_breaks=[],
               body_page_break=[],
               keep_on_body=[], chapter_pad=[], outline_anomaly=[],
               numbered_not_in_tree=[], toc_field=False)

    # 封面区边界：封面信息表之前的空段属封面留白，不是"章前顶页回车"（§23 只管正文区）
    cover_end = len(kids)
    for k, c in enumerate(kids):
        if c.tag.split('}')[-1] == 'tbl' and '文件编号' in etxt(c):
            cover_end = k
            break

    for b in doc.element.iter(qn('w:br')):
        if b.get(qn('w:type')) == 'page':
            out['hard_page_breaks'] += 1
    out['toc_field'] = bool(re.search(r'<w:instrText[^>]*>\s*TOC',
                                      doc.element.xml))

    padmap = {h: len(p) for h, p in chapter_pad_map(doc)}   # 元素作键（§43），不用 id()

    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p':
            continue
        pPr = c.find(qn('w:pPr'))
        t = etxt(c).strip()
        nt = re.sub(r'\s+', '', t)
        lvl = effective_outline(c, smap)
        pbb = flag(pPr, 'w:pageBreakBefore')
        hard = any(b.get(qn('w:type')) == 'page'
                   for b in c.iter(qn('w:br')))
        if hard and pbb:
            out['stacked_breaks'].append(t[:30] or '<空段>')          # §39 段前分页+段内硬分页
        elif pbb:
            prv = kids[i - 1] if i > 0 else None                     # §39 分节符+段前分页
            if prv is not None and prv.tag.split('}')[-1] == 'p' and sect_breaks_page_el(prv):
                # 实测：分节符(nextPage) 已换页，再加段前分页 Word 会折叠掉，
                # 并不必然多一页 —— 所以记"冗余"交渲染结果裁决，不当阻断项误报。
                out['redundant_breaks'].append('分节符+段前分页：' + (t[:24] or '<空段>'))
        if pbb and lvl is None and t:
            out['body_page_break'].append(t[:30])                     # §39
        if lvl is None and pPr is not None and (
                flag(pPr, 'w:keepNext') or flag(pPr, 'w:keepLines')):
            out['keep_on_body'].append(                               # §38
                ('<图/空段>' if egra(c) else '') + t[:30])
        if lvl == 0:
            n = padmap.get(c, 0)                                     # §23 判据见 chapter_pad_map
            if n >= 2 and i >= cover_end:
                out['chapter_pad'].append((t[:24], n))
            if nt in {re.sub(r'\s+', '', x) for x in cover_texts}:
                out['outline_anomaly'].append(('封面短行带一级大纲', t[:24]))
        if lvl is not None and not t and not in_field(c):
            out['outline_anomaly'].append(('空标题段', ''))            # §24
        if lvl is None and t and not in_field(c) \
                and _NUM_HEADING_RE.match(t) and not _CAPTION_RE.match(t):
            out['numbered_not_in_tree'].append(t[:30])                # §41
    return out

def page_ink_coverage(pdf_path, dpi=50, band=0.08, cutoff=200):
    """逐页返回"正文区墨占比(%)"，用于空白页判据（§40）。

    中文 PDF 常为子集字体且无 ToUnicode，pdftotext 只吐数字/拉丁，
    "字数"判据会把正常纯中文页误判为空白页——墨占比不受字体影响。
    经验档位：封面 2~3%，正文 3~13%，真空白页 0.0%。
    """
    import subprocess, tempfile, os, shutil
    tmp = tempfile.mkdtemp()
    try:
        subprocess.run(['pdftoppm', '-png', '-r', str(dpi), pdf_path,
                        os.path.join(tmp, 'p')], check=True, capture_output=True)
        pages = sorted(f for f in os.listdir(tmp) if f.endswith('.png'))
        res = []
        try:
            from PIL import Image
        except ImportError:                                     # 退化：PyMuPDF
            import fitz
            doc = fitz.open(pdf_path)
            for pg in doc:
                pix = pg.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
                w, h = pix.width, pix.height
                buf = pix.samples
                y0, y1 = int(h * band), int(h * (1 - band))
                seg = buf[y0 * w:(y1) * w]
                res.append(round(sum(1 for v in seg if v < cutoff) / len(seg) * 100, 3))
            doc.close()
            return res
        for f in pages:
            im = Image.open(os.path.join(tmp, f)).convert('L')
            w, h = im.size
            crop = im.crop((0, int(h * band), w, int(h * (1 - band))))
            px = list(crop.getdata())
            res.append(round(sum(1 for v in px if v < cutoff) / len(px) * 100, 3))
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def grade_pages_by_ink(coverage, blank=0.15, thin=0.8):
    """按 §37 分级 + §40 墨占比判据给出 (阻断项, 提示项)。

    末页单列：§41 的"末页 <0.8% 记提示"要盖过"空白页阻断"——正文只剩 1~2 行的末页
    墨占比会低到 0.1%，那是 §37 说的溢出行，交人决定，不能用偏离基线的行距去压页；
    只有**一点墨都没有**（c==0）的末页才是真空白页，仍然阻断。
    """
    block, warn = [], []
    n = len(coverage)
    for i, c in enumerate(coverage, 1):
        if c <= 0.0:
            block.append('第%d页正文区无墨（空白页）' % i)
        elif i == n and c < thin:
            warn.append('第%d页%.2f%%墨（末页溢出，交人决定）' % (i, c))
        elif c < blank:
            block.append('第%d页正文区无墨（空白页）' % i)
        elif i < n and c < thin:
            block.append('第%d页仅%.2f%%墨（疑似顶页/分页错位）' % (i, c))
    return block, warn


def pagination_repair(doc, cover_texts=(), apply=None):
    """按 pagination_audit 的判据**就地修复**分页与标题树缺陷，返回 {项: 处置数}。

    与 pagination_audit 共用同一套判据，避免"查的是一套、改的是另一套"。
    `apply` 可传子集限定动作；默认全开。所有动作都不改文字内容、不改 pStyle、不改字号。

    动作：
      drop_hard_break   段前分页已存在时删掉段内 `w:br type=page`（§39 空白页根因）；
                        段内只有硬分页符时：纯空占位段整段删除，有内容的段**换成**
                        `pageBreakBefore`（计入 `pbb_from_hard`），保证全包计数归零
      drop_pbb_after_sect 前一段是**换页**分节符时删掉本段的 `pageBreakBefore`
                        （§39 另一种叠加：分节符已换页，再写段前分页就多一张空白页；
                         sectPr 的 type 为 continuous 时段前分页要保留）
      drop_pad_tabs     章级标题里多余的制表符（保留 1 个，与全文其余章标题对齐）
      drop_chapter_pad  章标题前的顶页空段（§23；封面区与分节符载体段不动）
      demote_cover      封面文档名的大纲级别降为正文级 9（§25/§42）
      demote_empty      空标题段降级为 9（§24；带 sectPr/域/图形的只能降级不能删）
      drop_body_keep    正文级段落上的 keepNext/keepLines（§38 "点点"根因）
      drop_keep_before_table
                        标题段带 keepNext 且**下一块就是整张表**时摘掉（§45.2；
                        audit 的 keep_on_body 不收它——它不是"属性加错了段"，是"绑定对象太大"）
    """
    ALL = ('drop_hard_break', 'drop_pbb_after_sect', 'drop_pad_tabs', 'drop_chapter_pad',
           'demote_cover', 'demote_empty', 'drop_body_keep', 'drop_keep_before_table')
    apply = set(ALL) if apply is None else set(apply)
    stats = dict.fromkeys(ALL, 0)
    smap = _style_outline_map(doc)
    body = doc.element.body
    etxt = lambda el: ''.join(t.text or '' for t in el.iter(qn('w:t')))
    egra = lambda el: bool(el.findall('.//' + qn('w:drawing'))
                           or el.findall('.//' + qn('w:pict')))

    def flag_on(pPr, tag):
        if pPr is None:
            return False
        e = pPr.find(qn(tag))
        if e is None:
            return False
        return (e.get(qn('w:val')) or '1').strip().lower() not in ('0', 'false', 'off', 'none')

    def set_outline(el, val):
        pPr = el.get_or_add_pPr()
        e = pPr.find(qn('w:outlineLvl'))
        if e is None:
            e = OxmlElement('w:outlineLvl')
            pPr.append(e)
        e.set(qn('w:val'), str(val))

    sect_breaks_page = sect_breaks_page_el          # 与 audit 同一判据

    # 封面区边界
    kids = list(body.iterchildren())
    cover_end = len(kids)
    for k, c in enumerate(kids):
        if c.tag.split('}')[-1] == 'tbl' and '文件编号' in etxt(c):
            cover_end = k
            break
    coverset = {re.sub(r'\s+', '', x) for x in cover_texts}

    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p':
            continue
        pPr = c.find(qn('w:pPr'))
        t = etxt(c).strip()
        lvl = effective_outline(c, smap)
        pbb = flag_on(pPr, 'w:pageBreakBefore')
        if 'drop_hard_break' in apply:
            brs = [b for b in list(c.iter(qn('w:br'))) if b.get(qn('w:type')) == 'page']
            for b in brs:
                run = b.getparent()
                if run is not None:
                    run.remove(b)
                stats['drop_hard_break'] += 1
            if brs and not pbb:
                carrier = (pPr is not None and pPr.find(qn('w:sectPr')) is not None) \
                    or egra(c) or bool(c.findall('.//' + qn('w:fldChar')))
                if not t and not carrier:
                    nxt = c.getnext()
                    nxt_breaks = (nxt is not None and nxt.tag == qn('w:p') and (
                        flag_on(nxt.find(qn('w:pPr')), 'w:pageBreakBefore')
                        or any(b.get(qn('w:type')) == 'page' for b in nxt.iter(qn('w:br')))))
                    if nxt_breaks:
                        # 下一段自己就换页 → 占位段删掉，否则"空段分页 + 下段分页"又是一张空白页
                        body.remove(c)
                        stats['pad_removed'] = stats.get('pad_removed', 0) + 1
                        continue
                    # 下一段不换页 → 这个空段就是封面/章节的分页占位，**就地转成段前分页**，
                    # 不能删（删了分页意图就丢了，实测封面与正文第一块被排到同一页）
                pPr2 = c.get_or_add_pPr()
                if pPr2.find(qn('w:pageBreakBefore')) is None:
                    e = OxmlElement('w:pageBreakBefore')
                    pPr2.insert(0 if pPr2.find(qn('w:pStyle')) is None else 1, e)
                    stats['pbb_from_hard'] = stats.get('pbb_from_hard', 0) + 1
        if 'drop_pbb_after_sect' in apply and pbb and pPr is not None:
            prev = c.getprevious()
            if prev is not None and prev.tag.split('}')[-1] == 'p' and sect_breaks_page(prev):
                for old in pPr.findall(qn('w:pageBreakBefore')):
                    pPr.remove(old)
                    stats['drop_pbb_after_sect'] += 1
        if 'drop_pad_tabs' in apply and lvl == 0:
            tabs = [x for x in c.iter(qn('w:tab'))]
            for x in tabs[1:]:
                x.getparent().remove(x)
                stats['drop_pad_tabs'] += 1
        if 'drop_body_keep' in apply and lvl is None and pPr is not None:
            for tag in ('w:keepNext', 'w:keepLines'):
                e = pPr.find(qn(tag))
                if e is not None and flag_on(pPr, tag):
                    pPr.remove(e)
                    stats['drop_body_keep'] += 1
        if 'drop_keep_before_table' in apply and lvl is not None and pPr is not None \
                and flag_on(pPr, 'w:keepNext'):
            nxt = c.getnext()          # §45.2：标题 + 整张表被 keepNext 粘成一整块，块高超过剩余页高时
            if nxt is not None and nxt.tag == qn('w:tbl'):
                # 整块跳到下一页，上一页底部留大片空白，表后的说明行还会被挤成 0.26% 墨的薄页。
                pPr.remove(pPr.find(qn('w:keepNext')))
                stats['drop_keep_before_table'] += 1
        if 'demote_cover' in apply and lvl == 0 and i < cover_end \
                and re.sub(r'\s+', '', t) in coverset:
            set_outline(c, 9)
            stats['demote_cover'] += 1
        if 'demote_empty' in apply and lvl is not None and not t:
            set_outline(c, 9)
            stats['demote_empty'] += 1

    # 顶页空段：判据取自 chapter_pad_map，与 audit 的 chapter_pad 同一份（§8 第 4 步）。
    # 删一段序号全变，所以按最新段落表反复重扫（§23 边界3）。
    if 'drop_chapter_pad' in apply:
        for _round in range(6):
            hits = chapter_pad_map(doc)
            if not hits:
                break
            did = 0
            for _h, pads in hits:
                for el in pads:
                    # 只删"纯空段"：图形/分节符/域载体一律保留（chapter_pad_map 已排除图形与分节符）
                    if el.getparent() is body:
                        body.remove(el)
                        did += 1
            stats['drop_chapter_pad'] += did
            if not did:
                break
    return {k: v for k, v in stats.items() if v}


def set_cover_spacers(doc, n=3, first_cell_text='文件编号', body_style=None):
    """把「封面标题文字」与「封面信息表」之间的空段统一为 n 个正文空行。

    返回 dict。空段一律用正文样式（body_style 传样式 id；缺省沿用已存在空段的
    样式，没有则不写 pStyle 即 Normal）。只动封面区，不碰正文。
    护栏：标题与封面表之间若混入非空段或图形，直接跳过不动，交人处理。
    """
    body = doc.element.body
    kids = list(body.iterchildren())
    is_p = lambda c: c.tag.split('}')[-1] == 'p'
    etxt = lambda el: ''.join(t.text or '' for t in el.iter(qn('w:t')))
    ti = next((i for i, c in enumerate(kids) if is_p(c) and etxt(c).strip()), None)
    tb = next((i for i, c in enumerate(kids)
               if c.tag.split('}')[-1] == 'tbl' and first_cell_text in etxt(c)), None)
    if ti is None or tb is None or tb <= ti:
        return {'skipped': '未定位到封面标题或封面表'}
    span = [c for c in kids[ti + 1:tb] if is_p(c)]
    empties = [c for c in span if not etxt(c).strip()
               and not c.findall('.//' + qn('w:drawing'))
               and not c.findall('.//' + qn('w:pict'))
               and c.find('.//' + qn('w:sectPr')) is None]
    if len(empties) != len(span):
        return {'skipped': '标题与封面表之间含非空段或图形，不动', 'before': len(empties)}
    donor = body_style
    if donor is None and empties:
        st = empties[0].find('.//' + qn('w:pStyle'))
        donor = st.get(qn('w:val')) if st is not None else None
    before = len(empties)
    removed = 0
    for c in empties[n:]:
        body.remove(c)
        removed += 1
    kept = max(0, before - removed)
    added = 0
    anchor = kids[ti]
    for _ in range(n - kept):
        p = OxmlElement('w:p')
        if donor:
            pPr = OxmlElement('w:pPr')
            s = OxmlElement('w:pStyle')
            s.set(qn('w:val'), donor)
            pPr.append(s)
            p.append(pPr)
        anchor.addnext(p)
        anchor = p
        added += 1
    return {'before': before, 'after': kept + added, 'removed': removed, 'added': added}


def set_cover_top_spacers(doc, n=9, first_cell_text='文件编号', body_style=None):
    """把"封面标题之前的空段"统一成 n 行 —— 让封面整块落在版心**居中偏上**。

    为什么不用 `w:vAlign` + 分节（两条都实测踩过）：
      1. vAlign 是**节**属性。想让封面单独居中就得让封面单独成节，而新建节的 sectPr 只要
         带着与正文节相同的 headerReference/footerReference（哪怕换 r:id 指向同一部件），
         Word 就判"文件可能已经损坏"；把引用**搬**到封面节又会让正文节的首页眉脚状态改变，
         而且同节里被一起拖进来的目录页/前言页也会被竖排居中。
      2. 有的模板第一节本来就含目录/前言（封面不是独立节），节边界与封面页不是一回事。
    段前空段是纯流式排版：不碰节、不碰眉脚、不影响其它页，且**幂等**（先把已有前导空段
    清成基准再补到 n），换字号时按渲染墨区复核一次即可。
    返回 dict {before, after, removed, added}。
    """
    body = doc.element.body
    kids = list(body.iterchildren())
    is_p = lambda c: c.tag == qn('w:p')
    etxt = lambda el: ''.join(x.text or '' for x in el.iter(qn('w:t')))
    tb = next((i for i, c in enumerate(kids)
               if c.tag == qn('w:tbl') and first_cell_text in etxt(c)), None)
    if tb is None:
        return {'skipped': '未找到封面信息表'}
    ti = next((i for i in range(tb) if is_p(kids[i]) and etxt(kids[i]).strip()), None)
    if ti is None:
        return {'skipped': '封面表之前没有标题段'}
    lead = []
    for c in kids[:ti]:
        if not is_p(c):
            continue
        if etxt(c).strip() or c.findall('.//' + qn('w:sectPr'))                 or c.findall('.//' + qn('w:drawing')) or c.findall('.//' + qn('w:pict'))                 or c.findall('.//' + qn('w:fldChar')):
            break                       # 遇到非空/载体段就停，封面顶部留白只数最靠近标题的那一段
        lead.append(c)
    before = len(lead)
    removed = 0
    for c in lead[n:]:
        body.remove(c)
        removed += 1
    kept = min(before, n)
    donor = body_style
    if donor is None:
        st = kids[ti].find('.//' + qn('w:pStyle'))
        donor = st.get(qn('w:val')) if st is not None else None
    # 前导空段要紧贴标题之上：以第一个保留的空段为锚往它前面补；一个不剩就直接插到标题前
    added = 0
    cursor = lead[0] if kept else kids[ti]
    for _ in range(n - kept):
        p = OxmlElement('w:p')
        if donor:
            pPr = OxmlElement('w:pPr')
            s = OxmlElement('w:pStyle')
            s.set(qn('w:val'), donor)
            pPr.append(s)
            p.append(pPr)
        cursor.addprevious(p)
        added += 1
    return {'before': before, 'after': kept + added, 'removed': removed, 'added': added}


def set_cover_block_valign(doc, valign='center', first_cell_text='文件编号', below_spacers=0,
                           body_style=None, raise_pt=0):
    """让封面整块（标题文字＋封面信息表）在版心里**居中**，并用"表后空段"把可视块顶到**偏上**。

    为什么不用"标题前空段"定位：那要数准每行行高，字号／行距／软件（Word、WPS、LibreOffice）
    一变就漂；`w:vAlign` 由排版引擎按实际内容高度居中，天然稳。
    "居中偏上" = `vAlign=center` 的对称中心被**表后的 n 个空段**上移：
    居中对象变成"封面块＋尾部空段"，可见块上移约 (n × 行高)/2。

    只动封面所在那一节（封面表所在节），正文节不受影响。
    `valign=None` 且 below_spacers=0 时等于撤销本函数留下的设置。
    返回 dict：{sectPr 是否改, vAlign 值, 表后空段 before/after}。
    """
    body = doc.element.body
    kids = list(body.iterchildren())
    etxt = lambda el: ''.join(x.text or '' for x in el.iter(qn('w:t')))
    is_p = lambda c: c.tag.split('}')[-1] == 'p'
    ti = next((i for i, c in enumerate(kids) if is_p(c) and etxt(c).strip()), None)
    tb = next((i for i, c in enumerate(kids)
               if c.tag.split('}')[-1] == 'tbl' and first_cell_text in etxt(c)), None)
    if tb is None:
        return {'skipped': '未找到封面信息表'}
    # 封面所在节的 sectPr：从封面表往后找到第一个带 sectPr 的段落（找不到就是 body 末尾那个）
    sect = None
    for c in kids[tb:]:
        if c.tag.split('}')[-1] == 'p':
            pPr = c.find(qn('w:pPr'))
            if pPr is not None and pPr.find(qn('w:sectPr')) is not None:
                sect = pPr.find(qn('w:sectPr'))
                anchor = c
                break
    if sect is None:
        # 封面**不单独成节**（整份文档只有一个 body 级 sectPr）时绝不能回退去改那个 sectPr：
        # 那是"最后一节"的属性，会把**全文每一页**都竖排居中，页数与正文排版一起崩
        # （实测一份只有 1 节的模板：封面块从 2%~98% 变成 28%~72%，且全文多出一页）。
        return {'skipped': '封面不单独成节，vAlign 会作用到全文；先让封面成节或改用段前空段定位'}
    r = {'sect_found': sect is not None}
    if sect is not None:
        e = sect.find(qn('w:vAlign'))
        if valign is None:
            if e is not None:
                sect.remove(e)
        else:
            if e is None:
                e = OxmlElement('w:vAlign')
                # w:vAlign 在 CT_SectPr 里排在 pgMar 之后、cols 之前；追加后 Word 也能读，
                # 但为稳妥按 schema 顺序插到 cols/type 之前
                for tag in ('w:cols', 'w:docGrid', 'w:printerSettings', 'w:type'):
                    at = sect.find(qn(tag))
                    if at is not None:
                        at.addprevious(e)
                        break
                else:
                    sect.append(e)
            e.set(qn('w:val'), valign)
        r['vAlign'] = valign
    # "偏上"的量：加大**本节**的下页边距。vAlign 是按版心高度居中的，
    # 版心下边界上移 → 居中块整体上移，且**不往节里塞内容**，不会有溢出成空白页的风险
    # （实测垫空段的方案：某份文档加 2 段就多出整整一页空白）。
    if raise_pt:
        pgmar = sect.find(qn('w:pgMar'))
        if pgmar is None:                     # 本节没写 pgMar 时先从最后一节克隆一份，再改下边距
            bs0 = body.find(qn('w:sectPr'))
            bm0 = bs0.find(qn('w:pgMar')) if bs0 is not None else None
            if bm0 is not None:
                import copy as _c
                pgmar = _c.deepcopy(bm0)
                at = sect.find(qn('w:pgSz'))
                if at is not None:
                    at.addnext(pgmar)
                else:
                    sect.append(pgmar)
        body_mar = pgmar.get(qn('w:bottom')) if pgmar is not None else None
        if pgmar is not None and body_mar is not None:
            try:
                base_twip = int(body_mar)
            except (TypeError, ValueError):
                base_twip = 0
            # 页脚位置由 pgMar@footer（距页面下边界）决定，与下边距无关，所以不用动它；
            # 下边距只会变大，正文更不会压到页脚。
            pgmar.set(qn('w:bottom'), str(base_twip + int(raise_pt * 20)))
            r['bottom_margin_twip'] = pgmar.get(qn('w:bottom'))
    # 表后空段（尾部垫高，让可见块上移）
    if True:
        after = kids[tb + 1:]
        donor = body_style
        span, stopped = [], False
        for c in after:
            if not is_p(c):
                break
            pPr = c.find(qn('w:pPr'))
            if (etxt(c).strip() or pPr is not None
                    and pPr.find(qn('w:sectPr')) is not None):
                break
            if c.findall('.//' + qn('w:drawing')) or c.findall('.//' + qn('w:pict'))                     or c.findall('.//' + qn('w:fldChar')):
                break
            span.append(c)
        if donor is None and span:
            st = span[0].find('.//' + qn('w:pStyle'))
            donor = st.get(qn('w:val')) if st is not None else None
        before = len(span)
        for c in span[below_spacers:]:
            body.remove(c)
        anchor_el = kids[tb]
        kept = min(before, below_spacers)
        for c in span[:kept]:
            anchor_el = c
        added = 0
        for _ in range(below_spacers - kept):
            p = OxmlElement('w:p')
            if donor:
                pPr = OxmlElement('w:pPr')
                s = OxmlElement('w:pStyle')
                s.set(qn('w:val'), donor)
                pPr.append(s)
                p.append(pPr)
            anchor_el.addnext(p)
            anchor_el = p
            added += 1
        r['spacers'] = {'before': before, 'after': kept + added}
    return r


def ensure_cover_section(doc, first_cell_text='文件编号'):
    """让"标题＋封面信息表"自成一节（下一页分节符），这样封面才能单独做垂直对齐。

    有些模板整份文档只有一个 body 级 `sectPr`，封面和正文同属一节。此时想给封面设
    `w:vAlign` 只能改那个唯一的 sectPr，而它是"最后一节"的属性 —— 结果全文每一页都被竖排
    居中（实测：封面块从 2%~98% 变成 28%~72%，正文页也跟着居中，页数还多出一页）。
    所以先补一节：把分节符插在**正文首块之前**，分节符段自己归封面节。

    新节的 `sectPr` 从 body 级那份整体克隆，页面尺寸、页边距、页眉页脚引用与正文节完全一致
    （dod 第 12/15 项要求逐节页宽页距一致），并把 `w:type` 强制为 `nextPage`。
    返回 dict；封面已单独成节时只报告不重复插。
    """
    body = doc.element.body
    kids = list(body.iterchildren())
    etxt = lambda el: ''.join(x.text or '' for x in el.iter(qn('w:t')))
    cover_tbl = next((c for c in kids
                      if c.tag.split('}')[-1] == 'tbl' and first_cell_text in etxt(c)), None)
    if cover_tbl is None:
        return {'skipped': '未找到封面信息表'}
    idx = kids.index(cover_tbl)
    # 封面节应当在此结束：往后找第一个"带 sectPr 的段落"与第一个"有文字的正文块"
    first_body = None
    for c in kids[idx + 1:]:
        if c.tag.split('}')[-1] != 'p':
            break
        if etxt(c).strip():
            first_body = c
            break
        if c.find('.//' + qn('w:pPr') + '/' + qn('w:sectPr')) is not None:
            return {'already': True}          # 封面后面已有分节符，本就自成一节
    if first_body is None:
        return {'skipped': '封面之后找不到正文首块'}
    base = body.find(qn('w:sectPr'))
    if base is None:
        return {'skipped': '文档没有 body 级 sectPr，无法克隆节属性'}
    import copy
    sect = copy.deepcopy(base)
    # 页眉页脚引用**只能有一个节带着**：同一个眉脚部件被两节同时引用（哪怕换 r:id），
    # Word 直接判"文件可能已经损坏"（实测克隆 body 级 sectPr 插入分节符后 LibreOffice 与 Word
    # 都拒绝打开）。正确做法是把引用**整体搬进封面节**，正文节不带引用 → 按 Word 的
    # link-to-previous 模型自动继承封面节的眉脚，每一页都还在。
    moved = 0
    # 克隆体自带的引用必须**先删**：deepcopy 已经把 base 的四条引用复制过来了，
    # 再把 base 的原元素插进去就成了"同一个 r:id 在同一个 sectPr 里写两遍"，
    # Word 直接判文件损坏（实测 RD-057/RD-069 打不开，LibreOffice 也不出图）。
    for tag in ('w:headerReference', 'w:footerReference'):
        for e in list(sect.findall(qn(tag))):
            sect.remove(e)
    # 只有 headerReference/footerReference 需要搬（CT_SectPr 里它们排在最前，插到 pgSz 之前合法）；
    # titlePg 克隆体里本来就有，正文节那一份要**删掉**——它已不再引用首页眉脚，
    # 留着会让正文节第一页页眉变空白。
    for tag in ('w:headerReference', 'w:footerReference'):
        for e in list(base.findall(qn(tag))):
            base.remove(e)
            at = sect.find(qn('w:pgSz'))
            if at is not None:
                at.addprevious(e)
            else:
                sect.insert(0, e)
            moved += 1
    for e in list(base.findall(qn('w:titlePg'))):
        base.remove(e)
    typ = sect.find(qn('w:type'))
    if typ is None:
        typ = OxmlElement('w:type')
        sect.insert(0, typ)
    typ.set(qn('w:val'), 'nextPage')
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    pPr.append(sect)
    p.append(pPr)
    first_body.addprevious(p)
    return {'inserted': True, 'before': etxt(first_body).strip()[:20],
            'moved_refs': moved}


_TBLPR_AFTER_BORDERS = ('w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption',
                        'w:tblDescription')
_SIDES = ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')


def set_table_borders_six_way(doc, first_cell_text='文件编号', sz=4, val='single',
                              color='auto', skip_cover=True):
    """给每张表补齐**六向**实线（top/left/bottom/right/insideH/insideV）。

    这是一条"项目/用户显式排版要求"，按 `generality-boundaries-and-precedence.md` 第一节
    的优先级高于 §51 的通用默认（§51 通用默认是"表级与样式都无框线属设计，什么都不加；
    只补 left、绝不补 inside*"）。经验库里保留 §51 原语不动，另设本函数，
    需要六向边框的项目显式调用，两边都不污染对方。

    同时清掉单元格级 `w:tcBorders` 里 `val="nil|none"` 的边——不摘的话表级补了线也照样缺边。
    返回 {表号: [处置]}。
    """
    body = doc.element.body
    kids = list(body.iterchildren())
    etxt = lambda el: ''.join(x.text or '' for x in el.iter(qn('w:t')))
    cover_tbl = next((c for c in kids
                      if c.tag.split('}')[-1] == 'tbl' and first_cell_text in etxt(c)), None)
    res = {}
    for i, tbl in enumerate(doc.tables):
        el = tbl._tbl
        if skip_cover and el is cover_tbl:
            continue
        acts = []
        tblPr = el.find(qn('w:tblPr'))
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            el.insert(0, tblPr)
        bds = tblPr.find(qn('w:tblBorders'))
        if bds is None:
            bds = OxmlElement('w:tblBorders')
            ref = next((tblPr.find(qn(tag)) for tag in _TBLPR_AFTER_BORDERS
                        if tblPr.find(qn(tag)) is not None), None)
            if ref is not None:
                ref.addprevious(bds)
            else:
                tblPr.append(bds)
        for side in _SIDES:
            e = bds.find(qn('w:' + side))
            if e is None:
                e = OxmlElement('w:' + side)
                bds.append(e)
            if (e.get(qn('w:val')) or 'single') in ('nil', 'none'):
                acts.append('table:%s %s->%s' % (side, e.get(qn('w:val')), val))
            e.set(qn('w:val'), val)
            e.set(qn('w:sz'), str(sz))
            e.set(qn('w:space'), '0')
            e.set(qn('w:color'), color)
        for tcPr in el.findall('.//' + qn('w:tcPr')):
            cb = tcPr.find(qn('w:tcBorders'))
            if cb is None:
                continue
            for side in _SIDES:
                e = cb.find(qn('w:' + side))
                if e is not None and (e.get(qn('w:val')) or '') in ('nil', 'none'):
                    cb.remove(e)
                    acts.append('cell:%s nil 摘除' % side)
            if cb is not None and not len(cb):
                tcPr.remove(cb)
        if acts:
            res[i + 1] = acts
    return res


def normalize_table_geometry(doc, first_cell_text='文件编号', keep_cover_float=True,
                             border_sz=4, apply=('indent', 'borders', 'float', 'grid'),
                             grid_overrides=None, verbose=False):
    """修表格"左边框丢失/像被隐藏"的四类根因，返回 {表号: 处置列表}。

    四类根因症状相同、成因不同，必须分开判：
      indent  负 `w:tblInd` 把整表左推出对齐线 -> 归 0，左边框回到版心左沿
      borders 表级 `w:tblBorders/w:left` 缺失，或单元格 `w:tcBorders/w:left val="nil"`
              把左边框显式删掉 -> 只补"其他边有框线、唯独左边没有"的真缺失；
              设计上无框线的表（四边皆 nil 且表级/样式无框线）不动，避免加出线来
      float   正文表格继承了封面模板的 `w:tblpPr`（浮动 + `horzAnchor=page` +
              `tblpX` 小于左页边距）-> 去浮动改回行内；封面表按 §2 保留浮动
      grid    `w:tblGrid` 列宽总和大于版心 -> 按原比例缩放到版心宽，并同步 tcW/tblW；
              超过版心 2 倍者判为**列宽数据污染**（等比缩放后首列仍是一字宽），
              只报不改，除非在 `grid_overrides` 里给出该表的显式列宽
    `grid_overrides`: {表号(1 基): [各列 twips]}，长度须等于列数，总和自动等比归一到版心宽。
    """
    is_p = lambda c: c.tag.split('}')[-1] == 'p'
    etxt = lambda el: ''.join(t.text or '' for t in el.iter(qn('w:t')))
    body = doc.element.body
    kids = list(body.iterchildren())
    cover_tbl = next((c for c in kids
                      if c.tag.split('}')[-1] == 'tbl' and first_cell_text in etxt(c)), None)
    sec = doc.sections[0]
    text_w = sec.page_width.twips - sec.left_margin.twips - sec.right_margin.twips
    res = {}
    for i, t in enumerate(doc.tables):
        tbl = t._tbl
        acts = []
        tblPr = tbl.find(qn('w:tblPr'))
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl.insert(0, tblPr)
        is_cover = (tbl is cover_tbl)
        if 'indent' in apply:
            ind = tblPr.find(qn('w:tblInd'))
            if ind is not None:
                try:
                    v = int(ind.get(qn('w:w')) or 0)
                except (TypeError, ValueError):
                    v = 0
                if v < 0:
                    ind.set(qn('w:w'), '0')
                    ind.set(qn('w:type'), 'dxa')
                    acts.append('indent:%d->0' % v)
        if 'borders' in apply:
            # 1) 先摘掉单元格级把边框显式设成 nil/none 的写法（"像被隐藏"的直接元凶）
            fixed = 0
            for tcPr in tbl.findall('.//' + qn('w:tcPr')):
                cb = tcPr.find(qn('w:tcBorders'))
                if cb is None:
                    continue
                for side in ('left', 'right', 'top', 'bottom'):
                    e = cb.find(qn('w:' + side))
                    if e is not None and (e.get(qn('w:val')) or '').lower() in ('nil', 'none', 'hidden'):
                        cb.remove(e)
                        fixed += 1
            if fixed:
                acts.append('cell-border-nil:%d' % fixed)
            # 2) 只在"表级无左边框 且 首列单元格也没有单线"时补表级左边框。
            #    表级缺失但首列有单线的表渲染正常，补 insideH/insideV 反而会给
            #    设计上无内线的表凭空加线——所以这里只补 left，绝不动 inside*。
            b = tblPr.find(qn('w:tblBorders'))
            le = b.find(qn('w:left')) if b is not None else None
            tbl_left_ok = le is not None and (le.get(qn('w:val')) or '').lower() not in ('none', 'nil', 'hidden')
            first_col_line = False
            for r in tbl.findall(qn('w:tr')):
                tcs = r.findall(qn('w:tc'))
                if not tcs:
                    continue
                tcPr = tcs[0].find(qn('w:tcPr'))
                cb = tcPr.find(qn('w:tcBorders')) if tcPr is not None else None
                if cb is None:
                    first_col_line = True   # 单元格未覆盖 -> 跟随表级/样式，视为有
                    break
                e = cb.find(qn('w:left'))
                if e is None or (e.get(qn('w:val')) or '').lower() not in ('nil', 'none', 'hidden'):
                    first_col_line = True
                    break
            if not tbl_left_ok and not first_col_line:
                if b is None:
                    b = OxmlElement('w:tblBorders')
                    tblPr.append(b)
                e = OxmlElement('w:left')
                e.set(qn('w:val'), 'single')
                e.set(qn('w:sz'), str(border_sz))
                e.set(qn('w:space'), '0')
                e.set(qn('w:color'), 'auto')
                ex = b.find(qn('w:left'))
                if ex is not None:
                    b.remove(ex)
                b.append(e)
                acts.append('add-table-left-border')
        if 'float' in apply and not (is_cover and keep_cover_float):
            if tblPr.find(qn('w:tblpPr')) is not None:
                tblPr.remove(tblPr.find(qn('w:tblpPr')))
                acts.append('unfloat')
        if 'grid' in apply:
            grid = tbl.find(qn('w:tblGrid'))
            if grid is not None:
                cols = grid.findall(qn('w:gridCol'))
                ws = [int(c.get(qn('w:w')) or 0) for c in cols]
                tot = sum(ws)
                if tot > int(text_w * 1.05) and tot > 0:
                    override = (grid_overrides or {}).get(i + 1)
                    if override and len(override) == len(cols):
                        s = text_w / float(sum(override))
                        new = [max(300, int(w * s)) for w in override]
                        for c, w in zip(cols, new):
                            c.set(qn('w:w'), str(w))
                        for r in tbl.findall(qn('w:tr')):
                            tcs = r.findall(qn('w:tc'))
                            for j, tc in enumerate(tcs):
                                tcPr = tc.find(qn('w:tcPr'))
                                if tcPr is None:
                                    continue
                                tcw = tcPr.find(qn('w:tcW'))
                                if tcw is None or (tcw.get(qn('w:type')) or 'dxa') != 'dxa':
                                    continue
                                span = tcPr.find(qn('w:gridSpan'))
                                k = int(span.get(qn('w:val'))) if span is not None else 1
                                w = sum(new[j:j + k]) if j + k <= len(new) else new[j]
                                tcw.set(qn('w:w'), str(w))
                        tw = tblPr.find(qn('w:tblW'))
                        if tw is not None:
                            tw.set(qn('w:w'), str(text_w))
                            tw.set(qn('w:type'), 'dxa')
                        acts.append('grid-override:%d->%s' % (tot, new))
                    elif tot > text_w * 2:
                        # 超过版心 2 倍不是"略微溢出"，而是列宽数据被复制污染
                        # （典型形态：从两列表拷来，后几列全等于同一个 5803）。
                        # 等比缩放后首列仍会被压成一字宽，必须人工指定列宽 -> 只报不改。
                        acts.append('grid-corrupt:%d(需人工指定列宽)' % tot)
                    else:
                        scale = text_w / float(tot)
                        for c, w in zip(cols, ws):
                            c.set(qn('w:w'), str(max(300, int(w * scale))))
                        for tcw in tbl.findall('.//' + qn('w:tcW')):
                            if (tcw.get(qn('w:type')) or 'dxa') != 'dxa':
                                continue
                            try:
                                v = int(tcw.get(qn('w:w')) or 0)
                            except (TypeError, ValueError):
                                continue
                            if v:
                                tcw.set(qn('w:w'), str(max(300, int(v * scale))))
                        tw = tblPr.find(qn('w:tblW'))
                        if tw is not None:
                            tw.set(qn('w:w'), str(text_w))
                            tw.set(qn('w:type'), 'dxa')
                        acts.append('grid:%d->%d' % (tot, text_w))
        if acts:
            res[i + 1] = acts
            if verbose:
                print('  表%d: %s' % (i + 1, ', '.join(acts)))
    return res


def audit_table_geometry(doc, first_cell_text='文件编号'):
    """只读体检：返回 {表号: [问题]}，供 dod-checklist 的表格项核对。"""
    etxt = lambda el: ''.join(t.text or '' for t in el.iter(qn('w:t')))
    kids = list(doc.element.body.iterchildren())
    cover_tbl = next((c for c in kids
                      if c.tag.split('}')[-1] == 'tbl' and first_cell_text in etxt(c)), None)
    sec = doc.sections[0]
    lm = sec.left_margin.twips
    text_w = sec.page_width.twips - lm - sec.right_margin.twips
    bad = {}
    for i, t in enumerate(doc.tables):
        tbl = t._tbl
        tblPr = tbl.find(qn('w:tblPr'))
        p = []
        if tblPr is not None:
            ind = tblPr.find(qn('w:tblInd'))
            if ind is not None and (int(ind.get(qn('w:w')) or 0) < 0):
                p.append('负 tblInd=%s' % ind.get(qn('w:w')))
            if tblPr.find(qn('w:tblpPr')) is not None and tbl is not cover_tbl:
                e = tblPr.find(qn('w:tblpPr'))
                x = int(e.get(qn('w:tblpX')) or 0)
                p.append('正文表仍浮动(tblpX=%d, 左页边距=%d%s)'
                         % (x, lm, ', 已压进页边距' if x < lm else ''))
            b = tblPr.find(qn('w:tblBorders'))
            le = b.find(qn('w:left')) if b is not None else None
            tbl_left_ok = le is not None and (le.get(qn('w:val')) or '').lower() not in ('none', 'nil', 'hidden')
            # 表级左边框缺失本身不等于看不见：首列单元格自带单线时渲染正常，
            # 只有"表级无 + 首列也没有"才是真的丢边框，避免误改 20 张正常表。
            first_col_has = False
            for r in tbl.findall(qn('w:tr')):
                tcs = r.findall(qn('w:tc'))
                if not tcs:
                    continue
                tcPr = tcs[0].find(qn('w:tcPr'))
                cb = tcPr.find(qn('w:tcBorders')) if tcPr is not None else None
                if cb is None:
                    continue
                e = cb.find(qn('w:left'))
                v = (e.get(qn('w:val')) or '').lower() if e is not None else ''
                if e is None or v in ('single', 'thick', 'double', 'dotted', 'dashed'):
                    first_col_has = True
                    break
            # §51 规则 D：表级与样式都没有任何可见框线的，是设计上无框线的表，不是缺陷
            other_sides = [x for x in ('right', 'top', 'bottom', 'insideH', 'insideV')
                           if b is not None
                           and b.find(qn('w:' + x)) is not None
                           and (b.find(qn('w:' + x)).get(qn('w:val')) or '').lower()
                           not in ('', 'none', 'nil', 'hidden')]
            if not tbl_left_ok and not first_col_has:
                if other_sides or nilc:
                    p.append('左边框真缺失（该表其他边有框线，唯独左边没有）')
                else:
                    p.append('整表无框线（设计上无网格，不补线）')
            elif not tbl_left_ok:
                p.append('表级左边框缺失（首列单元格有单线，视觉正常，仅提示）')
        nilc = 0
        for tcPr in tbl.findall('.//' + qn('w:tcPr')):
            cb = tcPr.find(qn('w:tcBorders'))
            if cb is None:
                continue
            e = cb.find(qn('w:left'))
            if e is not None and (e.get(qn('w:val')) or '').lower() in ('nil', 'none', 'hidden'):
                nilc += 1
        if nilc:
            p.append('%d 个单元格左边框被设为 nil' % nilc)
        grid = tbl.find(qn('w:tblGrid'))
        if grid is not None:
            tot = sum(int(c.get(qn('w:w')) or 0) for c in grid.findall(qn('w:gridCol')))
            if tot > int(text_w * 1.05):
                p.append('列宽和 %d > 版心 %d（首列会被压窄、整表溢出）' % (tot, text_w))
        if p:
            bad[i + 1] = p
    return bad


LEAD_IN_RE = re.compile(r'(如下所示|如下图所示|如右图|见下图|见上图|见图|见表)')


def _run_font_of(p_el):
    """段落第一个"有文字"的 run 的字体/字号/加粗（同档内比对用，不解析样式链）。"""
    for r in p_el.findall(qn('w:r')):
        if not ''.join(t.text or '' for t in r.iter(qn('w:t'))).strip():
            continue
        rPr = r.find(qn('w:rPr'))
        out = {}
        if rPr is None:
            return out
        rf = rPr.find(qn('w:rFonts'))
        if rf is not None:
            out['ea'] = rf.get(qn('w:eastAsia'))
            out['latin'] = rf.get(qn('w:ascii'))
        e = rPr.find(qn('w:sz'))
        out['sz'] = e.get(qn('w:val')) if e is not None else None
        b = rPr.find(qn('w:b'))
        out['bold'] = (b is not None
                       and (b.get(qn('w:val')) or '1') not in ('0', 'false'))
        return out
    return {}


def _cover_end_index(doc, first_cell_text='文件编号'):
    kids = list(doc.element.body.iterchildren())
    for k, c in enumerate(kids):
        if c.tag.split('}')[-1] == 'tbl' and first_cell_text in ''.join(
                t.text or '' for t in c.iter(qn('w:t'))):
            return k
    return len(kids)


def heading_format_profile_from(doc, levels=(0, 1, 2), first_cell_text='文件编号'):
    """从参照文档统计正文区各级标题的"多数派"格式 -> {级别: {sz,ea,latin,bold,votes}}。

    取多数派而非首段或平均值：参照文档自身常有一两段偏离（实测某份 22 段一致、1 段漏加粗），
    多数派才能把这些也纠正过来。封面区与引导句都不参与投票。
    """
    S = _style_outline_map(doc)
    kids = list(doc.element.body.iterchildren())
    cover_end = _cover_end_index(doc, first_cell_text)
    votes = {}
    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p' or i < cover_end:
            continue
        lv = effective_outline(c, S)
        if lv not in levels:
            continue
        t = ''.join(x.text or '' for x in c.iter(qn('w:t'))).strip()
        if not t or LEAD_IN_RE.search(t):
            continue
        f = _run_font_of(c)
        key = (f.get('sz'), f.get('ea'), f.get('latin'), f.get('bold'))
        votes.setdefault(lv, {})
        votes[lv][key] = votes[lv].get(key, 0) + 1
    prof = {}
    for lv, d in votes.items():
        if not d:
            continue
        k = max(d, key=lambda x: d[x])
        prof[lv] = {'sz': k[0], 'ea': k[1], 'latin': k[2], 'bold': k[3], 'votes': d[k],
                    'total': sum(d.values())}
    return prof


def normalize_heading_format(doc, profile, levels=(0, 1, 2), first_cell_text='文件编号',
                             demote_lead_in=True, also_style=True):
    """把正文区各级标题统一到 profile 的字号/字体/加粗。

    profile 由 heading_format_profile_from(参照文档) 得到，形如
    {0: {'sz':'24','ea':'宋体','latin':'Times New Roman','bold':True}, 1: {...}, 2: {...}}

    四条硬护栏：
      1. 只动封面表之后的段落。封面大标题也是 outlineLvl=0（实测 sz=72），
         不排除会被一起压成正文号，七份封面同时毁掉。
      2. 跳过目录域内段落（含 fldChar/instrText 或 TOC/目录 样式）：改了会与正文标题不一致。
      3. 跳过表格内段落（只遍历 body 直接子级，天然满足）。
      4. 引导句（"××如下图所示："）被误标成标题级时降级为正文级，而不是给它套标题格式。
    also_style 同时改 heading 1/2/3 样式的默认字号，避免 Word 保存时按样式回涨（§13）。
    """
    S = _style_outline_map(doc)
    body = doc.element.body
    kids = list(body.iterchildren())
    cover_end = _cover_end_index(doc, first_cell_text)

    def in_field(el):
        if el.findall('.//' + qn('w:fldChar')) or el.findall('.//' + qn('w:instrText')):
            return True
        st = el.find('.//' + qn('w:pStyle'))
        sid = st.get(qn('w:val')) if st is not None else ''
        return S.get(sid, ('',))[0].startswith(('TOC', '目录'))

    def set_rPr(rPr, spec):
        rf = rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts')
            rPr.insert(0, rf)
        for a in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
            if rf.get(qn('w:' + a)) is not None:
                del rf.attrib[qn('w:' + a)]
        for a, v in (('w:ascii', spec.get('latin')), ('w:hAnsi', spec.get('latin')),
                     ('w:eastAsia', spec.get('ea')), ('w:cs', spec.get('latin'))):
            if v:
                rf.set(qn(a), v)
        for tag in ('w:sz', 'w:szCs'):
            v = spec.get('sz')
            if v:
                e = rPr.find(qn(tag))
                if e is None:
                    e = OxmlElement(tag)
                    rPr.append(e)
                e.set(qn('w:val'), str(v))
        bold = spec.get('bold')
        if bold is not None:
            for tag in ('w:b', 'w:bCs'):
                e = rPr.find(qn(tag))
                if bold:
                    if e is None:
                        e = OxmlElement(tag)
                        rPr.append(e)
                    if qn('w:val') in e.attrib:
                        del e.attrib[qn('w:val')]
                elif e is not None:
                    rPr.remove(e)

    changed = {lv: 0 for lv in levels}
    demoted = []
    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p' or i < cover_end:
            continue
        lv = effective_outline(c, S)
        if lv not in levels:
            continue
        t = ''.join(x.text or '' for x in c.iter(qn('w:t'))).strip()
        if not t or in_field(c):
            continue
        if demote_lead_in and LEAD_IN_RE.search(t):
            pPr = c.get_or_add_pPr()
            e = pPr.find(qn('w:outlineLvl'))
            if e is None:
                e = OxmlElement('w:outlineLvl')
                pPr.append(e)
            e.set(qn('w:val'), '9')
            demoted.append(t[:24])
            continue
        spec = profile.get(lv)
        if not spec:
            continue
        for r in c.findall(qn('w:r')):
            if not ''.join(x.text or '' for x in r.iter(qn('w:t'))).strip():
                continue
            rPr = r.find(qn('w:rPr'))
            if rPr is None:
                rPr = OxmlElement('w:rPr')
                r.insert(0, rPr)
            set_rPr(rPr, spec)
        pPr = c.find(qn('w:pPr'))
        if pPr is not None:
            prPr = pPr.find(qn('w:rPr'))
            if prPr is None:
                prPr = OxmlElement('w:rPr')
                pPr.append(prPr)
            set_rPr(prPr, spec)
        changed[lv] += 1

    if also_style:
        want = {0: 'heading 1', 1: 'heading 2', 2: 'heading 3'}
        for s in doc.styles.element.findall(qn('w:style')):
            nm = s.find(qn('w:name'))
            n = nm.get(qn('w:val')) if nm is not None else ''
            lv = next((k for k, v in want.items() if v == n), None)
            if lv is None or lv not in profile:
                continue
            rPr = s.find(qn('w:rPr'))
            if rPr is None:
                rPr = OxmlElement('w:rPr')
                s.append(rPr)
            set_rPr(rPr, profile[lv])

    return {'changed': changed, 'demoted_lead_in': demoted}



def _style_sz_chain(doc, sid):
    """沿 basedOn 链找样式自带字号（§34：值常在样式里而不在段落自己手上）。"""
    raw = {st.get(qn('w:styleId')): st for st in doc.styles.element.findall(qn('w:style'))}
    seen = 0
    while sid and sid in raw and seen < 8:
        e = raw[sid].find('.//' + qn('w:sz'))
        if e is not None:
            return e.get(qn('w:val'))
        bo = raw[sid].find(qn('w:basedOn'))
        sid = bo.get(qn('w:val')) if bo is not None else None
        seen += 1
    return None


def _effective_sz(p_el, doc):
    """段落生效字号：run 显式值 > 样式链 > Normal。Word 刷新目录时会把等价的 run 级字号
    归并进样式（§13），只读 run 会误判成"没有字号"，闸门必须走这条链。"""
    for r in p_el.findall(qn('w:r')):
        if not ''.join(t.text or '' for t in r.iter(qn('w:t'))).strip():
            continue
        rPr = r.find(qn('w:rPr'))
        if rPr is not None:
            e = rPr.find(qn('w:sz'))
            if e is not None:
                return e.get(qn('w:val'))
        break
    pPr = p_el.find(qn('w:pPr'))
    st = pPr.find(qn('w:pStyle')) if pPr is not None else None
    sid = st.get(qn('w:val')) if st is not None else None
    v = _style_sz_chain(doc, sid)
    if v:
        return v
    for s_ in doc.styles.element.findall(qn('w:style')):
        nm = s_.find(qn('w:name'))
        if nm is not None and nm.get(qn('w:val')) == 'Normal':
            e = s_.find('.//' + qn('w:sz'))
            return e.get(qn('w:val')) if e is not None else None
    return None

def check_heading_tiers(doc, body_sz=None, levels=(0, 1, 2), first_cell_text='文件编号'):
    """§10.5 跨档闸门：各级标题字号必须互不相同、严格递减，且章标题必须大于正文。

    只查"每级只剩一种取值"的闸门查不出"三级挤在同一档"这种退化——
    把 L1/L2/L3 全压成正文号时闸门全绿，但层级感已经消失。返回 (ok, 说明列表)。
    """
    S = _style_outline_map(doc)
    kids = list(doc.element.body.iterchildren())
    cover_end = _cover_end_index(doc, first_cell_text)
    per = {}
    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p' or i < cover_end:
            continue
        lv = effective_outline(c, S)
        if lv not in levels:
            continue
        t = ''.join(x.text or '' for x in c.iter(qn('w:t'))).strip()
        if not t or LEAD_IN_RE.search(t):
            continue
        if c.findall('.//' + qn('w:fldChar')) or c.findall('.//' + qn('w:instrText')):
            continue
        sz = _effective_sz(c, doc)
        if sz:
            per.setdefault(lv, set()).add(int(sz))
    notes = []
    ok = True
    if body_sz is None:
        for s_ in doc.styles.element.findall(qn('w:style')):
            nm = s_.find(qn('w:name'))
            if nm is not None and nm.get(qn('w:val')) == 'Normal':
                e = s_.find('.//' + qn('w:sz'))
                if e is not None:
                    body_sz = int(e.get(qn('w:val')))
                break
    for lv in levels:
        v = per.get(lv)
        if v is None:
            continue
        if len(v) > 1:
            ok = False
            notes.append('L%d 内部多档 %s' % (lv + 1, sorted(v)))
    got = {lv: sorted(per[lv])[-1] for lv in levels if per.get(lv)}
    seq = [got[lv] for lv in levels if lv in got]
    if any(a <= b for a, b in zip(seq, seq[1:])):
        ok = False
        notes.append('各级未严格递减: %s（全级别同字号=层级不可辨，见 §10.5）' % seq)
    if body_sz and seq and seq[0] <= body_sz:
        ok = False
        notes.append('章标题 %s <= 正文 %s，与正文同号' % (seq[0], body_sz))
    return ok, notes or ['各级成档: %s，正文 %s' % (seq, body_sz)]


NUM_MECH_HAND = '手写'
NUM_MECH_STYLE_AUTO = '自动-样式'
NUM_MECH_PARA_AUTO = '自动-段落'
NUM_MECH_NONE = '无编号'


def _style_has_numpr(doc, sid):
    raw = {st.get(qn('w:styleId')): st for st in doc.styles.element.findall(qn('w:style'))}
    seen = 0
    while sid and sid in raw and seen < 8:
        if raw[sid].find('.//' + qn('w:numPr')) is not None:
            return True
        bo = raw[sid].find(qn('w:basedOn'))
        sid = bo.get(qn('w:val')) if bo is not None else None
        seen += 1
    return False


def heading_numbering_mechanisms(doc, levels=(0, 1, 2), first_cell_text='文件编号'):
    """按级别统计标题的编号机制三态 -> {级别: {机制: 段数}}，并给出混用清单。

    三态：
      手写        序号写在文字里（`1.1 编写目的`、`第X章 …`）
      自动-样式    文字里没有序号，编号来自 pStyle 沿链的 w:numPr
      自动-段落    文字里没有序号，编号来自段落自己的 w:pPr/w:numPr（numId 非 0）
      无编号      三者皆无（如"概述""用户界面和体验"这类靠样式或纯文字的章名）

    返回 (per_level, mixed)；mixed = [(级别, {机制: 段数}), ...] 只含"同级别出现 2 种以上
    编号机制"的级别。**即使当前渲染完全正确、没有 §8 的双编号，混用本身也是一致性缺陷**：
    插删一章时只有自动那部分会重排，手写的不会跟着变，编号当场断裂。
    """
    S = _style_outline_map(doc)
    kids = list(doc.element.body.iterchildren())
    cover_end = _cover_end_index(doc, first_cell_text)
    per = {}
    for i, c in enumerate(kids):
        if c.tag.split('}')[-1] != 'p' or i < cover_end:
            continue
        t = ''.join(x.text or '' for x in c.iter(qn('w:t'))).strip()
        if not t:
            continue
        if c.findall('.//' + qn('w:fldChar')) or c.findall('.//' + qn('w:instrText')):
            continue                       # 目录域条目文字里自带序号与页码，不参与判定
        lv = effective_outline(c, S)
        if lv not in levels:
            continue
        pPr = c.find(qn('w:pPr'))
        np_ = pPr.find(qn('w:numPr')) if pPr is not None else None
        nid = np_.find(qn('w:numId')) if np_ is not None else None
        own = nid is not None and (nid.get(qn('w:val')) or '0') != '0'
        st = pPr.find(qn('w:pStyle')) if pPr is not None else None
        sid = st.get(qn('w:val')) if st is not None else None
        sty = _style_has_numpr(doc, sid) if sid else False
        hand = bool(re.match(r'^(\s*(第\s*[0-9一二三四五六七八九十百]+\s*[章节篇])'
                             r'|\d+(\.\d+)*[\s.、])', t))
        if hand:
            mech = NUM_MECH_HAND
        elif sty:
            mech = NUM_MECH_STYLE_AUTO
        elif own:
            mech = NUM_MECH_PARA_AUTO
        else:
            mech = NUM_MECH_NONE
        per.setdefault(lv, {}).setdefault(mech, 0)
        per[lv][mech] += 1
    mixed = [(lv, m) for lv, m in sorted(per.items())
             if len([k for k in m if k != NUM_MECH_NONE]) > 1]
    return per, mixed
