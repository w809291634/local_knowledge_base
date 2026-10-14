# -*- coding: utf-8 -*-
"""
docx_ops —— Word 文档「模板就地替换」通用原语库
================================================
本模块只提供**可复用的原子操作**，不含任何项目数据。
项目差异全部通过参数 / 配置传入，从而保证「相同代码只写一份」。

依赖：python-docx
"""
import copy
import hashlib
import os
import struct

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt
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