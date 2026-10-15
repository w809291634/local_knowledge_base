# EEZ Studio Widgets 参考笔记（W1–W43）

> 来源：`reference_guide_raw.txt`（EEZ Studio Reference Guide 纯文本转储，无图片）。
> 覆盖范围：Widgets 章节 W1 AnimationImage 至 W43 Lottie，全部捕获。
> 三种变体体系：**Dashboard**（Web 仪表盘）、**EEZ-GUI**（嵌入式 GUI）、**LVGL**（LVGL 原生对象）。
> 公共属性族在文末附录 A / 附录 B 各记录一次，正文中每个 widget 仅列其 **Specific（专属）属性**，并标注所属族，避免冗余。
> 对 W10 / W16 / W20 / W24 / W30 / W35 / W42 七个 LVGL 关键 widget 提供额外详细的 LVGL 映射与 `json2eez` / `center_in` 流水线说明。

---

## 0. 阅读约定

- **类型标记**：`EXPRESSION (type)` 表示该属性值支持表达式（支持 `+ - * /` 及括号，如 `18 + 36`、`(100 - 32) / 2`），且结果按 type 解释。`Enum` 为下拉枚举。`ObjectReference` 引用工程中已定义的 Style / 图像 / 仪表盘等对象。`Array` / `Object` 为结构化值。
- **表达式支持范围**：所有 `Left / Top / Width / Height` 均可在输入后回车即时求值；`Visible`、各 `EXPRESSION` 着色/状态属性同理。
- **公共族归属速查**：
  - **LVGL 族**（走通用 LVGL 属性集）：W10, W13, W14, W16, W20, W24, W30, W35, W36, W37, W42, W43。
  - **Dashboard / EEZ-GUI 族**（走 Resizing / Visible / Style 对象引用集）：W1–W9, W11, W12, W15, W17–W19, W21–W29, W31–W34, W38–W41。
  - 混合：W5/W6 Bitmap、W7/W8 Button、W22/W23 Dropdown 等分别属 Dashboard / EEZ-GUI 族。
- **分页噪音**：原文本含「第 X 页 / 共 784 页」及 `I.xxx` 标号，已忽略。

---

## 1. W1 AnimationImage（动画图像）

**Description**：循环播放一组图像帧形成动画的 widget。

**所属族**：Dashboard / EEZ-GUI（含通用 Resizing / Visible / Style 集）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Images | Array | — | 组成动画的帧图像列表（每帧为一幅图像引用）。 |
| Duration | Number | — | 单帧显示时长（毫秒）。 |
| Repeat infinite | Boolean | false | 是否无限循环播放；false 时按 Repeat count 播放指定次数。 |
| Repeat count | Number | — | 循环播放次数（Repeat infinite 为 false 时生效）。 |

**Examples**：典型用于加载动画、状态指示动画。

---

## 2. W2 Arc（圆弧）

**Description**：绘制圆弧/环形进度指示的 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Range min | EXPRESSION (int) | 0 | 弧值下限。 |
| Range max | EXPRESSION (int) | 100 | 弧值上限。 |
| Value | EXPRESSION (int) | — | 当前弧值。 |
| Mode | Enum | NORMAL | 绘制模式：NORMAL / REVERSE / SYMMETRICAL。 |
| Bg start angle | Number | — | 背景弧起始角度。 |
| Bg end angle | Number | — | 背景弧结束角度。 |
| Rotation | Number | — | 整体旋转角度。 |
| Use start angle | Boolean | — | 是否启用自定义起始角度。 |
| Start angle | Number | — | 弧起始角度（Use start angle 启用时）。 |
| Use end angle | Boolean | — | 是否启用自定义结束角度。 |
| End angle | Number | — | 弧结束角度（Use end angle 启用时）。 |

**Examples**：仪表盘进度环、音量环。

---

## 3. W3 Bar（进度条）

**Description**：线性进度条 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Min | Number | 0 | 最小值。 |
| Max | Number | 100 | 最大值。 |
| Mode | Enum | NORMAL | NORMAL / SYMMETRICAL（对称，从中间向两端）/ RANGE（范围两端值）。 |
| Value | Number | — | 当前值（或 RANGE 模式下的主值）。 |
| Value start | Number | — | RANGE 模式下的起始值。 |
| Enable animation | Boolean | — | 值变化时是否播放过渡动画。 |

---

## 4. W4 BarGraph（条形图）

**Description**：显示一组条形数据的 widget，支持阈值与方向。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 条形数据来源。 |
| Orientation | Enum | — | Left right / Right left / Top bottom / Bottom top（条形生长方向）。 |
| Display value | Boolean | — | 是否在条上显示数值。 |
| Threshold1 | Number | — | 第一阈值（用于变色/标记）。 |
| Threshold2 | Number | — | 第二阈值。 |
| Min | Number | — | 数据下限。 |
| Max | Number | — | 数据上限。 |
| Refresh rate | Number | — | 刷新率。 |
| Visible | EXPRESSION (boolean) | — | 表达式为真时可见。 |

---

## 5. W5 Bitmap（位图，Dashboard 变体）

**Description**：在 Dashboard 上显示一幅位图。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | — | — | 位图数据（Dashboard 变体，非表达式）。 |
| Bitmap | — | — | 位图图像引用。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 6. W6 Bitmap（位图，EEZ-GUI 变体）

**Description**：在 EEZ-GUI 上显示一幅位图（数据支持表达式）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION (int) | — | 位图数据来源（表达式求值为整数索引/引用）。 |
| Bitmap | — | — | 位图图像引用。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 7. W7 Button（按钮，Dashboard 变体）

**Description**：可点击按钮（Dashboard）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Label | String | — | 按钮文字。 |
| Enabled | Boolean | true | 是否可用。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 8. W8 Button（按钮，EEZ-GUI 变体）

**Description**：可点击按钮（EEZ-GUI）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Label | String | — | 按钮文字。 |
| Enabled | Boolean | true | 是否可用。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 9. W9 ButtonGroup（按钮组）

**Description**：一组互斥/可选按钮的集合。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Button labels | Array | — | 各按钮文字标签列表。 |
| Selected button | Number | — | 当前选中按钮索引。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 10. W10 Button（按钮，LVGL 变体）【重要】

**Description**：LVGL 原生按钮对象（`lv_button`）。Studio 会生成完整创建代码，但按钮上的文字/内容通常需由**子 Label widget** 提供，或后续自定义代码设置。

**所属族**：**纯 LVGL 通用族**（无任何 Specific 属性，继承附录 A 全部通用属性：Name / Group / Position&Size / Layout(Tab title) / Use style / Flags / States / Event handlers / Flow）。

**LVGL 特定说明（额外详细）**
- **坐标/尺寸**：通过 `Left / Top / Width / Height` + 对应 `unit`（px / % / content）设置；支持表达式。等价于 `lv_obj_set_x/y/w/h` 与 `lv_pct()`（% 模式）。
- **映射**：`lv_button_create(parent)` → 设置坐标/尺寸 → 通过 `LV_OBJ_FLAG_CLICKABLE`（默认开启）与 CLICKED 事件交互。按钮本身不带文字，常见做法是在其下挂一个 `lv_label` 作为子对象并居中。
- **Flags 关键点**：`Clickable`（默认 true，表达式可动态切换）、`Click focusable`、`Checkable`（点击切换选中态）、`Event bubble` 等；滚动类 Flag 对按钮通常无意义但同族可用。
- **States**：`Pressed` / `Checked` / `Disabled` / `Focused` 均可用 `EXPRESSION` 动态驱动（带 `… type` 枚举选择 Literal/Expression）。
- **对 `json2eez` / `center_in` 的影响**：该 widget 在 JSON 中没有 `specific` 段，流水线应识别为 `lv_button` 并套用通用 LVGL 布局；`center_in` 居中逻辑应使用 `Left/Top + Width/Height` 或 `Align and distribute / Center widget` 元数据（见附录 A），不依赖任何专属属性。

---

## 11. W11 ButtonMatrix（按钮矩阵）

**Description**：以矩阵排列的多个按钮。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Buttons | Array | — | 按钮定义列表，每项可含：New line（换行）、Text（文字）、Width（宽度）及标志位 HIDDEN / NO_REPEAT / DISABLED / CHECKABLE / CHECKED / CLICK_TRIG / POPOVER / RECOLOR / CUSTOM_1 / CUSTOM_2。 |
| One check | Boolean | false | 是否仅允许一个按钮处于选中态（单选矩阵）。 |

---

## 12. W12 Calendar（日历）

**Description**：日历选择 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Year | Number | — | 当前年。 |
| Month | Number | — | 当前月。 |
| Day | Number | — | 当前日。 |

---

## 13. W13 Canvas（画布）【LVGL 族，无 Specific】

**Description**：LVGL 画布对象（`lv_canvas`），用于自定义像素绘制；继承自 Image 概念，可在运行时用代码绘制。

**所属族**：**纯 LVGL 通用族**，无 Specific 属性。

**LVGL 说明**：映射 `lv_canvas_create(parent)`；像素缓冲由 Style / 后续代码设置。坐标/尺寸/Flags 同附录 A。流水线识别为 `lv_canvas`。

---

## 14. W14 Chart（图表）【LVGL 族，无 Specific】

**Description**：LVGL 原生图表对象（`lv_chart`），支持折线/柱状序列。

**所属族**：**纯 LVGL 通用族**，无 Specific 属性。

**LVGL 说明**：映射 `lv_chart_create(parent)`；序列、数据点、坐标轴范围等通过后续自定义代码或 Style 配置（LVGL 变体下不在 Studio 属性面板暴露，区别于 Dashboard/EEZ-GUI 的 W38/W39 LineChart 与 W25 EEZChart）。

---

## 15. W15 Checkbox（复选框，Dashboard 变体）

**Description**：Dashboard 复选框。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Value | Boolean/EXPRESSION | — | 勾选状态。 |
| Label | String | — | 文字标签。 |
| Enabled | Boolean | true | 是否可用。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 16. W16 Checkbox（复选框，LVGL 变体）【重要】

**Description**：LVGL 原生复选框（`lv_checkbox`），带可表达式驱动的文字标签。

**所属族**：LVGL 通用族 + 以下专属属性。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Text | EXPRESSION (string) | — | 复选框右侧文字标签；支持表达式动态生成。 |
| Text type | Enum | Literal | Literal（直接使用文字）/ Expression（Text 作为表达式求值）。 |

**LVGL 特定说明（额外详细）**
- **映射**：`lv_checkbox_create(parent)` → `lv_checkbox_set_text(obj, text)`。文字通过 `Text` 属性设置；当 `Text type = Expression` 时，Studio 在生成代码前对表达式求值得到最终字符串。
- **坐标/尺寸**：由通用 `Left/Top/Width/Height`（px/%/content）控制；复选框尺寸通常随文字自动适应（Width/Height unit 取 `content` 较常见）。
- **状态**：勾选态由 `States.Checked`（EXPRESSION boolean）驱动，点击触发 CLICKED 事件并自动切换 `Checked`；可与 `Checkable` Flag 配合。
- **对 `json2eez` / `center_in`**：JSON 中 `specific.text` / `specific.textType` 应翻译为 `lv_checkbox_set_text`；`center_in` 居中应使用通用坐标或 Align 元数据，文字不影响布局盒。

---

## 17. W17 Colorwheel（颜色轮）

**Description**：LVGL 颜色选择器（`lv_colorwheel`）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Mode | Enum | HUE | HUE / SATURATION / VALUE（选择可调节的颜色分量）。 |
| Fixed mode | Boolean | — | 是否锁定模式（用户不可切换）。 |
| Knob recolor | Boolean | — | 是否用当前颜色给旋钮上色。 |

---

## 18. W18 Container（容器，EEZ-GUI 变体）

**Description**：EEZ-GUI 容器，用于布局与分组子 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |
| Layout | Enum | Static | Static / Horizontal / Vertical / Docking Manager（子 widget 排布方式）。 |
| Edit layout | — | — | 进入布局编辑模式。 |
| Tab title | EXPRESSION (string) | — | 当父容器为 Docking Manager 时，本容器所在标签页标题。 |

---

## 19. W19 Container（容器，Dashboard 变体）

**Description**：Dashboard 容器，用于分组与 Docking Manager 标签页。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |
| Layout | Enum | Static | Static / Horizontal / Vertical / Docking Manager。 |
| Edit layout | — | — | 进入布局编辑模式。 |
| Tab title | EXPRESSION (string) | — | Docking Manager 下本容器标签页标题。 |

---

## 20. W20 Container（容器，LVGL 变体）【重要】

**Description**：LVGL 容器对象（`lv_obj` 作为容器），用于布局与分组。

**所属族**：LVGL 通用族；**唯一专属属性为 `Tab title`**（位于 Layout 段，仅当父容器为 Docking Manager 时有意义）。

**LVGL 特定说明（额外详细）**
- **关键发现**：在 LVGL 变体中，**布局模式（FLEX / GRID）、内边距（pad）、对齐方式并不是作为 widget 的内联属性出现**，而是通过**分配给该容器的 LVGL Style 的 Layout 段**来配置（即 Style → Layout → FLEX 或 GRID，以及 Style 的 Padding 段）。这与 Dashboard/EEZ-GUI 变体（W18/W19 直接在 Layout 枚举中选 Horizontal/Vertical）不同。
- **坐标/尺寸**：通用 `Left/Top/Width/Height`（px/%/content）。作为容器时常用 `content` 或 `%` 自适应。
- **映射**：`lv_obj_create(parent)`；若 Style 含 FLEX/GRID 布局，则生成 `lv_obj_set_flex_flow` / `lv_obj_set_grid_...` 等。子 widget 的排布完全取决于该 Style 的 Layout 配置。
- **对 `json2eez` / `center_in` 的严重影响**：
  - `json2eez` 必须**读取容器所引用 Style 的 Layout 段**才能还原 flex/grid 行为；不能假设容器有内联 `layout` 字段。
  - `center_in` 居中逻辑若作用于该容器的子项，需先解析父容器 Style 的 flex/grid 方向，再决定是水平/垂直居中，而非简单取容器几何中心。
  - 内边距（pad left/right/top/bottom）同样来自 Style，影响子 widget 实际可用区域，流水线计算命中区时必须纳入。

---

## 21. W21 DisplayData（数据显示）

**Description**：显示数值/文本的只读数据 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 要显示的数据源。 |
| Display option | Enum | All | All / Integer / Fraction（显示全部 / 仅整数 / 仅小数）。 |
| Refresh rate | Number | — | 刷新率。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 22. W22 Dropdown（下拉框，Dashboard 变体）

**Description**：Dashboard 下拉选择框。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 数据来源（可表达式）。 |
| Options | — | — | 选项列表。 |
| Enabled | Boolean | true | 是否可用。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 23. W23 Dropdown（下拉框，EEZ-GUI 变体）

**Description**：EEZ-GUI 下拉选择框。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 数据来源。 |
| Options | — | — | 选项列表。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 24. W24 Dropdown（下拉框，LVGL 变体）【重要】

**Description**：LVGL 原生下拉列表（`lv_dropdown`）。

**所属族**：LVGL 通用族 + 以下专属属性。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Options | EXPRESSION (array:string) | — | 选项数组（字符串列表；LVGL 内部以 `\n` 连接）。支持表达式动态生成。 |
| Options type | Enum | Literal | Literal / Expression（Options 是否作为表达式求值）。 |
| Selected | EXPRESSION (int) | — | 当前选中项索引（从 0 起）。 |
| Selected type | Enum | Literal | Literal / Assignable（Assignable 表示可被运行时赋值改变）。 |
| Direction | Enum | — | 下拉展开方向：UP / DOWN。 |

**LVGL 特定说明（额外详细）**
- **映射**：`lv_dropdown_create(parent)` → `lv_dropdown_set_options(obj, "opt1\nopt2\nopt3")` → `lv_dropdown_set_selected(obj, idx)`。注意 LVGL 要求选项以换行符 `\n` 分隔，Studio 的 `Options` 数组在生成代码时会被join为 `\n` 字符串。
- **坐标/尺寸**：通用 `Left/Top/Width/Height`（px/%/content）。下拉框本体高度通常固定，展开列表高度由 LVGL 默认或 Style 控制。
- **选中态**：`Selected`（EXPRESSION int）驱动；`Selected type = Assignable` 时允许 Flow/动作在运行时改写选中项。
- **对 `json2eez` / `center_in`**：`json2eez` 需将 `Options` 数组转为 `\n` 分隔字符串再调用 `lv_dropdown_set_options`；`center_in` 仅依据下拉框本体几何（不展开列表）居中，方向 `Direction` 不影响布局盒。

---

## 25. W25 EEZChart（EEZ 图表）

**Description**：功能丰富的 EEZ 图表（支持单/多序列、EEZ DLOG、仪器历史项）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Chart mode | Enum | — | Single / Multiple / EEZ DLOG / Instrument History Item。 |
| Chart data | — | — | 图表数据来源。 |
| Format | Enum | — | float / double / rigol-byte / rigol-word / csv（数据格式）。 |
| Sampling rate | Number | — | 采样率。 |
| Unit name | String | — | 单位名。 |
| Color | — | — | 颜色。 |
| Label | String | — | 标签。 |
| Offset | Number | — | 偏移。 |
| Scale | Number | — | 缩放。 |
| Charts | Array | — | 多图表配置（Multiple 模式下列表）。 |
| History item ID | — | — | 仪器历史项 ID（Instrument History Item 模式）。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 26. W26 Embedded Dashboard（嵌入式仪表盘）

**Description**：在当前页面内嵌入另一个 Dashboard。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Dashboard | ObjectReference | — | 被嵌入的 Dashboard 对象引用。 |
| Open dashboard | — | — | 打开/导航到该 Dashboard 的动作配置。 |
| Dashboard parameters | Array | — | 传给被嵌入 Dashboard 的参数列表。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 27. W27 Gauge（仪表，Dashboard 变体）

**Description**：Dashboard 指针仪表。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 数据来源。 |
| Title | String | — | 标题。 |
| Min range | Number | — | 量程下限。 |
| Max range | Number | — | 量程上限。 |
| Color | — | — | 颜色。 |
| Margin | Number/Object | — | 边距。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 28. W28 Gauge（仪表，EEZ-GUI 变体）

**Description**：EEZ-GUI 仪表盘（Style 含 Default/Bar/Value/Ticks/Threshold）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 数据来源。 |
| Min | Number | — | 量程下限。 |
| Max | Number | — | 量程上限。 |
| Threshold | Number | — | 阈值。 |
| Unit | String | — | 单位。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 29. W29 Grid（网格）

**Description**：以网格方式重复渲染子 widget，使用 `$index` 系统变量区分内容。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 决定子 widget 重复次数的数据（整数或数组长度）。 |
| Grid flow | Enum | Row | Row（先填满行）/ Column（先填满列）。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

> 与 W40/W41 List 类似，使用零基系统变量 `$index` 在子 widget 表达式中取值（如 `country_cities[$index].country`）。

---

## 30. W31 Image（图像）【重要·LVGL 变体】

**Description**：LVGL 图像对象（`lv_img`），支持旋转、缩放、枢轴与（scale needle 模式下的）指针值。

**所属族**：LVGL 通用族 + 以下专属属性。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Image | ObjectReference | — | 引用的图像对象（位图/符号）。 |
| Change pivot point | Boolean | — | 是否自定义旋转/缩放枢轴点。 |
| Pivot X | Number | — | 枢轴 X（Change pivot point 启用时）。 |
| Pivot Y | Number | — | 枢轴 Y。 |
| Scale | Number | 256 | 缩放系数；**256 表示无缩放**（256 = 100%）。 |
| Rotation | Number | — | 旋转角度，精度为 **0.1°**（如 10 表示 1.0°）。 |
| Inner align | — | — | 内部对齐方式。 |
| Value | EXPRESSION (int) | — | scale needle 模式下指针值（仅当作为 Scale 子 widget 时可见）。 |
| Value type | Enum | Literal | Literal / Expression（Value 是否按表达式求值）。 |
| Preview value | String | — | 编辑器内预览用的指针值（仅 Value type=Expression 时可用）。 |

**LVGL 特定说明（额外详细）**
- **映射**：`lv_img_create(parent)` → `lv_img_set_src(obj, img_src)` → `lv_img_set_pivot` / `lv_img_set_scale(obj, scale)`（注意 LVGL 的 scale 单位：256 = 原始尺寸）/ `lv_img_set_angle(obj, angle)`（LVGL angle 单位为 0.1°）。
- **坐标/尺寸**：通用 `Left/Top/Width/Height`（px/%/content）。`content` 模式下尺寸贴合图像原始大小。
- **scale needle 模式**：当 Image 作为 Scale widget 的子项时，`Value`/`Value type`/`Preview value` 出现，用于把图像当作指针按值旋转；此情形下 Image 本质是 `lv_img` 叠加在 `lv_scale` 之上。
- **对 `json2eez` / `center_in`**：`Scale=256` 必须原样映射为 LVGL 的 256（非 1.0）；`Rotation` 需 ×10 转为 LVGL angle；`center_in` 居中基于图像几何盒（旋转后包围盒由 LVGL 计算，Studio 元数据以未旋转盒为准）。

---

## 31. W32 Input（输入框，EEZ-GUI 变体）

**Description**：EEZ-GUI 文本/数字输入 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION | — | 输入数据绑定。 |
| Input type | Enum | — | Number / Text。 |
| Min | Number | — | 数值下限（Number 模式）。 |
| Max | Number | — | 数值上限。 |
| Precision | Number | — | 小数位数。 |
| Unit | String | — | 单位后缀。 |
| Password | Boolean | — | 是否为密码框（掩码显示）。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 33. W33 InstrumentTerminal（仪器终端）

**Description**：连接仪器的终端/控制台 widget。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Instrument | ObjectReference | — | 绑定的仪器对象。 |
| Show connection status bar | Boolean | — | 显示连接状态栏。 |
| Show shortcuts | Boolean | — | 显示快捷键栏。 |
| Show help | Boolean | — | 显示帮助。 |
| Show side bar | Boolean | — | 显示侧边栏。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

---

## 34. W34 Keyboard（键盘）

**Description**：屏幕软键盘，用于向 Textarea 输入。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Textarea | Enum | — | 目标 Textarea 引用（键盘输入写入的对象）。 |
| Mode | Enum | — | TEXT_LOWER / TEXT_UPPER / SPECIAL / NUMBER / USER_1 / USER_2 / USER_3 / USER_4（键盘布局模式）。 |

---

## 35. W35 Label（标签）【重要·LVGL 变体】

**Description**：LVGL 文本标签（`lv_label`），最常用文本显示 widget。

**所属族**：LVGL 通用族 + 以下专属属性。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Text | EXPRESSION (string) | — | 标签文字；支持表达式动态生成。 |
| Text type | Enum | Literal | Literal / Expression（Text 是否作为表达式求值）。 |
| Preview value | String | — | 编辑器内预览文字（仅 Text type=Expression 时可用）。 |
| Long mode | Enum | WRAP | 长文本处理：WRAP（换行）/ DOT（省略号截尾）/ SCROLL（滚动）/ SCROLL_CIRCULAR（循环滚动）/ CLIP（裁剪）。 |
| Recolor | Boolean | false | 是否解析文本内嵌颜色指令（如 `#ff0000 红#`）。 |

**LVGL 特定说明（额外详细）**
- **映射**：`lv_label_create(parent)` → `lv_label_set_text(obj, text)`（或 `lv_label_set_text_fmt`）；`Long mode` 映射 `lv_label_set_long_mode`（WRAP/DOT/SCROLL/SCROLL_CIRCULAR/CLIP）；`Recolor` 映射 `lv_label_set_recolor`。
- **坐标/尺寸**：通用 `Left/Top/Width/Height`（px/%/content）。`Width unit=content` 时常配合 `Long mode=WRAP` 自动按宽换行；`Long mode=SCROLL` 通常需要固定 Width。
- **动态文字**：`Text type=Expression` 时，Studio 在生成代码前对 `Text` 表达式求值得到最终字符串传给 `lv_label_set_text`。
- **对 `json2eez` / `center_in`**：`json2eez` 将 `Text`/`Preview value` 转为 `lv_label_set_text`；`Recolor` 需在文本中保留 `#rrggbb 文字#` 语法；`center_in` 居中依据标签几何盒（SCROLL 模式下为视口盒，非完整文本长度）。

---

## 36. W36 Led（LED）【LVGL 族】

**Description**：LVGL LED 对象（`lv_led`），矩形或圆形，亮度可调（亮度越低颜色越暗）。

**所属族**：LVGL 通用族 + 以下专属属性（位于 Specific 段）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Color | EXPRESSION (integer) | — | LED 颜色（同时用作背景/边框/阴影色）。 |
| Color type | Enum | Literal | 是否按表达式计算 Color。 |
| Brightness | EXPRESSION (integer) | — | 亮度，范围 **0（最暗）– 255（最亮）**。 |
| Brightness type | Enum | Literal | 是否按表达式计算 Brightness。 |

**LVGL 说明**：映射 `lv_led_create(parent)` → `lv_led_set_color` / `lv_led_set_brightness`。其余坐标/Flags/States/Events 同附录 A。

---

## 37. W37 Line（线）【LVGL 族】

**Description**：LVGL 线段对象（`lv_line`），在一组点之间绘制直线；也可作为 Scale 的子项充当指针（scale needle 模式）。

**所属族**：LVGL 通用族 + 以下专属属性。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Points | String | — | 点列表，格式 `x1,y1 x2,y2 x3,y3 ...`（例：`0,0 50,50 100,0 150,50 200,0`）。 |
| Invert Y | Boolean | false | 是否翻转 Y 轴（默认 y==0 在顶部；开启后 y==0 在底部）。 |
| Needle length | Number | — | 指针线长度（像素），仅 scale needle 模式可见。 |
| Value | EXPRESSION (integer) | — | 指针在 Scale 上的值，仅 scale needle 模式。 |
| Value type | Enum | Literal | Literal / Expression（Value 是否按表达式求值）。 |
| Preview value | String | — | 编辑器预览指针值，仅 Value type=Expression 时。 |

**LVGL 说明**：映射 `lv_line_create(parent)` → `lv_line_set_points`。scale needle 模式下作为 `lv_scale` 子对象，由 `Value` 驱动角度。

---

## 38. W38 LineChart（折线图，Dashboard 变体）

**Description**：Dashboard 折线图，含标题/X轴/Y轴/图例/网格/多条线；通过 `value` 输入逐点追加。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| X value | EXPRESSION (any) | — | 新增点的 X 轴值（可用 `Date.now()`，需逐点递增）。 |
| Lines | Array | — | 一条或多条线，每项含 Label（图例名）/ Color（线色）/ Value（Y 值）。 |
| Title | String | — | 图表标题。 |
| Display mode bar | Enum | — | Hover / Always / Never（模式工具条显示时机）。 |
| Show legend | Boolean | — | 显示图例。 |
| Show grid | Boolean | — | 显示网格。 |
| Show zero lines | Boolean | — | 显示零线。 |
| Show X axis | Boolean | — | 显示 X 轴。 |
| X axis tick suffix | String | — | X 轴刻度后缀（单位）。 |
| X axis range option | Enum | Floating | Floating（自动）/ Fixed（用 from/to 固定）。 |
| X axis range from | EXPRESSION (double) | — | X 轴下限（Fixed 时）。 |
| X axis range to | EXPRESSION (double) | — | X 轴上限（Fixed 时）。 |
| Show Y axis | Boolean | — | 显示 Y 轴。 |
| Y axis tick suffix | String | — | Y 轴刻度后缀。 |
| Y axis range option | Enum | Floating | Floating / Fixed。 |
| Y axis range from | EXPRESSION (double) | — | Y 轴下限。 |
| Y axis range to | EXPRESSION (double) | — | Y 轴上限。 |
| Max points | EXPRESSION (integer) | — | 最多显示点数（超出删最旧）。 |
| Margin | Object | — | 图表与边框的手动边距（Top 留给标题、Bottom 给 X 轴、Left 给 Y 轴、Right 给图例）。 |
| Marker | EXPRESSION (float) | — | 在此位置用 Marker 样式画一条竖线。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |

**输入（Flow Inputs）**：`reset`（OPTIONAL，清空所有点）、`value`（MANDATORY，追加一个点；达 Max points 后删最旧）。
**专属 Flow 输出**：`Output widget handle`（Boolean，开启后增加 `@Widget` 输出，发送 widget 引用，可用于 `AddToInstrumentHistory` 的 Plotly widget 属性）。

---

## 39. W39 LineChart（折线图，EEZ-GUI 变体）

**Description**：EEZ-GUI 折线图，结构与 Dashboard 变体类似但属性更细（含 Line width、各部件独立 Style）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| X value | EXPRESSION (any) | — | 新增点 X 值。 |
| Lines | Array | — | 每条线含 Label / Color / **Line width**（线宽像素）/ Value。 |
| Show title | EXPRESSION (boolean) | — | 显示标题。 |
| Show legend | EXPRESSION (boolean) | — | 显示图例。 |
| Show X axis | EXPRESSION (boolean) | — | 显示 X 轴。 |
| Show Y axis | EXPRESSION (boolean) | — | 显示 Y 轴。 |
| Show grid | EXPRESSION (boolean) | — | 显示网格。 |
| Title | EXPRESSION (string) | — | 图表标题。 |
| Y axis range option | Enum | Floating | Floating / Fixed。 |
| Y axis range from | EXPRESSION (double) | — | Y 下限。 |
| Y axis range to | EXPRESSION (double) | — | Y 上限。 |
| Max points | Number | — | 最多点数。 |
| Margin | Object | — | 边距（同 W38 说明）。 |
| Marker | EXPRESSION (float) | — | 竖线标记位置。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |
| Hide "Widget is outside of its parent" warning | Boolean | — | 隐藏越界警告。 |

**Style 对象**：Default / Title / Legend / X axis / Y axis / Marker（各部件独立样式）。
**输入**：`reset`、`value`（同 W38）。

---

## 40. W40 List（列表，EEZ-GUI 变体）

**Description**：将**一个子 widget** 按 `Data` 指定的次数重复渲染；用零基系统变量 `$index` 在子 widget 表达式中产生不同内容。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION (any) | — | 重复次数：整数=元素个数；数组=数组长度；EEZ-GUI 下还可为 `struct:$ScrollbarState`（连接 ScrollBar 实现滚动）。 |
| List type | Enum | — | 垂直 / 水平方向。 |
| Gap | Number | — | 子项间距（像素）。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |
| Hide "Widget is outside of its parent" warning | Boolean | — | 隐藏越界警告。 |

**示例**：`eez-gui-widgets-demo`、`CSV`、`JSON`、`MQTT`、`Simple HTTP`、`Charts`、`Regexp String`、`Multi-Language`。

---

## 41. W41 List（列表，Dashboard 变体）

**Description**：与 W40 同构的 Dashboard 列表 widget（重复渲染子 widget + `$index`）。

**Specific 属性**

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Data | EXPRESSION (any) | — | 重复次数（整数/数组/`struct:$ScrollbarState`）。 |
| List type | Enum | — | 垂直 / 水平。 |
| Gap | Number | — | 子项间距（像素）。 |
| Visible | EXPRESSION (boolean) | — | 可见性表达式。 |
| Hide "Widget is outside of its parent" warning | Boolean | — | 隐藏越界警告。 |

**示例**：同 W40 列出的全部 demo。

---

## 42. W43 List（列表，LVGL 变体）【重要】

> 注：原文编号为 W42（List LVGL）与 W43（Lottie）。此处按用户清单 W42 = List (LVGL)、W43 = Lottie。

**W42 List (LVGL)**
**Description**：LVGL 列表对象（`lv_list`）。**Work in progress**——Studio 会生成完整创建代码，但多于创建之外的功能需在自定义代码中实现（如 `ui_init()` 之后）。

**所属族**：**纯 LVGL 通用族**，无 Specific 属性（直接进 General / Position&Size / Layout(Tab title) / Use style / Flags / States / Events / Flow，见附录 A）。

**LVGL 特定说明（额外详细）**
- **与 W40/W41 的本质区别**：Dashboard/EEZ-GUI 的 List 通过 `Data` + `$index` **自动重复渲染子 widget**；而 **LVGL 变体的 List 没有 `Data` / `$index` / `Gap` 等专属属性**，不自动做子项乘法。列表项（lv_list_add_text / lv_list_add_btn）需由**后续自定义代码**添加。
- **映射**：`lv_list_create(parent)` → `lv_list_add_text` / `lv_list_add_btn`。坐标/尺寸通用。
- **对 `json2eez` / `center_in`**：`json2eez` 只能生成空 `lv_list` 容器；若期望自动列表，流水线须识别此限制并提示用户用自定义代码补全。`center_in` 仅针对列表容器几何盒居中。

---

## 43. W43 Lottie（Lottie 动画）【LVGL 族】

**Description**：Lottie 矢量动画播放 widget。**Work in progress**——Studio 生成创建代码，其余在自定义代码（如 `ui_init()` 后）完成。

**所属族**：**纯 LVGL 通用族**，无 Specific 属性（LVGL 通用集见附录 A）。

**LVGL 说明**：底层对应 LVGL 的 Lottie / 矢量动画对象；动画资源与播放控制通过自定义代码设置。坐标/尺寸/Flags/States 同附录 A。

---

# 附录 A：公共 LVGL 族属性（W10, W13, W14, W16, W20, W24, W30, W35, W36, W37, W42, W43 及所有 LVGL 变体通用）

> 以下属性在 LVGL 族 widget 中逐字重复出现，仅在此记录一次。每个 LVGL widget 的正文 Properties 仅列其 **Specific** 部分，其余均指回本附录。

**General**
| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Name | String | 空 | widget 名称，用于 LVGL action 中引用；工程内需唯一，可选。 |
| Group | ObjectReference | — | 所属输入组名。 |
| Group index | Number | 0 | 组内顺序（类似 HTML tabindex）。0=按结构顺序；>0 在 0 与前序小于它的索引之前；同值按结构顺序。 |

**Position and size**
| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Left | Number | 0 | 相对页面/父 widget 的 X（像素，支持表达式）。 |
| Left unit | Enum | px | px / %（相对父宽）。 |
| Top | Number | 0 | Y 坐标。 |
| Top unit | Enum | px | px / %（相对父高）。 |
| Width | Number | — | 宽度（像素）。 |
| Width unit | Enum | px | px / %（相对父宽）/ content（贴合内容宽）。 |
| Height | Number | — | 高度（像素）。 |
| Height unit | Enum | px | px / %（相对父高）/ content（贴合内容高）。 |
| Absolute pos. | String | — | 相对页面的绝对位置（只读）。 |
| Align and distribute | Any | — | 对齐/分布图标（多选时）。 |
| Center widget | Any | — | 水平/垂直居中图标。 |

**Layout**
| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Tab title | EXPRESSION (string) | — | 父容器为 Docking Manager 时，本 widget 所在标签页标题。 |

**Style**
| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Use style | ObjectReference | — | 选用全局定义的 Style。 |

**Flags**（均为 Boolean，除注明外默认未勾选；带 `… flag type` 者可选 Literal/Expression 动态驱动）
| 属性 | 类型 | 含义 |
|---|---|---|
| Hidden | EXPRESSION (boolean) | 隐藏对象。 |
| Hidden flag type | Enum | Hidden 是否按表达式计算。 |
| Clickable | EXPRESSION (boolean) | 可被输入设备点击。 |
| Clickable flag type | Enum | Clickable 是否按表达式。 |
| Click focusable | Boolean | 点击时加 focused 态。 |
| Checkable | Boolean | 点击切换 checked 态。 |
| Scrollable | Boolean | 可滚动。 |
| Scroll elastic | Boolean | 内部慢速滚动。 |
| Scroll momentum | Boolean | 抛出后继续滚动。 |
| Scroll one | Boolean | 仅一个可吸附子项滚动。 |
| Scroll chain hor | Boolean | 水平滚动向父传播。 |
| Scroll chain ver | Boolean | 垂直滚动向父传播。 |
| Scroll on focus | Boolean | 聚焦时自动滚入视野。 |
| Scroll with arrow | Boolean | 方向键滚动聚焦对象。 |
| Snappable | Boolean | 父开启 snap 时可吸附到本对象。 |
| Press lock | Boolean | 按下滑出仍保持按下。 |
| Event bubble | Boolean | 事件向父传播。 |
| Gesture bubble | Boolean | 手势向父传播。 |
| Adv hittest | Boolean | 更精确命中测试（如圆角）。 |
| Ignore layout | Boolean | 可被布局定位。 |
| Floating | Boolean | 父滚动时不滚且忽略布局。 |
| Overflow visible | Boolean | 不裁剪子内容到父边界。 |
| Scrollbar mode | Enum | OFF / ON / ACTIVE / AUTO（滚动条显示模式）。 |
| Scroll direction | Enum | NONE / TOP / LEFT / BOTTOM / RIGHT / HOR / VER / ALL。 |
| Scroll snap X | Enum | NONE / START / END / CENTER（水平吸附对齐）。 |
| Scroll snap Y | Enum | NONE / START / END / CENTER（垂直吸附对齐）。 |

**States**
| 属性 | 类型 | 含义 |
|---|---|---|
| Checked | EXPRESSION (boolean) | 选中/切换态。 |
| Checked state type | Enum | Checked 是否按表达式。 |
| Disabled | EXPRESSION (boolean) | 禁用态。 |
| Disabled state type | Enum | Disabled 是否按表达式。 |
| Focused | Boolean | 通过键盘/编码器/触摸聚焦。 |
| Focus key | Boolean | 仅键盘/编码器聚焦（非触摸）。 |
| Pressed | Boolean | 被按下。 |

**Events**
| 属性 | 类型 | 含义 |
|---|---|---|
| Event handlers | Array | 事件处理列表；每项含 Event（如 CLICKED）、Handler type（Flow/Action）、Action（Action 时指定的用户动作名）。 |

**Flow**
| 属性 | 类型 | 含义 |
|---|---|---|
| Inputs | Array | 自定义输入，供属性表达式中引用（名+类型）。 |
| Outputs | Array | 自定义输出，发送数据（名+类型）。 |
| Catch error | Boolean | 开启后增加 `@Error` 输出，错误时流经该输出（文本错误描述）。 |

---

# 附录 B：公共 Dashboard / EEZ-GUI 族属性（W1–W9, W11, W12, W15, W17–W19, W21–W29, W31–W34, W38–W41 通用）

> 以下属性在 Dashboard / EEZ-GUI 族 widget 中重复出现，仅记录一次。

**Position and size（Dashboard/EEZ-GUI 版）**
| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| Resizing | Any | — | 页面开启 "Scale to fit" 时的缩放行为：Pin to edge（固定上/右/下/左边缘相对页面距离）与 Fix size（固定宽/高）。注意 Pin 左+右 与 Fix width 互斥，Pin 上+下 与 Fix height 互斥。 |
| Left / Top / Width / Height | Number | — | 像素坐标/尺寸，支持表达式（+ - * / 及括号）。 |
| Hide "Widget is outside of its parent" warning | Boolean | — | 隐藏越界警告（部分 widget 有）。 |
| Absolute pos. / Align and distribute / Center widget | — | — | 同 LVGL 族对应项。 |

**Visible**
| 属性 | 类型 | 含义 |
|---|---|---|
| Visible | EXPRESSION (boolean) | 表达式为真可见；留空则始终可见。 |

**Style 对象引用**（不同 widget 引用不同子集，常见：Default / Text / Bar / Value / Ticks / Threshold / Focused / Disabled；W38 含 Default / Marker；W39 含 Default / Title / Legend / X axis / Y axis / Marker）
| 属性 | 类型 | 含义 |
|---|---|---|
| （各部件）Style | Object | 引用全局 Style 渲染对应部件。 |

**Events / Flow**（同附录 A 的 Event handlers / Inputs / Outputs / Catch error；部分 widget 额外有 Output widget handle：开启后增加 `@Widget` 输出发送 widget 引用，如 W38）
| 属性 | 类型 | 含义 |
|---|---|---|
| Event handlers | Array | 同附录 A。 |
| Output widget handle | Boolean | 仅部分 widget：增加 `@Widget` 输出（widget 引用）。 |
| Inputs / Outputs / Catch error | — | 同附录 A。 |

---

# 索引

| 编号 | Widget | 变体 | 关键专属属性 | 备注 |
|---|---|---|---|---|
| W1 | AnimationImage | D/EG | Images, Duration, Repeat infinite/count | |
| W2 | Arc | D/EG | Range min/max, Value, Mode, angles | |
| W3 | Bar | D/EG | Min/Max, Mode, Value, Enable animation | |
| W4 | BarGraph | D/EG | Data, Orientation, Thresholds, Min/Max | |
| W5 | Bitmap | Dashboard | Data, Bitmap, Visible | |
| W6 | Bitmap | EEZ-GUI | Data(expr), Bitmap, Visible | |
| W7 | Button | Dashboard | Label, Enabled, Visible | |
| W8 | Button | EEZ-GUI | Label, Enabled, Visible | |
| W9 | ButtonGroup | D/EG | Button labels, Selected button | |
| W10 | Button | LVGL | （无） | 见 §10 |
| W11 | ButtonMatrix | D/EG | Buttons(含标志), One check | |
| W12 | Calendar | D/EG | Year, Month, Day | |
| W13 | Canvas | LVGL | （无） | |
| W14 | Chart | LVGL | （无） | |
| W15 | Checkbox | Dashboard | Value, Label, Enabled | |
| W16 | Checkbox | LVGL | Text(expr), Text type | 见 §16 |
| W17 | Colorwheel | D/EG | Mode, Fixed mode, Knob recolor | |
| W18 | Container | EEZ-GUI | Visible, Layout, Edit layout, Tab title | |
| W19 | Container | Dashboard | Visible, Layout, Edit layout, Tab title | |
| W20 | Container | LVGL | Tab title（布局走 Style） | 见 §20 |
| W21 | DisplayData | D/EG | Data, Display option, Refresh rate | |
| W22 | Dropdown | Dashboard | Data, Options, Enabled | |
| W23 | Dropdown | EEZ-GUI | Data, Options | |
| W24 | Dropdown | LVGL | Options(expr arr), Selected, Direction | 见 §24 |
| W25 | EEZChart | D/EG | Chart mode, Format, Charts, History item ID | |
| W26 | Embedded Dashboard | D/EG | Dashboard, Parameters | |
| W27 | Gauge | Dashboard | Data, Min/Max range, Color, Margin | |
| W28 | Gauge | EEZ-GUI | Data, Min/Max, Threshold, Unit | |
| W29 | Grid | D/EG | Data, Grid flow, `$index` | |
| W30 | Image | LVGL | Image, Scale(256), Rotation(0.1°), Pivot | 见 §30 |
| W31 | Imgbutton | D/EG | Released/Pressed/Disabled/Checked 图像组 | |
| W32 | Input | EEZ-GUI | Input type, Min/Max, Precision, Password | |
| W33 | InstrumentTerminal | D/EG | Instrument, 各 Show 开关 | |
| W34 | Keyboard | D/EG | Textarea, Mode | |
| W35 | Label | LVGL | Text(expr), Long mode, Recolor | 见 §35 |
| W36 | Led | LVGL | Color, Brightness(0–255) | |
| W37 | Line | LVGL | Points, Invert Y, scale needle | |
| W38 | LineChart | Dashboard | X/Y value, Lines, ranges, Marker | |
| W39 | LineChart | EEZ-GUI | 同 W38 + Line width + 独立 Style | |
| W40 | List | EEZ-GUI | Data, List type, Gap, `$index` | |
| W41 | List | Dashboard | Data, List type, Gap, `$index` | |
| W42 | List | LVGL | （无；需自定义代码加项） | 见 §42 |
| W43 | Lottie | LVGL | （无；work in progress） | |
