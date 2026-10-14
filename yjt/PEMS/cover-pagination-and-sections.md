# 封面 / 分页 / 分节：三大高风险点（通用）

> 适用：任何「封面 + 目录 + 正文」三段式的公司文档模板。踩坑与排查方法通用。

## 结论先行

封面独立成页靠二者之一：**封面表后的「分节符（下一页）」** 或 **显式分页符**。
二者都没有 → 封面与正文挤在一页；封面区残留**多余空段** → 渲染出**空白页**。

排查顺序：① 封面表后有没有 `sectPr` 或 `w:br type=page`？没有就补；② 之间有没有纯空段？有就删。

## 1. 三种坏形态与处理

| 现象 | 成因 | 处理 |
|---|---|---|
| 封面与正文同页 | 模板封面后无分节符 | 封面表后插分页符 |
| 封面后多一页空白 | 封面区多余空段溢出 | 删空段 |
| 正文页眉丢失 | 删正文时把含 `sectPr` 的段落一起删了 | 含 `sectPr` 的段落**只清 run、保留该段** |

## 2. 封面表多是「浮动表」，别按普通表处理

封面信息表常带 `tblpPr`（绝对定位、锚定文本），**不占正常流高度**：

```xml
<w:tblPr>
  <w:tblpPr w:leftFromText="180" w:rightFromText="180"
            w:vertAnchor="text" w:horzAnchor="margin" w:tblpY="206"/>
```

→ 「封面占多少版面」不能只数段落。克隆表格做内容表时，**保留 `tblPr` 整体**（边框、`tblCellMar`），
只去掉 `tblpPr`。

## 3. 定位与修复（实现见 `tools/docx_ops.py`）

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def find_cover_table(body):            # 首格文本 == '文件编号'
    ...

def ensure_cover_page_break(doc):
    """封面表后无分节符/分页符时补分页符，保证封面独立成页"""
    ...

def trim_cover_spacers(doc):
    """删除封面表与首个正文块之间的纯空段"""
    ...
```

清理空段时的关键细节：**遇到非段落元素（如残留 `bookmarkEnd`）要 `continue` 而不是 `break`**，
否则循环提前结束，空段清不干净，封面后一直多一页空白。

> ⚠️ 另一个变种陷阱：**判"空段"不能只看"文本为空"**。只含域标记（`w:fldChar`）的段落同样没有文本，
> 按"文本为空"把它删掉会**直接弄坏域**（实测：删掉承载 `end` 的空段会让目录域失去闭合，指令裸露）。
> 空段判定要排除含 `w:fldChar` / `w:instrText` 的段落，见 `docx-fields-and-toc-repair.md` 第 7 节。

```python
for el in list(body):
    if el is cover: started = True; continue
    if not started: continue
    if el.tag == qn('w:p'):
        pPr = el.find(qn('w:pPr'))
        if pPr is not None and pPr.find(qn('w:sectPr')) is not None: break
        if ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip(): break
        if el.findall('.//' + qn('w:br')) or el.findall('.//' + qn('w:drawing')): break
        body.remove(el)                # 纯空段 → 删
    elif el.tag == qn('w:tbl'):
        break
    else:
        continue                       # ★ bookmark* 等：跳过，不要 break
```

## 4. 若用脚本「重建正文」（不推荐，但在模板结构不可用时）

- 删正文时，**保留第一个含 `sectPr` 的段落**（清空其文字、保留分节符），其余分节符段落删除；
  否则分节结构丢失、页眉页脚跟着丢。
- 文档末尾的 `body/sectPr`（最后一个）不要动。

## 5. 目录与正文之间必须「显式分页」，禁止靠空段顶页

**现象**：目录页底部挤出正文首标题（如「1. 软件验证和确认过程的描述」），目录页尾大片空白，目录页码全错。

**真因**：模板在「目录末条目 → 正文首标题」之间塞了**几十个纯空段当垫片**（实测 26～44 个），
靠空段把正文"顶"到下一页。字体/行高稍变就顶不准 → 标题掉回目录页。

**处理**：删除全部垫片空段，改为**一个显式分页符**（不改节数，符合"分节数以模板为准"）：

```python
def normalize_toc_page_break(doc, pad_min=5):
    """目录末条目与正文首标题之间的垫片空段 → 1 个显式分页符；返回(删除数, 是否加分页)"""
    ps = doc.paragraphs
    tocs = [i for i, p in enumerate(ps) if (p.style.name or '').lower().startswith('toc')]
    if not tocs:
        return 0, False
    last = max(tocs)
    first_body = None
    for i, p in enumerate(ps):                       # 正文首标题＝带 numPr 的有文字段
        if i <= last: continue
        pPr = p._p.find(qn('w:pPr'))
        if pPr is not None and pPr.find(qn('w:numPr')) is not None and paragraph_text(p).strip():
            first_body = i; break
    if first_body is None:
        return 0, False
    empt = [p for p in ps[last + 1:first_body] if not paragraph_text(p).strip()
            and not p._p.findall('.//' + qn('w:br'))
            and not p._p.findall('.//' + qn('w:drawing'))
            and not p._p.findall('.//' + qn('w:pict'))]
    if len(empt) < pad_min:                          # 少量空段不算"顶页"
        return 0, False
    keep = empt[0]                                   # 第 1 个空段改造成分页符段
    for r in keep._p.findall(qn('w:r')):
        keep._p.remove(r)
    r = OxmlElement('w:r'); br = OxmlElement('w:br'); br.set(qn('w:type'), 'page')
    r.append(br); keep._p.append(r)
    n = 0
    for p in empt[1:]:
        p._p.getparent().remove(p._p); n += 1
    return n, True
```

判据：**目录条目后到正文首个标题之间，纯空段 ≥ 5 个就视为"靠空段顶页"**（1～2 个属正常留白）。

## 6. 各节页面宽度/页边距必须一致

**现象**：用户反馈"**后面的页面宽度不一致**"。

**真因**：模板的**某一节被设成了横向**（`w:pgSz w:orient="landscape"`），例如元良 RD-028：
节1 `11906×16838`（纵向 A4）／节2 `16838×11906`（**横向**）→ 第 2 页起页宽 29.7cm、第 1 页 21cm。

**检测**（逐节比对 `pgSz` 与 `pgMar`）：

```python
for i, s in enumerate(doc.sections):
    e = s._sectPr; sz = e.find(qn('w:pgSz')); mar = e.find(qn('w:pgMar'))
    print(i + 1, sz.get(qn('w:w')), sz.get(qn('w:h')), sz.get(qn('w:orient')),
          mar.get(qn('w:left')), mar.get(qn('w:right')))
# 各节 (w,h,orient) 不一致 → 页宽不一致
```

**处理**：**以第 1 节为基准**统一各节 `pgSz` 与 `pgMar`（通则：封面节通常是标准纵向，用它当基准）。
若某节横向是为了放宽图，则应改**模板**而不是改文档；统一为纵向后要顺带确认宽图没被裁切
（正文宽度 = 页宽 − 左右页边距，超宽要按比例缩放）。

## 7. 验证

```python
import fitz
d = fitz.open("out.pdf")
print(d.page_count)
for i in range(min(3, d.page_count)):
    print(i + 1, d[i].get_text().strip().replace("\n", " ")[:80])
# 期望：p1 只有封面字段；p2 目录；p3 正文首节；不存在仅有页眉页脚的空页

# ★ 再加两项（本轮实测暴露的缺陷）：
for i in range(d.page_count):                    # ① 各页尺寸必须一致
    r = d[i].rect
    print(i + 1, round(r.width, 1), round(r.height, 1))
# ② 目录页首行不得出现裸露域代码（含 "TOC \o" / "PAGEREF" 字样）：
assert 'TOC \\o' not in d[1].get_text(), '目录域壳破损，见 docx-fields-and-toc-repair.md'
# ③ 目录页尾部不得混入正文标题（如 '1. 软件验证和确认过程的描述'）：
assert '1. 软件验证和确认过程的描述' not in d[1].get_text(), '目录与正文未分页'
```