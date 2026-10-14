# Word 域（Field）与目录修复（通用）

> 适用：任何带「自动目录（TOC）+ 页码域（PAGEREF/HYPERLINK）」的公司文档模板族。
> 与具体项目无关；本文结论均来自实测（元良 PEMS `RD-026 / RD-032 / RD-068`，逐份回读 XML 验证）。

## 结论先行

目录"坏了"会表现出**同一个症状**：目录页第一行露出 `TOC \o "1-2" \h \u` 之类的**域指令文字**。
但真因有**三种**，必须先判形态再动手 —— 否则会修错（本文第 4 节的教训就是修错了方向）。

**判定只看 XML，不用渲染**：把全文的 `w:fldChar` / `w:instrText` 按文档顺序拉成一个序列，
看 ① `begin/end` 是否配平、② TOC 指令**有没有被 `begin … separate` 包裹**、③ 目录条目里有没有域。

## 1. 症状 → 三种真因

| 形态 | 结构特征 | 检测判据 | 修法 |
|---|---|---|---|
| **A 未闭合** | 有 `begin`+`instrText`+`separate`，但**缺 `end`** | `begin - end > 0` | 在**目录末条目段落末尾**补 `end`（个数 = 差值） |
| **B 域壳被拍平** | 指令在 `instrText` 里但**前面没有 `begin`**（也没有 `separate`）；或指令直接落在 `w:t` | `toc_has_begin == False` 或 `text_has_toc == True` | 补 `begin`；若指令是 `w:t` 则改名为 `w:instrText`；再补 `separate` 与 `end` |
| **C 目录无域** | 目录条目是纯文本 + 硬编码页码，全文没有 TOC 指令 | `toc_instr == False` 且 `entry_has_field == False` | **只能在 Word/WPS 里重建目录**，脚本别硬造（见第 5 节） |

实测三态（同一批文档三种都占齐了）：

| 文档 | begin/separate/end | toc_has_begin | entry_has_field | 判定 |
|---|---|---|---|---|
| RD-068（修前） | 7/7/**6** | True | True | **A：缺 1 个 `end`** |
| RD-026（V4 原状） | 11/11/11 | True | True | **健康**（结构完整） |
| RD-026（经 Word 更新域+保存后） | 被拍平 | **False** | True | **B：域壳被拍平，指令变可见文字** |
| RD-032 | 0/0/0 | False | **False** | **C：纯文本目录，无超链接** |

> ⚠️ `begin == end` **不代表正常**：形态 B 可能是平衡的（每个 `PAGEREF`/`HYPERLINK` 自带 begin/end，
> 而外层 TOC 连 `begin` 都没有）。**必须再查 `toc_has_begin` / `text_has_toc`。**

## 2. 诊断代码（`tools/docx_ops.py:toc_diagnose`）

```python
from docx.oxml.ns import qn
from collections import Counter

def toc_diagnose(doc):
    body = doc.element.body
    seq = []                                   # 按文档顺序拉平
    for el in body.iter():
        if el.tag == qn('w:fldChar'):   seq.append(('fld', el.get(qn('w:fldCharType'))))
        elif el.tag == qn('w:instrText'): seq.append(('instr', el.text or ''))
        elif el.tag == qn('w:t'):       seq.append(('t', el.text or ''))
    c = Counter(v for k, v in seq if k == 'fld')
    pos = [i for i, (k, v) in enumerate(seq) if k == 'instr' and 'TOC' in v]
    has_begin = has_sep = False
    if pos:
        i = pos[0]
        depth = 0
        for j in range(i - 1, -1, -1):         # 向前找"未被闭合的 begin"
            k, v = seq[j]
            if k == 'fld' and v == 'end':   depth += 1
            elif k == 'fld' and v == 'begin':
                if depth == 0: has_begin = True; break
                depth -= 1
        for j in range(i + 1, len(seq)):       # 向后找 separate（到首个 end 为止）
            k, v = seq[j]
            if k == 'fld' and v == 'separate': has_sep = True; break
            if k == 'fld' and v == 'end':      break
    tocs = [i for i, p in enumerate(doc.paragraphs)
            if (p.style.name or '').lower().startswith('toc')]
    return dict(balance=c.get('begin',0)-c.get('end',0), has_begin=has_begin, has_sep=has_sep,
                has_instr=bool(pos), text_has_toc=any('TOC' in v for k,v in seq if k=='t'),
                entry_has_field=any(doc.paragraphs[i]._p.findall('.//'+qn('w:fldChar')) for i in tocs))
```

## 3. 修法（补壳）

```python
def _fld(type_):
    r = OxmlElement('w:r'); fc = OxmlElement('w:fldChar')
    fc.set(qn('w:fldCharType'), type_); r.append(fc); return r

# A：缺 end → 目录末段落末尾补足
last = doc.paragraphs[max(toc_indices)]
for _ in range(begin - end): last._p.append(_fld('end'))

# B：补 begin +（必要时把 w:t 转 instrText）+ separate
r.addprevious(_fld('begin')); r.addprevious(instr_run); r.addprevious(_fld('separate'))
```

## 4. ★ 教训：「更新目录」会重写域壳，修完必须回读复诊

**实测（RD-026）**：V4 的 TOC 域**本来是健康的**（`begin + instrText + separate` + 嵌套 `HYPERLINK`，
`begin/end` 配平）。我用 Word 执行「更新目录 → 更新域 → 保存」后：

- 外层 `begin` / `separate` 与嵌套的 `HYPERLINK` 域**一起消失**；
- TOC 指令**变成可见文本**（渲染出来就是目录第一行那段 `TOC \o "1-2" \h \u`）；
- 也就是说：**刷新页码这一步本身把域壳拍平了**。

→ 补充实测细节：**同一份文件补齐域壳后再刷新一次，没有再被拍平**（复诊通过）。
也就是说 **Word 重写域结构的后果无法预知**，可能拍平也可能不动 —— 所以「刷新后必须复诊」是硬性要求。

**正确顺序**：**先修复域壳 → 用 Word 刷新（F9/更新目录）→ 再回读复诊 → 复诊不通过就再补壳**，
**绝不能"刷新完就直接交付"**（我上一轮就是漏了最后这一步，才把健康文档弄坏）。

排查口诀：**改完域 → `toc_diagnose()` 过 → 渲染 PDF 看目录首行没有 `TOC \o` → 才算完。**

## 5. 形态 C：目录无域，只能重建（别硬造）

不要用脚本给纯文本目录硬塞 `PAGEREF` —— **书签字形（`_Toc8001` / `_Toc2670` …）与条目顺序不保证对应**，
造错会变成"错误！未定义书签"。正确做法是**在 Word/WPS 里重建**：引用 → 目录 → 自动目录
（或 COM 的 `TablesOfContents.Add`）；前提是正文小标题确实用了 Heading 样式，否则自动目录会抓不到标题。

## 6. 刷新页码（必做）

```python
import win32com.client as w
app = w.Dispatch('Word.Application'); app.Visible = False; app.DisplayAlerts = 0
d = app.Documents.Open(path)
for i in range(1, d.TablesOfContents.Count + 1): d.TablesOfContents(i).Update()
d.Fields.Update(); d.Save(); d.Close(False); app.Quit()
```

等价于 Word 里按 F9 /「更新目录」。**注意第 4 节：这一步可能拍平域壳，之后必须复诊。**

## 7. 禁忌

- **不要对含 `fldChar`/`instrText` 的段落做 run 合并或整体重写文本**（会把域拍平成普通文字）。
- **删"空段"时要排除含 `fldChar` 的段落**：只按"文本为空"判断，会把只含域标记的空段落删掉，直接弄坏域
  （与"删封面区空段"同一陷阱的变种）。
- **不要试图用脚本重算 `PAGEREF` 的结果值**。
- 补 `end` 只补外层，别动成对闭合的内层 `PAGEREF`/`HYPERLINK`。

## 8. 一句话

**域问题一律「先判形态（A 缺 end／B 壳被拍平／C 无域）→ 只补壳 → 交给 Word 刷新 → 回读复诊」**；
目录无域的只能重建，别硬造。
