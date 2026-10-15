# 环境与格式坑（通用）

> 处理 Word 文档族时反复会遇到的工具/格式问题，与具体项目无关。

## 结论先行

四个高频坑：**① 老旧 `.doc` 会被 Word 以「检测到问题」拒开**（换 WPS 转出）；
**② LibreOffice 并发/复用实例会失败或卡死**（一次一份 + 独立用户配置目录）；
**③ 清理空段时残留的 `bookmarkEnd` 会让循环提前 `break`**（非段落元素要 `continue`）；
**④ 图片内容脚本读不到**（只能人工核对，图上可能还带着旧项目文字）。

新增三个"看起来是文档坏了"的坑，共同点是**python-docx 与 LibreOffice 都不报错，只有 Word 拒开**：
**⑥ 往整包无图形部件的模板脚本加图**；**⑦ 孤立媒体清理只扫正文段落**（删掉页眉/文本框在用的图）；
**⑧ 克隆带 `numPr` 的段落**（双编号 + 顶偏后续章节号）。另有 **⑨ 文本框内文字**词替换覆盖不到。
→ 结论：**交付前的最后一道必须是"Word 逐个只读打开"**，不能只靠 LibreOffice 渲染。

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
| 字体/编码 | 中文文档注意 `eastAsia` 字体槽；GBK 文件读写别用 UTF-8 假设（详见 `font-and-style-normalization.md`） |
| 无 PyYAML 环境 | 事实文件仍用 YAML 时，自带一个只支持"两层 key: value + 标量列表 + 内联字典 + 嵌套列表"的极简解析器；解析器要能容忍 `key:` 行后跟行内注释 |
| 上游生成器留下的同义重复段 | 用"承接旧稿 + 插入新段"方式产出的文档，常有两段几乎同义的句子（如两版"目的：…"、两版"设计准则：…"）。下游继承时**必须逐份去重**：删除项按"只有重复段才命中的尾串"精确匹配，同键多次出现用 keep-first-only |
| 控制台中文乱码 | Windows GBK 终端里 `print` 中文是乱码，但**文件本身没坏**；核对内容请写 UTF-8 文件后用编辑器/读文件工具看，别据乱码判断文档出错 |

## 6. 向「整包无图形部件」的模板脚本加图 → Word 判"文件可能已损坏"（最阴的一个）

现象：某模板本身能正常打开（Word/WPS/python-docx 都正常），但用 `doc.add_picture()` 或
`docx_ops.insert_figure_before()` 给它加一张图后，**Word 报"文件可能已经损坏"、LibreOffice 不出 PDF**；
而同一套代码往别的模板加图完全正常。

定位方法（二分，别猜）：

```python
# 1) 只做最小操作：open + add_picture + save，成功即排除"内容改写"因素
# 2) 逐步叠加：段落替换 → 表格 → 封面 → 分页/缩进 → 插图 → 孤立媒体清理
#    每步存一个文件，用 Word COM 只读打开判成败
d = Document('模板.docx'); d.add_picture(png, width=Inches(5.9)); d.save('t_min.docx')
```

判据：包结构看起来**完全正常**（`[Content_Types].xml` 已加 `Default Extension="png"`、
`word/media/image1.png` 在位、rId 不冲突、`w:drawing` 片段与能正常打开的文档逐字节同构）——
即"查不出 XML 毛病但 Word 就是拒开"。

处置（按优先级）：

1. **该模板不自动插图**：把图留在 `figs/`，在 `todo.md` 记"需在 Word/WPS 中人工插入"，其余文档照常批量。
2. 换一份**本来就含图形部件**的同版式模板作供体。
3. 先用 Word 打开模板 → 另存为 `.docx`（补齐 Word 自己的 drawing 上下文）→ 再用脚本插图。

> 教训：闸门必须包含"**Word 逐个打开**"这一条。LibreOffice 与 python-docx 都通过 ≠ Word 能开；
> 评审用的正是 Word。

## 7. 清理孤立媒体部件：判定范围必须是「整包 XML」而不是「正文段落」

`drop_orphan_image_rels` 若只用 `doc.paragraphs` 收集已引用 rId，会把**页眉/页脚/脚注/文本框**
正在用的图判成孤立件删掉 → 保存后 Word 报文档损坏（与第 6 节症状相同，极易误判）。

```python
used = set(正文引用)                                  # 不够！
blob = '\n'.join(part.blob.decode('utf-8','ignore')   # ★ 遍历包内所有 xml/rels 部件
                 for part in doc.part.package.iter_parts()
                 if 'xml' in (part.content_type or ''))
for rid, rel in list(doc.part.rels.items()):
    if 是图片部件 and basename not in used and re.search(r'["/>]%s["]' % rid, blob) is None:
        doc.part.drop_rel(rid)
```

安全网：只有"本轮确实删过旧图"的文档才执行瘦身；日志打印每个被删部件名，删 0 个也要打出来，
便于事后回溯是哪一步引入的损坏。

## 8. 克隆模板段落时，`w:numPr` 会造出双编号并顶偏后续章节号

从模板克隆段落（插新章节、补小节、加图题）时，供体段若带 `numPr`：

- 手写序号 + 自动编号 → 渲染成 `1.6. 1.6 适用范围`；
- 克隆段还会**占用编号序列**，把后续章节的自动编号整体顶偏（原 `1.8` 渲染成 `1.11`）。

分两种处置：

| 克隆用途 | 处置 |
|---|---|
| 正文段 | 去掉 `numPr`（`insert_paragraphs_after` 已内置此逻辑） |
| 标题段 | **保留** `numPr`，并把文本里的手写序号删掉，交给自动编号排号（`1.6 适用范围` 写成 `适用范围`） |

配套检查：渲染后扫描"独占一行的 `\d+(\.\d+)*\.`"，逐个确认是模板正常自动编号还是叠加缺陷；
模板本身在标题里手写了序号（如 `1.4 硬件关系`）而样式又带 `numPr` 时，用槽位把文本改成不含序号，
让自动编号接管，一次修全章。

## 9. 文本框（`w:txbxContent`）里的文字：`p.runs` 取不到，要按 `w:t` 节点改写

`python-docx` 的 `Paragraph.runs` 只含 `w:p` 的直接子 `w:r`；文本框里的 run 深藏在
`w:r → w:pict|mc:AlternateContent → v:textbox → w:txbxContent → w:p` 里，**词替换与整段替换都覆盖不到**，
残留旧项目文字就藏在这些地方（命名规则示意图、示意图标注）。

```python
for t in p._p.iter(qn('w:t')):            # 读：整段（含文本框）全文
    ...
nodes = list(p._p.iter(qn('w:t')))        # 写：按节点位置整段改写
assert len(nodes) == len(new_texts), (len(nodes), len(new_texts))
for t, v in zip(nodes, new_texts):
    t.text = v; t.set(qn('xml:space'), 'preserve')
```

三条注意：① `mc:AlternateContent` 会把同一图形的文字**存两份**（DrawingML + VML 回退），
节点数与替换列表必须按"两份"给，否则只改一半；② 一句话常被拆成 `(`、`M代表…`、`，`、`)` 多个节点，
按整句匹配会落空 → 用"节点位置 + 等长替换表"并校验节点数；③ 残留检查（禁用词扫描）必须用
`iter(qn('w:t'))` 与页眉页脚一起扫，只用 `paragraph.text` 会漏报。


## 10. `run.text = ...` 会连带抹掉同一个 run 里的图形

`python-docx` 给 run 赋文本时是"清空该 run 的其它子节点再写一个 `w:t`"。因此对
含 `w:pict` / `w:drawing`（尤其 VML group 里带 `w:txbxContent` 的表单、示意图）的段落做
整段替换或"合并 run"式词替换，会**把图形一起删掉，且不报任何错**——只在渲染时表现为
"表单没了 / 示意图只剩一行散字"。

```python
if p._p.findall('.//' + qn('w:pict')) or p._p.findall('.//' + qn('w:drawing')):
    substitute_wt_nodes(p, subs)      # 逐 w:t 节点替换，不合并 run
else:
    apply_substitutions(p, subs)
```

槽位确实要改写这种段落时：**先摘图形再换文字**（`_strip_images(p)` → `set_paragraph`），
否则改完的文字带着旧图形，或图形带着旧文字。

## 11. 「承接旧稿 + 插入新段」做块对齐时，空段必须先剔除

模板封面区常有十几个空段。两侧都 `norm()` 成 `''` 后，`difflib` 会把它们当成**大段相同内容**
配对，于是真正的正文被整体判成"新增"并插到封面区——实测症状是**封面整页消失**、目录条目
落到封面表前后。

```python
bi = [(i, norm(t)) for i, t in enumerate(base_texts) if t.strip()]   # ★ 先过滤
vj = [(j, norm(t)) for j, t in enumerate(v6_texts) if t.strip()]
```

配套两条护栏：① **第一个分节符之前不接受任何插入**（封面区）；② 目录域区内（含 `fldChar`
或 `toc` 样式）不接受插入纯文本条目，否则会和自动目录叠成两套。

## 12. Word「更新目录」对模板手工条目结构会**过收**

模板目录若是 `TOC \o "1-2"` + 手工条目（`HYPERLINK` 而非 `PAGEREF`），而正文表格单元格段落
又带着 outline 级别，Word 重新生成会把"测试人：""验证条款"这类表格文字全收进目录
（实测 6 条 → 47 条），目录反而更长更错。

处置：刷新后**比较条目数**，超出阈值就还原刷新前的备份，改为只校正缓存页码：

```python
ok = td1['healthy'] and (ntok0 - 1) <= ntok1 <= ntok0 + 2
if not ok: shutil.copy2(bak, path)      # 宁可用旧页码，也不交一份 47 条的错目录
```

> 与 `docx-fields-and-toc-repair.md` 第 4 节合起来看：**刷新可能拍平域壳，也可能过收**，
> 两种都得复诊；"刷完就交付"从来不成立。

## 13. Word 保存会顺手重写 `styles.xml`，把等价的样式字号规掉

实测：Word 更新目录并保存后，某级标题样式的 `w:sz` 被删（值与 `docDefaults` 等价时 Word 认为冗余）。
视觉可能无差，但产物 XML 不再等于模板版式，且**下一次字体统一会以为样式没设**。

→ 顺序要求：**字体统一 / 样式默认值必须在"目录刷新"之后再跑一遍**，并从刷新前的备份把
各级样式的 `sz` 原值写回。

## 14. 表格重建：列数看 `tblGrid`，克隆行前先去 `vMerge`

- 判现有列数用 `table_grid_cols(tbl)`，**不要用末行 tc 数**——合并单元格会让 tc 数少于列数，
  据此判断会漏调列，产出"表头 5 列、数据行 4 格"的错位表。
- 用末行作样式供体克隆新数据行前必须 `flatten_table_rows()`：带 `vMerge` 的首个新行没有可继承的
  上方 tc，`row.cells` 直接抛 `ValueError: no `tc` element at grid_offset=…`。

## 15. 字体统一的两个"改了不生效"

1. `w:rFonts` 上的 `asciiTheme` / `eastAsiaTheme` / `hAnsiTheme` / `cstheme` **优先级高于显式字体名**，
   不删掉这些属性，写了 `宋体` 也仍按主题渲染。
2. `doc.paragraphs` **不含表格内段落**：只遍历它就以为整份文档统一完了，实测表格里的旧字体
   （上千字）一个都没动。字体与残留扫描都要单独遍历 `doc.tables` 的单元格（合并格去重）。

## 16. 承接与槽位是两条写入轨道，会把同一句话各写一遍

双轨写入（模板原样 + 上一版承接 + 本轮按权威源重写的槽位）必然出现的碰撞：槽位把某段
重写成新表述，承接又把上一版的旧表述落到相邻段落 → 文档里同一内容两遍，而且**两段格式
不同**（一段带模板缩进，一段是本轮新写的空 pPr），读者一眼就看到"这段话重复了、格式还不一样"。

判据必须四条一起用（`tools/para_ops.py:dup_kind`），只用整体相似度必漏：

| 形态 | 例子 | 只按 ratio 的后果 |
|---|---|---|
| `exact` | 上一版一段被承接到两个位置 | 能抓到 |
| `near` | 只差标点／一个连接词 | 能抓到 |
| `same-lead` | 开头"××遵循以下设计准则："相同，后面条目列表不同 | **漏**（列表差异把 ratio 稀释到 0.6 以下） |
| `contained` | 上一版两句合成一句，本轮又拆开写 | **漏**（长度差太大） |

处置：
1. **写前拦**：承接／插入前先与"本轮正文池"（所有槽位新文本 + 槽位自带补充段）比一遍，
   命中就不写；被让路的那个模板段属于被替换内容，要删掉而不是留旧文。
2. **写后扫**：文档末尾再跑一次全量去重，优先级 `本轮正文 > 模板原样 > 上一版承接`，同级留靠前。
3. **两段都是模板原样时禁止自动删**：那是模板自带的并列写法（实测两条"××验证"条目开头相同），
   自动删等于吃正文；只报闸门由人判断，并在配置里用 `dup_allow` 显式声明同族条目。
4. 去重前先确认"本轮正文"是否已覆盖被删段的**独有事实**（工具名、参数、功能项）。实测被删段
   常带"测试工具包括…"这类细节，直接删就是丢信息 —— 正确做法是把细节并进保留段。

## 17. 同一锚点连续插多段，插入函数写错就成了整章倒序

`insert_after_para(anchor, [A, B, C])` 内部用 `el.addnext(new)` 逐段追加时顺序正确；
但如果**每次调用只传一段**（或外层把多段 `list.insert(0, x)` 累积），后插的总排在前面，
整段正文倒序：「概述 → 总体构架 → 模块 → 接口 → 约束」变成「约束 → 接口 → 模块 → …」。
文字都对、内容都不缺，只有顺序反了 —— 逐字校对很容易漏，必须专门设一条顺序检查。

- 累积同锚点的多段一律 `append`，不要 `insert(0, …)`。
- 闸门加一条：承接段（来自上一版的文字）在产物里的先后，必须与它在上一版里的先后一致
  （把上一版段落编号映射到产物段落序号，检查非递减）。
- 顺序错了不能靠"再倒着插一遍"修，要回到累积处修，否则下一次改锚点又会翻。

## 18. 新写段落没带 pPr，就是"内容对了、格式不同"

Word 正文观感来自**段落属性**（首行缩进／行距／对齐）或正文样式，不来自字符格式。本轮新写的
段落有两个来源都不带正文版式：① 槽位命中了模板里的"注：…"批注段（本来就无缩进）；
② 插入函数复制的锚点段自己就没有 pPr。结果是新写的正文贴着页边、上下文却缩进两字符。

三条实测结论：

1. **必须按"生效版式"比对**：`docDefaults → 样式链（basedOn 逐级）→ 段落直接 pPr`。
   只读段落 pPr 会把"样式里已设好缩进、段落不写 pPr"误判成缺格式，于是冤枉模板、乱改一通。
2. **锚点要单向就近**：给每个本轮新写段配"左边最近的模板段（或自己写了 pPr 的段）"作锚点。
   实测两种直觉做法都错 —— "就近互指"在整片都是新写段时 A 抄 B、B 抄 A，几轮都定不下来；
   "±N 多数派"会把模板刻意写了缩进的段拉平成样式默认值，等于新造不一致。
3. **对齐方式：pStyle 双向对齐 + 只抄参照段直接写了的属性**。
   只抄直接 pPr 不够（两段都无 pPr 时差异全在样式：Normal / Default / 自定义正文样式）；
   反过来把参照段的"生效值"全量写成直接属性也不行 —— 正文会冒出一堆模板没有的硬格式，
   用户之后在 Word 里改样式跟不动。

另外：空 `<w:pPr/>` 不算"刻意写了版式"。把它当锚点会让整片缺缩进的段落互相充当参照，
漂移反而检不出来（实测修复前判 0 处、修复后才判出真实数量）。

## 19. 渲染脚本"PDF 已存在就跳过"，逐页核对全部作废

`to_pdf()` 写成 `if os.path.exists(dst): return dst` 后，改完文档再跑渲染，读到的还是上一轮
的 PDF：页数、分页、逐页文字全是旧的，而脚本会正常打印"渲染通过 0 项"。更糟的是**页码补丁
基于旧分页**，目录页码会跟着改错。

- 复用条件必须是 `PDF 不比 docx 旧`（比较 mtime），否则删除重转；交付前再核对一遍
  `pdf/` 与产物 docx 的时间戳关系。
- 管线顺序：生成 → 目录刷新 → **渲染** → 按渲染结果改目录页码 → 再渲染确认页数不变 → 闸门。
  先改页码后渲染，等于拿旧分页改新文档。
- 凡是"能跳过"的缓存，都要问一句：它读的是不是本轮的输入？打印"通过"不等于真的检查过。
