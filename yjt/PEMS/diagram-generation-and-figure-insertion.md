# 配图生成与 Word 插图替换（框图 / 流程图 / 拓扑图）

> 适用：需给 Word 文档配「软件体系架构图、状态图、硬件拓扑图、流程图」的场景（PEMS 的 RD-028/030/052/057 等）。
> 来源：中医封包治疗仪 RD-052 软件描述文档补 9 张图（2026-10-14）。首版图出现「文字压框、元素错位、箭头指错」被退回，本文件是返工后的定稿方法。
> 工具：`tools/fig_tools.py`（绘图原语）+ `tools/docx_ops.py` 的「图片」区块（插图替换与校验）。

## 结论先行

- 图错，八成不是"画得不好"，而是**坐标硬编码**：文字位置手填、箭头端点手填，一旦框大小变了就压框/指错。
- 三条硬规则能一次性消掉重叠与箭头错位：**① 1 数据单位 = 1 英寸；② 方框一律 Rectangle；③ 箭头端点由 `edge()` 从框边界算。**
- 图名**不要画进图里**——Word 已有居中图题，画进去就是重复。
- 插图替换有三个必踩的坑：**目录条目与正文标题同文本 → 插错位置**；**删段落不删媒体部件 → 文件虚胖**；**文档被 Word/WPS 打开 → 保存 PermissionError**。
- 交付前**必须逐图看一遍 PNG**（脚本读不到图内文字），再加哈希 + 宽高比两项机器校验。

---

## 1. 绘图三原则

### 1.1 单位归一：1 数据单位 = 1 英寸

```python
fig = plt.figure(figsize=(w, h))
ax = fig.add_axes([0, 0, 1, 1])      # ★ axes 占满 figure
ax.set_xlim(0, w); ax.set_ylim(0, h)
ax.set_aspect('equal')
```

三者比例一致时才成立。好处：**字号 pt 可直接换算**——`9pt ≈ 0.125 英寸`，两行文字约 `0.29` 英寸高，
于是"框高 1.25 英寸放两行字够不够"可以算，不必反复试。

> 不设 `[0,0,1,1]` 时 matplotlib 默认留 `图边距`，数据单位与英寸不再挂钩，字号只能靠试。

### 1.2 方框只用 Rectangle，边界必须精确

`FancyBboxPatch` 的 `pad`/`rounding_size` 会让实际边界**不等于** `(x, y, w, h)`，
箭头端点就落在"看起来的边"和"实际的边"之间 → 指进框里或悬在框外。

```python
ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw))   # 边界 == (x,y,w,h)
```

要圆角容器（层的外框、分组框）再用 FancyBboxPatch——**这类框不接箭头**，圆角无碍。

### 1.3 箭头端点由框边界计算

```python
def edge(b, side, t=0.5):           # b = (x, y, w, h)
    x, y, w, h = b
    return {'top': (x+w*t, y+h), 'bottom': (x+w*t, y),
            'left': (x, y+h*t), 'right': (x+w, y+h*t)}[side]

a = box(ax, 1, 3.5, 3, 1.2, '输入 A')
b = box(ax, 6, 3.5, 3, 1.2, '输出 B')
arr(ax, edge(a, 'right'), edge(b, 'left'))        # 端点自动贴两条边
```

`t` 控制"落在边的哪个位置"，多根箭头从同一个框出发时用它错开（如 `0.15 / 0.5 / 0.85`），避免挤在一起。

### 1.4 分层容器用「表头带 + 内容区」

层次架构图（应用层/板级/框架/库）最容易出"层标题压内容框"。
把层框切成两段：**顶部 0.5 英寸做表头带（填底色 + 层名），余下才是内容区**，
内容框再在内容区里居中排。层与层之间留 `0.55` 的间隙单独放向下箭头。

### 1.5 图内不写图名

图名交给 Word 图题（居中 + 加粗 + 10.5pt）。图里再画一遍标题，交付后就是"图 1"出现两次。

### 1.6 生成即自检：文本宽度预警

中文按 `1.0em`、西文按 `0.55em` 估算宽度，超过框宽就记预警（**不静默**）：

```
[宽度预警] OVER: 需≈2.38 in > 框宽 2.00 in -> 这是一段明显超过框宽的中文文字内容测试
```

生成后打印 `warn_report()`，应为空；不为空就调字号或加宽框。

---

## 2. 自检循环（关键动作）

**脚本读不到图内文字**（`Paragraph.text` 不含图内标注），所以必须人眼看：

```
生成 PNG → 用读图工具看这张 → 逐项核对（文字是否出框/压在框线上；元素是否重叠；
箭头是否从源框边界指向目标框边界；有无交叉穿透）→ 有问题改坐标 → 重新生成 → 再看
```

一次只复核一张，别一口气生成 9 张再统一看——那样错了要重做全部。
本项目的具体核对清单：

| 检查项 | 反例 |
|---|---|
| 文字是否压框线 | 层标题压在内容框上沿 |
| 标签与图形是否重叠 | 指示灯标签落在圆圈内部 |
| 箭头是否贴边 | 端点悬在框外/指进框里 |
| 箭头有无穿越 | 连线横穿主控框 |
| 注释是否越界 | 流程图右侧注释超出画布 |

---

## 3. 插图替换入 Word（三个坑）

### 3.1 目录条目与正文标题同文本 → 插错位置

用"按标题文本定位锚点"时，**TOC 条目会先被命中**，图就被插进目录区。必须跳过目录样式：

```python
def find_body_heading(doc, text):
    for p in doc.paragraphs:
        style = p.style.name if p.style else ''
        if style.lower().startswith('toc'):      # ★ 必须跳过
            continue
        if p.text.strip().startswith(text):
            return p
```

现象：图跑到目录页、正文该在的位置反而没有图。

### 3.2 删段落不删媒体部件 → 文件虚胖

python-docx 删掉图片段落后，**包内的图片部件仍在**。反复替换会让旧图越积越多：
本案例 1.48MB → 2.43MB（11 个孤立部件）。

修法：断开未被引用的图片关系即可，**不用改 zip**：

```python
for rid, rel in list(doc.part.rels.items()):
    base = os.path.basename(rel.target_ref or '')
    if base.startswith('image') and base.endswith('.png') and base not in used:
        doc.part.drop_rel(rid)      # 保存时"不可达"部件不会被写出
```

效果：2.43MB → **0.98MB**，媒体部件 20 → 9。

> 动刀前先确认孤立部件确实没被引用：遍历全部 `.xml`/`.rels` 里的 `r:embed`/`r:link`。
> 本例只有 `word/document.xml` 引用 9 个 rId，其余 11 个才是安全可删的孤立件。

### 3.3 文档被 Word/WPS 打开 → 保存 PermissionError

`doc.save(path)` 对已打开的 `.docx` 直接抛 `PermissionError`，而且**此时前面所有改动都白做**。
动笔前先探一次独占写权限：

```python
try:
    with open(path, 'rb+'): pass
except OSError:
    raise IOError('目标文档被其它进程占用，请先关闭')
```

查是谁占着：`Get-CimInstance Win32_Process` 看命令行里带该文件名的 `wps.exe` / `WINWORD.EXE`。

### 3.4 只认一种图片形式 → 数错图、误删 VML 图（最险）

Word 里图片有两种形态：**DrawingML**（`a:blip@r:embed`）与 **VML**（`v:imagedata@r:id`）。
模板文档（老版式、文本框、艺术字）常混用 VML —— 实测本工程 **RD-030 有 4 张 VML 图**、
**血糖仪 058 参考文档有 3 张**。

只判断 `a:blip` 的代价（在 RD-030 副本上实测）：

```
iter_image_paragraphs 只数到 3 张（实际 7 张）
drop_orphan_image_rels 删掉 4 个"仍被 VML 引用"的关系  ->  media 7 → 3
保存后 4 处悬空引用（rId12/13/14/17）  ->  4 张图直接从文档里消失
```

**判定"引用"必须同时收两种**，且 VML 要用 **Clark 记法**（python-docx 的 nsmap 里**没有 `v` 前缀**，
写 `qn('v:imagedata')` 会 `KeyError: 'v'`）：

```python
VML_NS = 'urn:schemas-microsoft-com:vml'
IMAGE_REF_TAGS = ((qn('a:blip'), qn('r:embed')), ('{%s}imagedata' % VML_NS, qn('r:id')))

def image_rids(p):                     # 唯一出口：所有"找图片"都走这里
    rids = []
    for tag, attr in IMAGE_REF_TAGS:
        for el in p._p.findall('.//' + tag):
            if el.get(attr):
                rids.append(el.get(attr))
    return rids
```

`has_inline_image / iter_image_paragraphs / paragraph_image_sha256 / drop_orphan_image_rels /
verify_figures` 统一走 `image_rids`——**不要再单独写 `findall('a:blip')`**。
另外 VML 图没有 `wp:inline`/`wp:extent`，核宽高比前要先判空，否则 `IndexError`。

> **教训（本文件自己要记的）**：`docx_ops.py` 里本来就有 `has_graphic()`（`w:drawing`/`w:pict` 两种都认），
> 我却又写了个只认一种的 `has_inline_image` —— 既重复又做错。
> 这正是"只写新文件、不先查已有约定"的后果：**加函数前先搜同义实现。**

---

## 4. 两项机器校验（截图看不出，但必须做）

`python-docx` 插图时若**同时指定宽度和高度**会造成拉伸；只给宽度时，高度按 PNG 原始比例算，才不会变形。替换图后要核：

| 校验 | 做法 | 通过标准 |
|---|---|---|
| 二进制一致 | 取嵌入图片 blob 的 sha256，与源 PNG 比 | 逐张相等且顺序正确 |
| 显示宽高比 | `wp:extent` 的 `cx/cy` 与 PNG 像素 `宽/高` 比 | 差 < 1% |

本案例 9 张全部通过（如 fig1 `5.80×3.70 in`，PNG 比 `1.569`，显示比 `1.569`）。

---

## 5. 交付前清单

1. 生成图 → **逐张读图核对**（第 2 节表格）。
2. 每条图题**居中 + 加粗**，且位于**正文区**（第一个 Heading 1 之后，不在目录区）。
3. `clear_figures` → `replace_figures` 重建，锚点用 `find_body_heading`（跳过 toc）。
4. 跑 `drop_orphan_image_rels` **之前**先对账：`iter_image_paragraphs` 的总数应等于文中
   `a:blip` + `v:imagedata` 的引用数之和；不等说明还原成"只认一种"，**停下别删**。
5. `drop_orphan_image_rels` 瘦身；保存后重开，确认 media 部件数 == 实际被引用数，且无悬空 rId。
6. `verify_figures` 通过（哈希 + 宽高比；VML 图只核哈希）。
7. 文件可写校验通过后再保存；保存后重开一次确认结构与图片数。
8. 人工在 Word/WPS 里翻页确认渲染效果。

## 6. 复用入口

| 需求 | 直接用 |
|---|---|
| 画框图/流程图/拓扑图原语 | `tools/fig_tools.py`：`canvas / box / txt / edge / arr / circle / flow / save / warn_report` |
| 竖向流程图 | `fig_tools.flow(ax, steps, bx, top, notes={...})` |
| 列图片段落 / 取图片 rId | `docx_ops.iter_image_paragraphs(doc)` / `docx_ops.image_rids(p)`（**两种图片形式都认**） |
| 插图替换 | `docx_ops.replace_figures(doc, specs)`（specs = `[(png, 图题, 锚点标题, 宽度in), ...]`） |
| 瘦身 | `docx_ops.drop_orphan_image_rels(doc)` |
| 校验 | `docx_ops.verify_figures(doc, [png...])` |
| 写前探锁 | `docx_ops.assert_writable(path)` |

> 项目只提供"图清单"（png / 图题 / 锚点 / 宽度）与事实来源；绘图与插图逻辑不重复实现。
