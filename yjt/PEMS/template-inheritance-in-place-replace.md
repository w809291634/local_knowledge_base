# 模板继承：以参考文档「就地替换」

> 通用方法。任何「版式固定、内容按项目替换」的 Word 文档族都适用。

## 结论先行

把已定稿的参考文档 `.docx` **当底层文件打开**，只做三件事：
① 替换段落**文字**（保留该段的 `pPr`/`rPr`）；② 替换表格**单元格文字**（保留 `tblPr`/`tblGrid`）；
③ 补齐封面分页。**图片、分节符、目录、页眉页脚一律不动。**

## 1. 动手前先摸清结构

```bash
# 方式一：打印块序列（段落/表格/编号/分节/图形标记）
python - <<'PY'
import docx
from docx.oxml.ns import qn
d = docx.Document("参考文档.docx")
for i, el in enumerate(d.element.body, 1):
    if el.tag == qn('w:p'):
        t = ''.join(n.text or '' for n in el.iter(qn('w:t'))).strip()
        pPr = el.find(qn('w:pPr'))
        f = ''
        if pPr is not None:
            if pPr.find(qn('w:numPr')) is not None: f += 'NUM'      # 自动编号
            if pPr.find(qn('w:sectPr')) is not None: f += 'SECT'    # 分节符
        if el.findall('.//' + qn('w:drawing')) or el.findall('.//' + qn('w:pict')): f += 'IMG'
        print(i, 'P', f, t[:60])
    elif el.tag == qn('w:tbl'):
        print(i, 'TBL rows=%d' % len(el.findall(qn('w:tr'))))
PY
```

关键判断：
- 模板的**小标题常是「直接格式」**（`numPr` + 加粗 + `sz`），不是命名样式 → 必须克隆元素，别套样式名。
- 带 `numPr` 的标题，**文本里不含序号**，序号由编号定义生成 → 替换时只写文字。
- 段落可能含 `w:fldChar`/`w:instrText`（目录 `PAGEREF` 等）→ 此类段落**不要做 run 合并**。

## 2. 原语（实现见 `tools/docx_ops.py`）

| 函数 | 作用 |
|---|---|
| `iter_blocks_xml(doc)` | 打印/返回块序列，用于定位 |
| `find_cover_table(body)` | 按「首格=文件编号」定位封面表 |
| `set_paragraph(p, text, label=None)` | 整段替换；`label` 非空保留首 run 的加粗（「加粗标签+正文」同段） |
| `insert_paragraphs_after(p, texts)` | 段后插入新段（深拷贝该段、去 `numPr`、沿用末 run 的 `rPr`） |
| `fill_table(doc, idx, header_rows, rows, ...)` | 保留表头，按需增删数据行，写单元格 |
| `apply_global_substitutions(p, subs)` | 段内全局词替换（长串在前），跳过含域段落 |

## 3. 必须遵守的四条

1. **按「整段文本」匹配，不按 run 匹配**：Word 会把一句话拆成多个 run，按 run 替换必漏。
2. **长串优先的替换表**：如同时有 `多功能半导体激光治疗仪` 和 `半导体激光治疗仪`，长的放前面。
3. **含域代码的段落不合并 run**（见上）。
4. **产品名/公司代号/编号等，集中进 `config.json`**，不要散落在脚本里。

## 4. 校验闭环

```bash
# 结构：段落数/表格数/分节数/页眉 与模板对比
# 渲染：一次只转一份，抽页首文本核对
soffice --headless --convert-to pdf --outdir out "某份.docx"   # 一次只转一份
# 最后一步：用 Word 只读打开每份产物并记录页数（LibreOffice/python-docx 不报的错 Word 会报）
```

## 5. 以「别的项目的已验收产物」作模板时的三件必做事

复用同族项目的产物当版式模板最省事，但它同时把上游项目的**内容和缺陷**一起带过来：

1. **把上游项目的事实列成禁用词表，全文扫描**（正文 + 表格 + 文本框 + 页眉页脚，用
   `iter(qn('w:t'))`，`paragraph.text` 会漏报）。命中即阻断交付——这样"他项目残留"从人工目测
   变成机器可判定项。禁用词表本身属于项目配置，不进经验库。
2. **逐份去同义重复段**：上游若用"承接旧稿 + 插入新段"的方式生成，常留下两段几乎同义的句子
   （两版"目的：…"、两版"设计准则：…"）。删除键要用**只有重复段才命中的尾串**精确匹配；
   两段文字完全相同时用 keep-first-only（首次保留、后续删除），否则一段都留不下。
3. **补齐上游模板缺的章节**，而不是照抄它的章节号。模板缺 1.6/1.7 却直接跳 1.8 时，
   克隆标题段补进去——注意克隆段带 `numPr` 会造出"1.6. 1.6 xxx"双编号并顶偏后续章节号，
   标题段保留自动编号、去掉手写序号（详见 `pitfalls.md` 第 8 节）。

> 版式与通用正文可以继承，**事实与结论一律不继承**（`generality-boundaries-and-precedence.md` 第一节）。
> 上游文档里的"通过/符合要求"、签署人、测试日期、样例参数，必须在继承时被清空或改写为中性表述。

## 6. 版式收口

字体字号统一（分区、样式默认值、配图字体一起改）见 `font-and-style-normalization.md`；
它同样要"改生成器 + 改事实文件的 `formatting:` 段"，不要在 Word 里手改产物。