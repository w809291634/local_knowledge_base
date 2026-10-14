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
soffice --headless --convert-to pdf --outdir out "输出.docx"
```

> LibreOffice 同一实例并发转换会失败/卡死：**一次一份**，必要时先杀掉 `soffice*` 进程。