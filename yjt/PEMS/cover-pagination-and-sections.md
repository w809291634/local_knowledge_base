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

## 6. 各节页面尺寸与格式档案一致

**现象**：后续页面宽度、方向或页边距与预期不符。

**原则**：不能要求所有分节与第一页完全相同。横向宽表、附录、图页或封面可能是模板有意设置；每一节应当与当前模板格式档案中登记的页面尺寸、方向和页边距一致。

**检测**（逐节读取 `pgSz` 与 `pgMar`，再与模板档案对比）：

```python
for i, s in enumerate(doc.sections):
    e = s._sectPr; sz = e.find(qn('w:pgSz')); mar = e.find(qn('w:pgMar'))
    print(i + 1, sz.get(qn('w:w')), sz.get(qn('w:h')), sz.get(qn('w:orient')),
          mar.get(qn('w:left')), mar.get(qn('w:right')))
```

**处理**：

- 若模板档案规定该节为纵向，输出被意外改成横向或页边距变化，则按模板恢复；
- 若模板档案规定该节横向，用于宽表或宽图，则保留横向并检查表格/图示未裁切；
- 未建立格式档案时，不得擅自以第一页覆盖其余分节；应先确定每节的预期格式。
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
> **更新（§23/§39 之后）**：本节"处理"里的 `normalize_toc_page_break` 用**插入 `w:br type=page`** 收拢垫片空段，
> 与 §23「用 `w:pageBreakBefore`、不要插 `w:br type=page`」和 §39「两者叠加＝多一张空白页」冲突。
> 现行做法：删垫片空段后，把分页写在**正文首标题段的 `pageBreakBefore`** 上，不再插 `w:br`。
> 该函数仍可用于"只删垫片、加分页交回 `pagination_repair`"的场景；直接沿用其旧行为会把 §39 的缺陷重新造出来。

> **更新（§41 之后）**：本节 §7 的验证用 `get_text()` 断言页内容，中文 PDF 缺 ToUnicode 时会**整页取不到字**，
> 断言会假通过或假失败。空白页与"该页有没有正文"一律改用 `page_ink_coverage` + `grade_pages_by_ink`；
> `get_text()` 只用于确认"某页是否出现了不该出现的字符串"，且要先确认该 PDF 有 ToUnicode。

## 8. 空白页 / 段前"冒点"的定位—修复—复验流程（五步，缺一环就返工）

**适用症状**：正文里莫名多一张空白页；某段前面冒出一个点、看起来"变成了标题"；页码跳号；目录页码与实际不符。
这类缺陷的共同特点是**逐段看 XML 每一处都"合理"**，只有渲染出来才暴露，所以必须按固定顺序走完五步，不能凭读代码判断。

**第 1 步 先跑判据，不要先改。**
`pagination_audit(doc, cover_texts=[封面文档名])` 一次给出七项：`hard_page_breaks` / `stacked_breaks` /
`body_page_break` / `keep_on_body` / `chapter_pad` / `outline_anomaly` / `numbered_not_in_tree`。
**判据自身要先自证清白**：本轮实测出三个判据缺陷（`w:val="0"` 被当开启、目录域条目被当正文标题、
封面留白被当顶页空段），误报一次就有几十条，真问题会被淹没。所以任何一类报出来后，
**先回到原始 XML 复核其中一处**，确认判据可信，再看全表。

**第 2 步 用渲染定位，不要用文字。**
`page_ink_coverage(pdf)` → `grade_pages_by_ink(cov)`（§41）。哪一页真空白、哪一页疑似顶页，
只有墨占比说得准；`pdftotext` / `get_text()` 在中文 PDF 上不可信。

**第 3 步 查"叠加"，不要查"存在"。**
空白页的根因几乎总是**同一个效果被写了两遍**：段前分页＋段内硬分页符、分节符(NEW_PAGE)＋段前分页、
样式分页＋段落分页。单看每一处都合法，所以要查的是"同时存在"（`stacked_breaks`），
而不是"有没有分页符"。段前冒点同理是**属性写到了不该写的段上**（§38）：
正文级段落带 `keepNext`/`keepLines`，或封面文档名带 `outlineLvl`。

**第 4 步 修复与判据共用同一套函数。**
`pagination_repair(doc, cover_texts=[...], apply=[...])` 直接复用 `pagination_audit` 的判据，
避免"查的是一套、改的是另一套"。原则是**只删多余那一份，保留规范那一份**（一律留 `pageBreakBefore`，
删 `w:br type=page`）；`apply` 收窄到本轮已确认的动作，不要默认全开。
改完立即复跑 `pagination_audit`，七项应全为 0 或空。

**第 5 步 重渲染并核账页数。**
重导 PDF：`len(cov)` 必须等于"修复前页数 − 消除的空白页数"，且 `grade_pages_by_ink` 无阻断项。
再人工看修复点前后各一页——标题是否仍在页首、居中是否被多余制表符顶偏。
**页数没变**＝修复没生效或被 Word 保存回滚；**页数少得比预期多**＝误删了结构段。
两种都必须停下来查，不能当"顺手又排了一版"。

**收尾**：第 1 步的七项判据与第 5 步的墨占比分级已并入 `dod-checklist.md` F 组，
是每轮交付的固定终检项；同批文档不要一份一份手工看，用同一段脚本对全部产物跑一遍并留档。
