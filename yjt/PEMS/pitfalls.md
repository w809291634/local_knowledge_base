# 环境与格式坑（通用）

> 处理 Word 文档族时反复会遇到的工具/格式问题，与具体项目无关。

## 结论先行

四个高频坑：**① 老旧 `.doc` 会被 Word 以「检测到问题」拒开**（换 WPS 转出）；
**② LibreOffice 并发/复用实例会失败或卡死**（一次一份 + 先杀进程）；
**③ 清理空段时残留的 `bookmarkEnd` 会让循环提前 `break`**（非段落元素要 `continue`）；
**④ 图片内容脚本读不到**（只能人工核对，图上可能还带着旧项目文字）。

## 1. 打不开的 `.doc`

```python
import win32com.client as w
for prog in ('Word.Application', 'KWPS.Application'):   # 先 Word，失败退 WPS
    try:
        app = w.Dispatch(prog); app.Visible = False; app.DisplayAlerts = 0
        d = app.Documents.Open(src, ReadOnly=True)
        d.SaveAs2(dst, FileFormat=16)   # 16 = .docx
        d.Close(False); app.Quit(); break
    except Exception:
        continue
```

## 2. LibreOffice 转 PDF

```powershell
# 不要终止用户正在使用的 soffice 进程；为本次自动化任务创建独立用户配置目录。
$profile = Join-Path $env:TEMP ("pems_lo_" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $profile | Out-Null
soffice --headless "-env:UserInstallation=file:///$($profile -replace '\\','/')" --convert-to pdf --outdir OUT "file.docx"   # 一次一份
```

- 现象：一批命令里连续转多份 → 只成功第一份；卡死后只留 `lu*.tmp` 锁文件。
- 别死循环重试：改用 PDF 文本抽取做结构核对，或直接看 XML。

### 兜底：改用 Word COM 只读导出（LibreOffice 持续卡死时）

本轮实测 LibreOffice 连续卡死（隔离 profile、清锁文件都无效），**改用 Word COM 导出 PDF 成功且稳定**：

```python
import win32com.client as w
app = w.Dispatch('Word.Application'); app.Visible = False; app.DisplayAlerts = 0
try:
    d = app.Documents.Open(src, ReadOnly=True)
    print('页数 =', d.ComputeStatistics(2))       # 2 = wdStatisticPages
    d.ExportAsFixedFormat(pdf_out, 17)            # 17 = PDF
    d.Close(False)
finally:
    app.Quit()
```

- 优点：拿到的是**Word 自己的分页**（比 LibreOffice 更接近用户所见）。
- 想取页宽/页高：用 PyMuPDF 读 `page.rect`（`595×842pt = 21×29.7cm`）。
- 只用 `ReadOnly=True` 打开；**不要在用户正开着文件时写回**。

## 3. 遍历 `w:body` 清理时的 `break` 陷阱

```python
for el in list(body):
    if el.tag == qn('w:p'):   ...
    elif el.tag == qn('w:tbl'): break
    else: continue            # ★ bookmarkStart/End 等：跳过而非 break
```

- 反例：非段落元素直接 `break` → 后面的空段漏清 → 封面后多一页空白。

## 4. 图片两种形式都要认

| 形式 | XML | 备注 |
|---|---|---|
| DrawingML | `a:blip` / `w:drawing` | 新式 |
| VML | `w:pict` / `v:shape` / `v:imagedata@r:id` | 老式（模板图常见，必须逐图识别） |

`Paragraph.text` 里**没有图内文字**；沿用旧模板时图上的标注（模式名、部件名、颜色）很可能
还是旧项目的 → 交付前逐图人工看。

> ⚠️ **只认 `a:blip` 会删掉 VML 图**：判定"图片是否被引用"若漏了 `v:imagedata@r:id`，
> 瘦身函数会把仍被 VML 引用的图当孤立件删除（实测 RD-030：media 7→3、4 处引用悬空、丢 4 张图）。
> 另：python-docx 的 nsmap 无 `v` 前缀，写 `qn('v:imagedata')` 会 `KeyError`，须用 Clark 记法。
> 详见 `diagram-generation-and-figure-insertion.md` 第 3.4 节。

## 5. 其他零碎

| 坑 | 说明 |
|---|---|
| `.doc` 与 `.docx` 混放 | 按后缀分流，`.doc` 先转 `.docx` |
| 合并单元格计数 | `row.cells` 对合并区域会重复返回同一 cell，拼文本会重复，写值无碍 |
| 目录（TOC） | 多为「超链接 + `PAGEREF` 域」，替换要**避开含域代码的段落**；域壳破损有三种形态，见 `docx-fields-and-toc-repair.md` |
| 目录后垫片空段 | 「目录 → 正文」之间几十个纯空段是**靠空段顶页**，脆且常顶不准（正文标题掉到目录页），要改成显式分页符 |
| 各节页宽不一致 | 模板可能把某节设成**横向**（`pgSz@orient="landscape"`）→ 后面页宽和前面不同，检测/修法见 `cover-pagination-and-sections.md` 第 6 节 |
| 页眉编号 | 页眉常含 `<编号> <版本>`，换项目时它也要改 |
| 输出目录 | 产物目录独立，避免覆盖源文档与历史版本 |
| 字体/编码 | 中文文档注意 `eastAsia` 字体槽；GBK 文件读写别用 UTF-8 假设 |