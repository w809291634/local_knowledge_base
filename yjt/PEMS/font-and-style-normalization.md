# 字体与字号统一（文档族级版式收口）

> 适用：文档族由多份历史模板拼合、被不同人改过，出现「同一份文档里宋体/仿宋/黑体/微软雅黑混用、
> 字号 9/10.5/11/12/14/16/22/36 并存」时的批量收口。
> 原则：**改生成器 + 改事实文件的版式段，不手改产物**；改完全量重生成并重新跑闸门与渲染。

## 结论先行

1. 字号统一不是"全选改一遍"：要**分区**（正文 / 各级标题 / 表格 / 图题 / 封面区 / 目录 / 页眉页脚），
   并明确哪些**故意不动**（封面版式、目录层级、页眉页脚）。
2. 只改 run 的直接格式**不够**：必须同时改 `styles.xml` 里 `Normal`、`Heading 1~4` 的默认值，
   否则用户在 Word 里新打一个字又回到旧字体。
3. **空 run 也要设字号**——它们不显示文字，但决定行高与后续输入。
4. 中文与西文分槽：`w:rFonts@eastAsia` 管中文，`@ascii`/`@hAnsi` 管西文与数字。
   注册资料里大量标准号、型号串与带单位的数值（如 `GB 9706.1`、`XX-1000`、`10mW±20%`）属西文，惯例配 Times New Roman；
   强行让西文也用宋体会让长串换行变多。
5. **表格字号一般要比正文小一档**（正文小四 → 表格五号）。宽表（5~7 列窄列）全上小四会撞破列宽、
   行高膨胀、页数增加；这是取舍，不是偷懒，需在版本说明里写明。
6. 配图是 PNG，**不受 Word 字体设置影响**：正文换宋体后，图内若还是黑体就仍然"不统一"，
   必须回到绘图脚本换字体重绘（matplotlib：`rcParams['font.family']='SimSun'`，在 import 绘图库之后覆盖）。

## 1. 先测量，再动手

```python
import os, collections
from docx import Document
from docx.oxml.ns import qn

def eastasia(r):
    rPr = r._r.find(qn('w:rPr'))
    if rPr is None: return None
    rf = rPr.find(qn('w:rFonts'))
    return rf.get(qn('w:eastAsia')) if rf is not None else None

agg = collections.Counter()
for f in os.listdir(OUT):
    if not f.endswith('.docx'): continue
    d = Document(os.path.join(OUT, f))
    for p in d.paragraphs:
        for r in p.runs:
            if r.text.strip():
                agg[(f[:6], 'body', eastasia(r),
                     r.font.size.pt if r.font.size else None)] += 1
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        if r.text.strip():
                            agg[(f[:6], 'table', eastasia(r),
                                 r.font.size.pt if r.font.size else None)] += 1
for k, v in sorted(agg.items(), key=lambda x: -x[1]):
    print(k, v)
```

看三件事：① 有多少 run 的字体槽是 `None`（继承样式，改样式即可批量生效）；
② 有多少被**直接格式**钉死（必须逐 run 覆写）；③ 表格与正文各占多少（决定要不要分档）。

## 2. 版式规则写进事实文件（唯一来源）

```yaml
formatting:
  east_asia: 宋体
  ascii_font: Times New Roman
  body_pt: 12          # 正文 小四
  table_pt: 10.5       # 表格 五号（宽表用小四会撞破列宽）
  caption_pt: 10.5     # 图题/表题 五号
  h1_pt: 16            # 三号；h2 15（小三）、h3 14（四号）、h4 12（小四），均加粗
  keep_untouched: [封面区, 目录条目, 页眉页脚, 文本框图形]
  figure_font: SimSun  # 配图内文字随正文
```

## 3. 执行要点

```python
def _apply_font(run, ea, ascii_font, size_pt, bold=None):
    run.font.name = ascii_font                    # python-docx 会同时写 ascii 与 hAnsi
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rPr.insert(0, rf)
    rf.set(qn('w:eastAsia'), ea)
    rf.set(qn('w:cs'), ascii_font)
    run.font.size = Pt(size_pt)                   # 用 python-docx 写 sz/szCs，避免元素顺序违规
    if bold is not None:
        run.font.bold = bold
```

分区判定顺序（先特殊后一般）：

| 判定 | 依据 | 处置 |
|---|---|---|
| 封面区 | 正文块序列里**封面表之前**的所有段落 + 封面表本身 | 跳过不动 |
| 目录 | `p.style.name` 以 `toc` 开头、`Table of contents` | 跳过不动 |
| 页眉页脚 | `section.header/footer` | 不遍历即不动 |
| 文本框图形 | `p.runs` 天然取不到 `w:txbxContent` 内的 run | 自动跳过（要改见 `pitfalls.md` 节点级替换） |
| 标题 | 样式名 `Heading N` / `标题 N` | 该级字号 + `bold=True` |
| 表格 | 遍历 `doc.tables` 全部单元格（去重合并格） | 表格字号，`bold` 不覆盖（保留表头加粗） |
| 图题/表题 | 样式 `Figure`/`Caption`，或文本以「图」「表」开头且 ≤40 字 | 图题字号 |
| 其余 | — | 正文字号 |

**同时改样式默认值**：`Normal` → 正文档，`Heading 1~4` → 各级字号，并写 `rFonts@eastAsia`。

## 4. 验证（不能只看"改成功了"）

1. 复跑第 1 节的测量脚本：目标档位之外**只允许**出现"故意保留"的封面/目录条目；把例外逐项指认到位置（封面大标题、封面表）。
2. 页数会因字号变大而增加：逐页渲染检查**无空白页、无列宽撞破、无表格被挤到跨页断行**。
3. 用 Word（不只 WPS、不只 LibreOffice）逐个打开确认无损坏，并记录页数。
4. 版本升级：输出到新版本目录（`*_V2/`），旧版保留；在版本说明里写清"本版仅版式，内容未变"，
   避免评审把版式改动误读为内容变更。

## 5. 反模式

- 在 Word 里全选改字体 → 封面大标题、目录、页眉一起变，且下次重生成又被模板打回原形。
- 只改 `Normal` 样式 → 被直接格式钉死的 run 一个都没变，看起来"改了没用"。
- 正文/表格同字号 → 宽表溢出，回头又手工缩小表格，重新变成不统一。
- 忘记重绘配图 → 文档正文宋体、图里黑体，肉眼一眼看出不统一。


## 6. 执行顺序（实测，错了会白改一遍）

```
生成/就地替换 → 表格与图示 → 封面与分页
   → 目录刷新（Word 更新域）→ ★ 字体统一（第二遍）→ 闸门 → 渲染
```

字体统一必须**在目录刷新之后再跑一遍**，两个原因：

1. Word 保存时会重写封面标题与目录条目的 run，把显式 `rFonts` 丢掉（实测三份文档各
   141/39/50 处变成 `None/None`）——刷新前统一得再干净也会被抹回去；
2. Word 还会顺手规掉与 `docDefaults` 等价的**样式默认字号**，需从刷新前的备份把各级样式
   `w:sz` 写回，否则产物 XML 不再等于模板版式。

## 7. 覆盖清单与闸门项

统一动作必须覆盖四处，缺一处就是"看起来改了其实没改"：

| 位置 | 手段 | 漏掉的后果 |
|---|---|---|
| 正文段落 run | `unify_document_fonts` | 主体 OK |
| **表格单元格** | 同上（内部遍历 `doc.tables`） | `doc.paragraphs` 不含表内段落，旧字体整片残留 |
| **空 run** | 同上（不按有无文字过滤） | 行高与用户新输入仍走旧字号 |
| **样式默认值** | `style_font(Normal/Heading 1~4/Caption)` | Word 里新打一个字就回到旧字体 |

配套硬约束：改 `w:rFonts` 时必须删掉 `asciiTheme/eastAsiaTheme/hAnsiTheme/cstheme`，
否则主题优先级更高，显式字体名不生效。

闸门最少四条（非零退出码阻断发布）：

1. 分区字体基线：所有非文本框 run 的 `eastAsia`/`ascii` == 基线值；
2. 分区字号：正文=正文档、表格与图题=表格档；标题/封面/页眉**只校字体不校字号**；
3. 样式默认值：`Heading N` 的 `sz` 与模板一致（只允许 `Normal` 随正文档变），`eastAsia` 已统一；
4. 配图字体：绘图脚本的 `font.family` 与正文一致，重绘后跑宽度预警 + 逐张看图
   （PNG 不受 Word 字体设置影响，正文换宋体而图里还是黑体，一眼就能看出来）。
