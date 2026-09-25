# tools/ —— 工具索引

所有 Python 工具只依赖标准库（**Pillow 按需**：只有图像/字体度量类工具才需要，
缺了会给出安装提示，不会在 import 阶段崩掉）。
配置从**工程侧**的配置文件读取（查找顺序见 `CONFIG.md §0`），**不需要传路径参数**。

> 约定：`python` 指配置里 `binaries.python` 或任意已装 Pillow 的解释器。

---

## 一、体检类

### `kit.py` —— 公共库 / 配置自检

```bash
python tools/kit.py                 # 打印配置解析结果 + 关键路径存在性（先跑这个）
```

作为库使用：

```python
import kit
cfg = kit.load_config()
img = kit.open_gray("x.png")
print(kit.ink_bbox(img, thr=140))
print(kit.diff_report("a.png", "b.png")["pct"])
```

API：`load_config / cfg_path / screen_size / open_gray / ink_bbox / row_profile /
col_profile / is_uniform_row / edge_touch / diff_report / TextMeasurer / ink_offset /
walk_tree / load_pages / declared_fonts / is_builtin_font / require_pil`

### `log_entry.py` —— 记录写入器（新问题 / 提示词留痕）

```bash
python tools/log_entry.py prompt  "用户的原始提示词" --tool <AI名> --ask 诉求 --out 产出 --link P-0001
python tools/log_entry.py problem --title "<标题>" --symptom .. --repro .. --root .. --fix .. --evidence .. --sink .. [--status open|fixed|wontfix]
python tools/log_entry.py list [problem|prompt|all]
python tools/log_entry.py next-id [problem|prompt]
```

把「新问题」写进 `intake/P-####_*.md`（并更新 `intake/index.md`），把「提示词」追加进
`prompts/PROMPT_LOG.md`。只用标准库、与工程解耦 —— **任何 AI 工具都能调**。完整规约见 `../INTAKE.md`。

### `tree_check.py` —— 组件树静态体检

```bash
python tools/tree_check.py                    # 用配置里的设计源
python tools/tree_check.py --src 别的.json
python tools/tree_check.py --json out.json --show 20
```

检查 5 类：**几何越界 / 文本会被折行 / 字体名未声明 / 死链 / 入口页**。
字段映射读配置的 `tree_schema`，换框架只改配置。
若 `screen.w/h` 未配置，会自动跳过几何与折行检查并提示。

退出码：`0` 全通过，`1` 有问题（可直接用于 CI）。

### `ink_check.py` —— 墨迹检测（判断"到底裁没裁"）

```bash
python tools/ink_check.py <图.png>
python tools/ink_check.py <图.png> --box X Y W H          # 只看这个矩形（要紧包单个元素）
python tools/ink_check.py <图.png> --rows                 # 打印行分布（找边界）
python tools/ink_check.py <图.png> --against L T W H      # 与声明框对比，算实际偏移 ★
```

`--against` 会输出 `dx/dy = 墨迹左上 − 声明框左上`。
**非 0 就意味着父容器/控件有默认 padding 或 border**（`PLAYBOOK §4.2` / `cases/B3`）。

---

### `audit_ui.py` —— 回归断言集（把踩过的坑固化成断言）

```bash
python tools/audit_ui.py                # 全量 A1~A10
python tools/audit_ui.py A3 A6          # 只跑指定项
```

| 项 | 检查 | 不检查会怎样 |
|----|------|--------------|
| A1 | 字体名已声明 | 拼错不报错，静默回退默认字号 → 大标题变小字 |
| A2 | 字体基线 = 实测 | 编辑器画的字与固件差几 px → 文字画高/超框 |
| A3 | 会吃主题内边距的类型显式 `pad_*=0` | 工程坐标 ≠ 渲染坐标 → 文字被推出画布 |
| A4 | 禁止"固定宽 + text_align 居中/右对齐" | 保存时按它自己的字宽重算 → 坐标变负数跑出画布 |
| A5 | 其它元素不得压进底栏区 | 点列表行却跳去了底栏 → "点了画面来回跳" |
| A6 | 生成代码引用的字体在运行配置里已开 | 模拟器能编过、真机 undeclared → "本地能跑上机炸" |
| A7 | 底栏显式传"当前页名"而非用高亮索引 | 二级页回主页的跳转被误删 |
| A8 | 设计源 / 工程 / 生成代码 三者跳转数一致 | 效果图上有按钮、上机没有 |
| A9 | 生成代码用到的 LVGL 部件在运行配置里已开 | 用了 `lv_switch_create` 但 `LV_USE_SWITCH=0` → 上机编译失败 |
| A10 | 样式值符合目标框架的取值语法（颜色必须 `0xRRGGBB`） | 写成 int/十进制时**构建不报错**，只在 GUI 报 invalid color → 见 `cases/B6` |

**A6 的两个细节**（都踩过，会影响可信度）：

- 先剥掉 `#if LV_FONT_X ... #endif` 守护块再统计 —— 生成器给内置字体查表加的
  就是这层保护，开关为 0 时引用根本不会编译进去，全文匹配会**假阳性**；
- 工程**自烘焙**字体（如 `ui_font_*`）不走 `LV_FONT_*` 开关，用
  `checks.font_switch_ignore` 排除，其存在性由 A2/A8 覆盖。

缺哪份输入就跳过哪条（打印"跳过"而非报错）。退出码 `1` = 有阻断项。

### `gen_clicks.py` —— 自动生成 L2 真点击用例

```bash
python tools/gen_clicks.py -o clicks.txt          # 写文件
python tools/gen_clicks.py --only Main,Settings   # 只生成指定页
```

从设计源推导**每个可达按钮**（含"先导航回该页"的路径），另生成两类回归：
点当前页底栏项应原地不动、**底栏空槽位点击不应跳转**（后者专抓"内容压占底栏导致误跳"）。
底栏槽位以按钮 x 为键自动推导（不能用 children 下标——当前页那一项通常不生成按钮，
下标会整体错位）。不可达的屏会明确列出来。

### `run_gate.py` —— 一键门禁（CI / pre-commit 用）

```bash
python tools/run_gate.py                 # G1 + 配置挂的工程侧闸门 + G4
python tools/run_gate.py --quick         # 只跑 G1 + 配置里标 quick 的项
python tools/run_gate.py --skip-tree     # 跳过 G4（tree_check 需要 Pillow）
python tools/run_gate.py --gen-clicks clicks.txt   # 顺带生成 L2 用例
```

内置闸门：`G1 audit_ui.py`、`G4 tree_check.py`；
工程侧闸门由配置 `checks.gates` 挂载（脚本留在工程里，不存在则 SKIP 不阻断）。

---

## 二、对照类

### `diff_report.py` —— 图像差异量化

```bash
python tools/diff_report.py a.png b.png
python tools/diff_report.py <期望目录>/ <实际目录>/        # 按同名文件批量比对
python tools/diff_report.py a.png b.png --overlay diff.png
python tools/diff_report.py a.png b.png --json r.json --grid 40 --thr 64
```

输出：`big`（结构性差异像素）、`pct`、`mid`（中等差异）、`hot`（热点区域）、`bbox`。
判读：`big==0` 一致；`pct < config.checks.diff_accept_pct` 且形状一致 → 抗锯齿；
否则看热点定位元素。尺寸不一致会**显式标注**（不会静默缩放）。

### `text_measure.py` —— 文本真实宽度

```bash
python tools/text_measure.py "<文本>" --font <字体名>
python tools/text_measure.py "<文本>" --font <字体名> --width-limit 98
python tools/text_measure.py "<文本>" --font <字体名> --centered-in 64
python tools/text_measure.py --batch texts.txt --font <字体名> --width-limit 60
python tools/text_measure.py          # 不带参数 → 跑自检样本
```

输出**净宽**（用于居中/右对齐）与**含余量宽度**（用于换行判定）—— 两者别混用。

---

## 三、抓原生渲染图（Chromium / Electron 系）

### `cdp/launch.sh` —— 按配置启动并等端口

```bash
bash tools/cdp/launch.sh            # 启动 + 等 CDP 端口就绪
bash tools/cdp/launch.sh --status   # 只检查端口
bash tools/cdp/launch.sh --kill     # 只杀进程
```

参数全部取自配置的 `runtime` 段（含"必须清掉的环境变量"与"不能加的开关"）。

### `cdp/grab.js` —— 通用抓图器

```bash
node tools/cdp/grab.js --out out.png                     # 截整窗
node tools/cdp/grab.js --out out.png --canvas            # 取最大 <canvas> 的原始像素 ★
node tools/cdp/grab.js --out out.png --canvas --click "<视图名>"
node tools/cdp/grab.js --out <目录>/ --click "<A>" --click "<B>"
node tools/cdp/grab.js --text                            # 只 dump 界面文本（排障）
```

内置三个必需行为：**合成事件点开视图**（`bubbles+view`）、**等像素变化**（防旧帧）、
**过滤空白帧**（防单色图）。

---

## 四、栈专属工具放哪里

不属于本工具箱。请放在**你的工程里**（例如 `design/` 或 `scripts/`），例如：

- 设计源 → 目标工程的**转换器**
- 设计源 → 图片的**渲染器**
- 目标工程 → 图片的**交叉验证渲染器**
- 字体/资源**离线生成器**
- 目标 IDE 的 CLI 构建**封装脚本**

这样工具箱保持"拷到哪都一样"，工程换框架也不用改工具箱。
