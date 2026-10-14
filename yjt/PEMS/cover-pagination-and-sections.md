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

## 5. 验证

```python
import fitz
d = fitz.open("out.pdf")
print(d.page_count)
for i in range(min(3, d.page_count)):
    print(i + 1, d[i].get_text().strip().replace("\n", " ")[:80])
# 期望：p1 只有封面字段；p2 目录；p3 正文首节；不存在仅有页眉页脚的空页
```