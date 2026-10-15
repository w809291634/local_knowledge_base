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

### `config_check.py` —— 工程配置适配体检 ★换工程先跑这个

```bash
python tools/config_check.py            # 在工程根目录跑（配置会自动向上查找）
python tools/config_check.py --strict   # WARN 也算不通过（CI 用）
```

回答一个问题：**工具箱的配置真的对这个工程生效了吗？**
四类一致性核对，任一对不上都会让门禁**静默降级**（看着 PASS，其实该查的没查）：

| 类 | 核对什么 | 对不上的后果 |
|---|---|---|
| A 路径 | 里写的每个文件/目录是否存在 | 脚本跳过或直接崩 |
| B 屏幕 | `screen.w/h` 是否等于设计源与工程文件实际尺寸 | 越界检查基准算错 |
| C 字体 | `name_to_px` / 图标私有区是否覆盖实际用到的字体与码位 | 未声明字体误报、图标宽度算错 |
| D 结构 | `tree_schema` 的键名与类型是否匹配设计源真实结构 | 组件树遍历不到，体检形同虚设 |
| E 门禁 | `checks.gates` 挂的脚本是否存在 | 闸门被 SKIP，等于没挂 |

顺带查出**旧工程的绝对路径残留**（换机器/迁目录后最常见的隐性失效）。
运行时产物目录（`preview/render/work/native_dir`）缺失只报 INFO，不算错。

退出码：`0` 通过，`1` 有 ERROR（`--strict` 下 WARN 也算）。

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

### `font_verify.py` —— 「后台烘焙的字体 == EEZ Studio GUI 产物吗」★

自己搭了旁路生成（解包官方引擎 / 任何脚本烘焙）之后，**最大的风险不是跑不起来，
而是「跑起来了但和官方产物不一样」** —— 差几个空行、一个 include、几个字形，
编译照样过、上屏才豆腐，肉眼根本看不出来。

```bash
# 1) 在 EEZ Studio 里 Check and Build 之后，立刻存真值
python tools/font_verify.py snapshot --src src/ui --golden .golden_fonts \
       --note "EEZ Studio 1.22.10 GUI Check and Build 产物"

# 2) 换成后台产物后比对（--metrics 顺带比 line_height/base_line）
python tools/font_verify.py check --src src/ui --golden .golden_fonts --metrics

python tools/font_verify.py metrics --src src/ui        # 只看度量
```

- **黄金样本必须来自 GUI**。自己烘一份当真值 = 自己给自己当裁判，一致也证明不了任何事。
- 不一致时自动定位并**猜成因**（成因表见 `skills.md §11.13` 第四节）：
  base64 误解码 / `lv_include` / 空行折叠 / 末尾空白 / `Opts` 参数 / 字形集合 / CRLF。
  优先级从具体到泛化，先命中先报。**CRLF 会淹没真实差异，工具先归一化再诊断。**
- 退出码：0 全一致，1 有不一致，2 用法/环境错误。
- ⚠ 逐字节比对**不充分**（文件没被覆盖时也全绿），必须再做「清空重建实验」——
  步骤见文件末尾 `EXPERIMENT` 注释与 `skills.md §11.13` 第三节。

---

## 三、构建类（工程无关内核）

### `eez_font_bake.py` —— 调 EEZ Studio **官方**字体引擎烘焙 ★

EEZ 的 headless CLI `--build-project` **不烘焙字体**，而「必须手工点 GUI Build」又进不了
CI。这个工具把 EEZ 安装目录 `app.asar` 里的**官方引擎本身**解出来跑，**纯后台、不开 GUI**，
产出与 GUI 点 Build **逐字节一致**（判据与验证方法见 `skills.md §11.13`）。

```bash
python tools/eez_font_bake.py --info                  # 探测 asar / node / 引擎缓存
python tools/eez_font_bake.py <工程文件> <输出目录>      # 烘全部 LVGL 字体
python tools/eez_font_bake.py <工程文件> <输出目录> 名1 名2
python tools/eez_font_bake.py --clean                  # 清引擎缓存（EEZ 升级后必做）
```

输出：`<输出目录>/ui_font_*.c` + `manifest.json`（变量名清单，由 EEZ 的 `getName()` 算出）。
**只写输出目录，不碰任何工程目录** —— 落到哪、要不要增量，都是工程侧胶水的事。

作为库用（工程侧脚本推荐这么调，别复制一份 `BAKE_JS`）：

```python
import eez_font_bake
names = eez_font_bake.bake(proj_path, out_dir)     # -> ["ui_font_xxx", ...]
if eez_font_bake.kernel_hash() != EXPECTED_HASH:   # 内核被改过就报警
    raise SystemExit("字体内核已分叉，重新验证")
```

`kernel_hash()` 是内核 `BAKE_JS` 的 sha256：**改了烘焙行为指纹就变**，
工程侧拿它做防分叉检查，避免"工具箱升级了、工程里那份还在偷偷跑旧逻辑"。

环境变量：`EEZ_STUDIO_ASAR` 指定 `app.asar`；`EEZ_NODE` 指定 node。
引擎解包缓存落在 `%LOCALAPPDATA%/eez-font-engine/<asar 指纹>`，**EEZ Studio 升级后要 `--clean`**。

> 分工：本文件 = **内核**（工程无关，进工具箱）；落盘 / 增量 / 写 `src/ui` /
> 孤儿清理 = **胶水**（工程专属，留在工程里）。详见 `skills.md §11.12`。

---

## 四、抓原生渲染图（Chromium / Electron 系）

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
- 把内核产物搬到工程目录的**胶水脚本**（例：本工程 `design/eez_font_engine.py`，
  它 import 本工具箱的 `eez_font_bake.py`，自己只管落盘/增量/孤儿清理）

这样工具箱保持"拷到哪都一样"，工程换框架也不用改工具箱。
