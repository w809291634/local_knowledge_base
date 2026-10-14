# -*- coding: utf-8 -*-
"""
docx_ops —— Word 文档「模板就地替换」通用原语库
================================================
本模块只提供**可复用的原子操作**，不含任何项目数据。
项目差异全部通过参数 / 配置传入，从而保证「相同代码只写一份」。

依赖：python-docx
"""
import copy
import os

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
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