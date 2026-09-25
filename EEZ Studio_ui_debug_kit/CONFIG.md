# CONFIG.md —— 配置文件说明

> **换工程时，只需要改工程侧的配置文件**（默认名 `ui_debug_kit.config.json`，放在工程里）。
> 路径可写相对**该配置文件所在目录**的相对路径，也可写绝对路径；工具会自动解析成绝对路径。

## 0. 配置文件放哪、怎么被找到

查找顺序（`tools/kit.py`）：

1. 环境变量 `UI_DEBUG_KIT_CONFIG` 指定的文件
2. 从**当前工作目录**向上逐级查找 `ui_debug_kit.config.json` ← **推荐**
3. 从当前工作目录向上逐级查找 `config.json`（简易场景）
4. 工具箱目录下的 `config.json`（**不推荐**：会把工程信息留在工具箱里）

工具箱自带的是 `config.template.json`（纯占位符），**不会被当作配置**。

推荐做法：`cp ui_debug_kit/config.template.json <你的工程>/ui_debug_kit.config.json`，然后填它。

---

## 1. 字段总览

### `project` —— 工程基本信息与路径

| 字段 | 含义 | 备注 |
|---|---|---|
| `name` | 工程标识（仅用于打印） | 随意 |
| `platform` | 技术栈描述 | 帮助人和 AI 建立上下文 |
| `root` | 工程根目录 | 其他相对路径的基准点（按需） |
| `design_dir` | 设计源与工具目录 | |
| `design_src` | **设计源文件** | 静态体检读它 |
| `project_file` | 目标工程/产物文件 | 若为 JSON，工具会尝试读其中的字体声明 |
| `gen_dir` | 生成的代码目录 | 一致性检查用 |
| `builder` | 设计源生成器脚本（可选） | `audit_ui` A7 扫它查"底栏是否显式传了当前页名" |

### `screen` —— 屏幕与渲染语义

| 字段 | 含义 | 怎么定 |
|---|---|---|
| `w` / `h` | 画布尺寸 | 设计稿的分辨率；**留空会跳过几何类检查** |
| `origin` | 原点位置 | `top-left`（多数）/ `bottom-left` |
| `child_coords` | 子元素坐标语义 | `relative-to-parent`（多数）/ `absolute` |
| `design_coords` | 设计源坐标语义 | 常用于和 `child_coords` 不同 → 需要换算 |
| `ink_threshold` | 判定"墨迹"的亮度阈值（0–255） | **必须实测**：太低会把底色算成内容 |
| `last_row_is_separator` | 最外一行是否为全宽分隔线 | true 时自动跳过它，避免误报"触底" |
| `safe_margin` | 期望的安全边距（px） | 建议 ≥2 |

### `runtime` —— 运行时（抓原生图用）

| 字段 | 含义 | 备注 |
|---|---|---|
| `kind` | 运行时类型 | `electron` / `browser` / `native` / `emulator` |
| `exe` | 可执行文件 | 绝对路径最稳 |
| `args` | 启动参数 | **务必包含 `--enable-unsafe-swiftshader`**，且**不要**加 `--disable-software-rasterizer` / `--in-process-gpu` |
| `debug_port` | CDP 端口 | 默认 9222 |
| `open_project_as_arg` | 是否把工程路径作为参数传入 | true 时自动追加 `project_file` |
| `unset_env` | 需要清除的环境变量 | Electron 系通常要清 `ELECTRON_RUN_AS_NODE` |
| `exit_after_seconds` | 观察到进程自崩的时间（参考值） | 用来提示"要抢时间窗"，0 表示未知 |
| `capture_one_target_per_launch` | 一个目标是否要一次启动 | 多数 Chromium 宿主为 true（第二次起画布可能不再重绘） |

### `binaries` —— 解释器与工具

| 字段 | 用途 |
|---|---|
| `python` | 跑工具脚本（需要 Pillow） |
| `python_venv` | 另装依赖的解释器（可选） |
| `node` | 跑 `tools/cdp/*.js`（需 18+，内置 fetch/WebSocket） |

### `fonts` —— 字体（**最容易填错，务必实测**）

| 字段 | 含义 | 关键点 |
|---|---|---|
| `device_ttf` | 设备实际使用的正文字体 | 用来量文本宽度 |
| `icon_woff` / `icon_ttf` | 图标字体 | 图标字符要切到这个字体量 |
| `name_to_px` | 字体名 → 像素字号 | 设计稿常写不存在的字号；这里把"名字"映射到"实际生效字号" |
| `builtin_patterns` | 内置字体的名字通配（可留空，留空则用命名约定启发式） | 命中这些模式的名字不算"未声明" |
| `metrics` | 各字号的实际度量 | **必须读生成物**，**不要抄面板配置值** |
| `ink_offset_from_box_top` | 字号 → `[上偏移, 下偏移]` | 用 `tools/ink_check.py --against` 实测得到 |
| `icon_private_ranges` | 图标/符号的码位区间 | 决定"逐字符切字体"的判定 |

> 建议在 `metrics` 里把面板上的**错误值**也一并留着（例如加个 `panel_value_do_not_use` 字段）：
> 一旦发现两者不一致，就是"配置值 ≠ 生效值"这个坑又出现了（`PLAYBOOK §4.3`）。

### `theme_defaults` —— 默认主题带来的额外偏移

| 字段 | 含义 |
|---|---|
| `container` / `button` / … | 该类控件下，子控件的额外偏移 `{dx, dy}` |

**怎么测（三步）**：
1. 把**同类控件**分别放进容器与目标控件里，各放一个坐标已知的元素；
2. 用 `tools/ink_check.py --against` 量出各自的墨迹偏移；
3. 两者的差就是默认主题的贡献。

若已在样式里显式清零（`padding: 0`），这里填 `0` 即可。

### `tree_schema` —— 组件树字段映射（**换框架改这里**）

把设计源的字段名映射到工具期望的语义键：

| 键 | 含义 | 默认 |
|---|---|---|
| `pages` | 页面列表所在的键（可给多个候选，取第一个命中的） | `["pages"]` |
| `page_name` | 页名字段 | `name` |
| `page_root` | 页根节点字段 | `screen` |
| `children` | 子节点列表 | `children` |
| `x` / `y` / `w` / `h` | 坐标与尺寸 | 同名 |
| `type` | 控件类型 | `type` |
| `text` | 文本内容 | `text` |
| `font` | 字体名 | `font` |
| `goto` | 跳转目标 | `goto` |
| `image` | 图片/纹理引用 | `texture` |
| `type_values` | 类型**取值**映射 `{container, button, label}` | 默认同名；换框架改这里 |
| `nav_types` | 哪些类型算"可跳转控件" | `[button]` |
| `style_key` / `main_part` / `default_state` | 样式字段与默认分区/状态路径 | `style` / `MAIN` / `DEFAULT` |
| `width_unit_key` / `content_unit_value` | 宽度单位字段与"按内容"取值 | `wUnit` / `content` |

### `checks` —— 体检期望值

| 字段 | 含义 |
|---|---|
| `pages` | 期望的页面清单（批量抓图/比对用） |
| `entry_page` | 入口页名（必须存在且通常是第一页） |
| `expect_*` | 各检查的期望违规数（一般为 0） |
| `gates` | **工程侧扩展闸门**（`run_gate.py` 挂载）：`[{code,title,script,quick,need_pil}]` | 脚本留在工程里；不存在则 SKIP 不阻断 |
| `tab_bar` | 底栏识别规则 `{y,h,w}`，`y`=底栏顶边（可选） | **须 `y>0` 才生效**；不配 / `null` / `y<=0` 一律视为「无底栏」，A5 与底栏回归自动跳过 |
| `tab_pages` | 底栏各项对应的页名（可选） | 一般能自动推导；推导不出时才按 x 从左到右补 |
| `diff_big_threshold` | 结构性差异阈值（默认 64） |
| `diff_accept_pct` | 可接受差异百分比（默认 0.05%，用于放行抗锯齿差异） |

**A6 / A10 专用字段**（不给就用默认值；换框架时才需要改）：

| 字段 | 含义 | 默认 |
|---|---|---|
| `font_symbol_prefix` | 生成代码里字体符号的前缀 | `lv_font_` |
| `font_macro` | 运行时配置里字体开关的宏名模板（`%s` 填符号名大写） | `LV_FONT_%s` |
| `font_guard_aware` | 统计引用前先剥掉 `#if LV_FONT_X … #endif` 守护块（防假阳性） | `true` |
| `font_switch_ignore` | 引用的字体里，**不需要** `LV_FONT_*` 开关的符号名正则（如工程自烘焙字体 `["^ui_font_"]`）；这类字体的存在性由 A2/A8 覆盖 | `[]` |
| `color_props` | 样式里的颜色类属性名 | 常见 10 个（见 `audit_ui.DEFAULT_COLOR_PROPS`） |
| `color_node_keys` | **直接写在节点上**的简写颜色键（用于"颜色不放在 style 里"的 DSL，如 `bg`/`color`/`borderColor`） | `[]` |
| `color_value_patterns` | 合法颜色的正则白名单 | `["^#?[0-9a-fA-F]{3,6}$", "^0[xX][0-9a-fA-F]{6}$"]` |

### `paths` —— 产物目录

| 字段 | 含义 |
|---|---|
| `preview_dir` | 设计预览图 |
| `render_dir` | 交叉验证图 |
| `native_dir` | 原生渲染图 |
| `work_dir` | 临时产物 |
| `screens_c` | 生成的 UI 代码主文件（可选） | `audit_ui` A6 扫它引用的字体、A8 数它的事件回调 |
| `lv_conf` | 运行时字体开关配置，如 `lv_conf.h`（可选） | A6 与 `screens_c` 对账，防"本地能跑、上机炸" |
| `font_c` | 生成的字体文件，可写通配符（可选） | A2 用它算真实基线（`line_height − base_line`） |

---

## 2. 迁移到新工程（清单）

```
[ ] 拷入 ui_debug_kit/
[ ] cp ui_debug_kit/config.template.json <工程>/ui_debug_kit.config.json
[ ] 填 project.*（路径 + name/platform）
[ ] 填 screen.*（分辨率；ink_threshold 与 last_row_is_separator 必须实测）
[ ] 填 runtime.*（exe / args / debug_port / unset_env）
[ ] 填 binaries.*（python / node 解释器路径）
[ ] 填 fonts.device_ttf / icon_* / name_to_px / builtin_patterns
[ ] ★ 实测 fonts.metrics（读生成物里的 line_height / base_line → 换算 ascent）
[ ] ★ 实测 fonts.ink_offset_from_box_top（ink_check.py --against）
[ ] ★ 实测 theme_defaults（同类控件放进容器/按钮各测一次）
[ ] 填 tree_schema（按设计源的实际字段名；类型取值与 nav_types 也在这里）
[ ] 填 checks.pages / entry_page
[ ] 可选：paths.screens_c / lv_conf / font_c、project.builder（audit_ui 的 A2/A6/A7/A8 用）
[ ] 可选：checks.gates 挂上工程自己的检查脚本（跑 run_gate.py 时会一起跑）
[ ] 可选：checks.tab_bar（有底栏的话；底栏页名一般自动推导）
[ ] python tools/kit.py        → 关键路径全部 OK、screen 已配
[ ] python tools/run_gate.py   → 建立基线（A1~A10 缺输入会自动跳过并打印"跳过"）
[ ] 按 PLAYBOOK §3.3 选本栈的原生图手法，先跑通**一张**图
[ ] 把这轮新踩的坑写进 cases/
```

---

## 3. 常见配置错误

| 症状 | 原因 | 修正 |
|---|---|---|
| 报错说找不到配置文件 | 没建配置，或不在工作目录的祖先链上 | 见本文 §0；或用环境变量 `UI_DEBUG_KIT_CONFIG` |
| 提示 `screen.w / screen.h 未配置` | 屏幕尺寸留空 | 填上，否则几何类检查会被跳过 |
| 文本宽度全都不对 | `name_to_px` 里没有设计源实际使用的字体名 | 从设计源里 grep 出唯一字体名，逐个登记 |
| 墨迹检测到处误报 | `ink_threshold` 太低（把底色算成内容） | 用 `ink_check.py --rows` 看底色亮度再定阈值 |
| "触底"误报 | 画布最外一行是分隔线 | 打开 `last_row_is_separator` |
| 抓图全是空白 | `args` 少了 `--enable-unsafe-swiftshader`，或加了禁用兜底的参数 | 见 `PLAYBOOK §3.2` 参数避坑表 |
| 抓图拿到重复图 | 没有"等画面变化"；或需要一目标一次启动 | 用 `grab.js`（内置去重）；打开 `capture_one_target_per_launch` |
| 静态体检说坐标越界但肉眼没越界 | 用 `design_coords`/`child_coords` 未换算 | 检查是否需要"绝对→相对"的换算步骤 |
| 内置字体被报"未声明" | 命名不满足启发式，且 `builtin_patterns` 没覆盖到 | 按框架的内置字体命名补通配（如 `<前缀>_*`） |
