# EEZ Studio Widgets 参考笔记（第二部分：W44 – W87）

> 资料来源：`reference_guide_raw.txt`（EEZ Studio Reference Guide 纯文本转储，共 784 页）。
> 本文件覆盖 Widget 编号 **W44 ~ W87**，含同一 Widget 的多种变体（Dashboard / EEZ-GUI / LVGL）。
> 标注【重要】的 LVGL 变体（W56、W61、W67、W71、W74、W78、W80、W83、W84）在本文件中额外给出“LVGL 对象映射”与“json2eez 流水线相关属性”说明。
>
> 约定：属性类型保持原文英文（如 `String`、`EXPRESSION (integer)`、`Enum`、`Boolean`、`ThemedColor`、`ObjectReference`、`array:string`、`json`、`struct:$ScrollbarState` 等）；中文为释义。

---

## 0. 通用属性组（所有 Widget 共享）

本指南中每个 Widget 的属性都按固定分组展开：**General → Position and size → Layout → Style → Flags → States → Events → Flow**。
为避免 44 个 Widget 重复罗列，下面把“通用分组”完整记录一次；每个 Widget 的子节只记录其 **Specific（特有）属性**，并注明它适用哪些通用分组。

### 0.1 General（标识与输入分组）
| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Name | String | （空） | Widget 名称，整个项目中必须唯一。用于 LVGL action 等场景按名引用；不引用时可留空。 |
| Group | ObjectReference | （空） | 该 Widget 所属“输入分组”的名称。 |
| Group index | Number | 0 | 分组内排序，类似 HTML 的 tabindex：0 表示按 Widgets Structure 顺序；>0 的会排在 0 及更大值之前；相同值之间保持结构内顺序。 |

### 0.2 Position and size（位置与尺寸）
| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Left | Number | 0 | 相对页面/父 Widget 的 X 像素坐标。支持 `+ - * /` 与括号的数学表达式（如 `18 + 36`、`(100 - 32) / 2`），回车即求值。 |
| Left unit | Enum | px | `px`（默认像素）或 `%`（相对父宽度百分比）。 |
| Top | Number | 0 | 相对页面/父 Widget 的 Y 像素坐标。 |
| Top unit | Enum | px | `px` 或 `%`（相对父高度百分比）。 |
| Width | Number | 0 | 宽度（像素）。 |
| Width unit | Enum | px | `px` / `%` / `content`（自动适应内容宽度）。 |
| Height | Number | 0 | 高度（像素）。 |
| Height unit | Enum | px | `px` / `%` / `content`（自动适应内容高度）。 |
| Absolute pos. | String | （只读） | 相对页面的绝对位置，只读。 |
| Align and distribute | Any | （无） | 对齐与分布图标（选 2+ 显示对齐，3+ 显示分布）。 |
| Center widget | Any | （无） | 水平/垂直居中图标。 |

> **Dashboard / EEZ-GUI 变体的差异**：这类 Widget 没有 `Left unit/Top unit/Width unit/Height unit` 的 `%`/`content` 细分，而是用：
> - **Resizing**（Any）：页面启用 “Scale to fit” 时控制缩放行为，含 Pin to edge（固定四边）与 Fix size（固定宽高）选项（互斥规则：同时 Pin 左右边会禁用 Fix width，反之亦然；上下边同理）。
> - **Hide "Widget is outside of its parent" warning**（Boolean）：勾选可隐藏越界警告。

### 0.3 Layout
| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Tab title | EXPRESSION (string) | （空） | 当 Widget 位于“Docking Manager”布局容器内时，设置其所在 Tab 的标题。 |

### 0.4 Style
| 名称 | 类型 | 适用 | 含义 |
|------|------|------|------|
| Use style | ObjectReference | LVGL 变体 | 选用一个全局定义的 Style。 |
| Default | Object | Dashboard / EEZ-GUI 变体 | 渲染 Widget 时使用的样式（背景等）。 |

### 0.5 Flags（仅 LVGL 变体，约 24 项）
| 名称 | 类型 | 含义 |
|------|------|------|
| Hidden | EXPRESSION (boolean) | 隐藏对象。 |
| Hidden flag type | Enum | Hidden 状态是否由表达式计算（Literal / Expression）。 |
| Clickable | EXPRESSION (boolean) | 允许被输入设备点击。 |
| Clickable flag type | Enum | Clickable 状态是否由表达式计算。 |
| Click focusable | Boolean | 点击时添加 focused 状态。 |
| Checkable | Boolean | 点击时切换 checked 状态（开/关、选中/未选中）。 |
| Scrollable | Boolean | 可滚动。 |
| Scroll elastic | Boolean | 允许内部滚动但速度更慢。 |
| Scroll momentum | Boolean | 被“甩动”后继续滚动。 |
| Scroll one | Boolean | 一次只允许滚动一个可吸附子对象。 |
| Scroll chain hor | Boolean | 允许将水平滚动传递给父对象。 |
| Scroll chain ver | Boolean | 允许将垂直滚动传递给父对象。 |
| Scroll on focus | Boolean | 聚焦时自动滚动使其可见。 |
| Scroll with arrow | Boolean | 允许用方向键滚动聚焦对象。 |
| Snappable | Boolean | 父对象启用 snap 时可吸附到此对象。 |
| Press lock | Boolean | 即使指针滑出对象也保持按下。 |
| Event bubble | Boolean | 事件向上传递给父对象。 |
| Gesture bubble | Boolean | 手势向上传递给父对象。 |
| Adv hittest | Boolean | 更精确的命中（点击）测试（如圆角）。 |
| Ignore layout | Boolean | 可被布局定位。 |
| Floating | Boolean | 父滚动时不滚动且忽略布局。 |
| Overflow visible | Boolean | 不裁剪子对象到父边界。 |
| Scrollbar mode | Enum | `OFF`（从不显示）/ `ON`（总是显示）/ `ACTIVE`（滚动时显示）/ `AUTO`（内容足够大时显示）。 |
| Scroll direction | Enum | `NONE`/`TOP`/`LEFT`/`BOTTOM`/`RIGHT`/`HOR`/`VER`/`ALL`。 |
| Scroll snap X | Enum | `NONE`（默认）/ `START`/`END`/`CENTER`。 |
| Scroll snap Y | Enum | `NONE`（默认）/ `START`/`END`/`CENTER`。 |

### 0.6 States（仅 LVGL 变体）
| 名称 | 类型 | 含义 |
|------|------|------|
| Checked | EXPRESSION (boolean) | 切换/选中状态（如 Switch 开、Checkable 对象按下）。 |
| Checked state type | Enum | Checked 是否由表达式计算。 |
| Disabled | EXPRESSION (boolean) | 禁用状态。 |
| Disabled state type | Enum | Disabled 是否由表达式计算。 |
| Focused | Boolean | 通过键盘/编码器聚焦，或触摸/鼠标点击聚焦。 |
| Focus key | Boolean | 仅通过键盘/编码器聚焦（非触摸/鼠标）。 |
| Pressed | Boolean | 正在被按下。 |

### 0.7 Events
| 名称 | 类型 | 含义 |
|------|------|------|
| Event handlers | Array | 事件处理器列表。每个处理器需定义：`Event`（如 CLICKED）、`Handler type`（`Flow` 或 `Action`）、`Action`（当 Handler type=Action 时指定要执行的用户动作名）。 |

### 0.8 Flow（数据流）
| 名称 | 类型 | 含义 |
|------|------|------|
| Inputs | Array | 自定义输入，每条含 名称+类型，供属性表达式引用。 |
| Outputs | Array | 自定义输出，每条含 名称+类型，可向外发送数据。 |
| Catch error | Boolean | 启用后增加 `@Error` 输出，Flow 出错时走该输出（数据为错误文本）。 |
| Output widget handle | Boolean | 启用后增加 `@Widget` 输出，创建时发送 widget 类型句柄（如供 AddToInstrumentHistory 的 Plotly widget 引用）。 |

---

## W44. Markdown
### Description
用于显示 Markdown 文本的 Widget。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | MultilineText | 要显示的 Markdown 文本。 |
| Visible | EXPRESSION (boolean) | 表达式为真时可见，为假时隐藏；留空则始终可见。 |
### 适用通用分组
Position and size（含 Dashboard 风格的 Resizing）、Layout、Style（Default）、Events。
### Examples
- 将 Markdwon 文本填入 `Text`；用 `Resizing` 的 Pin to edge / Fix size 配合页面 “Scale to fit”。

---

## W45. Menu
### Description
**Work in progress**：可加入项目并生成创建代码，但更多功能需自定义代码（如 `ui_init()` 之后）。
### Specific 属性
无特有属性（仅有通用 General / Position and size / Layout / Style / Flags / States / Events / Flow）。
### 适用通用分组
全部通用分组（按 LVGL 模式）。
### Examples
- 该 Widget 当前仅生成骨架，自定义行为写在 `ui_init()` 之后的代码里。

---

## W46. MessageBox
### Description
**Work in progress**：同上，仅生成创建代码，更多逻辑需自定义。
### Specific 属性
无特有属性。
### 适用通用分组
全部通用分组（LVGL 模式）。

---

## W47. Meter
### Description
Meter Widget 以非常灵活的方式可视化数据：可显示弧线（arc）、指针（needle，含 image/line）、刻度线（scale lines）与标签（labels）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Scales | Array | 刻度定义列表。每个刻度有 次刻度（minor）/主刻度（major）及主刻度上的标签；每个刻度可挂 1~多个指示器，指示器共 4 类：**Needle image**、**Needle line**、**Scale lines**、**Arc**。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。

---

## W48. MultilineText
### Description
用于显示多行文本的 Widget。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | EXPRESSION (any) | 要显示的文本。若是静态文本需加引号；若用变量则编辑器无法计算，会直接显示表达式本身。 |
| Visible | EXPRESSION (boolean) | 同上可见性逻辑。 |
| Resizing | Any | 见 0.2 的 Dashboard 差异说明（Pin to edge / Fix size）。 |
| Hide "Widget is outside of its parent" warning | Boolean | 隐藏越界警告。 |
| Name（位于 General 组内，作编辑期显示名） | String | 当 Text 表达式无法在编辑期计算时，这里可设编辑器内显示的文本（也会出现在 Widgets Structure 面板）。 |
### 适用通用分组
Position and size（Dashboard 风格）、Layout、General（含编辑期 Name）、Style（Default）、Events。
### Examples
- 静态显示：`Text` 填 `"Hello\nWorld"`；变量文本：`Text` 填 `someVar`。

---

## W49. NumberInput
### Description
用于输入数字的 Widget。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (double) | 存储输入数字值的变量。 |
| Min | EXPRESSION (double) | 可输入的最小值。 |
| Max | EXPRESSION (double) | 可输入的最大值。 |
| Step | EXPRESSION (double) | 数值需遵循的粒度（步长）。 |
| Disable default tab handling | Boolean | 设为 false（原文提示“设为 false 以禁用”，实际语义：关闭默认 TAB 键处理）可在该 Widget 聚焦时禁用默认 TAB 切换。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events、Flow。

---

## W50. Panel
### Description
用于把多个 Widget 分组/组织的容器：当页面 Widget 很多，或想对一组 Widget 批量操作（如用 Panel 的 Hidden 标志整体隐藏）。Panel 内的 Widget 其 Left/Top 相对 Panel 的左上角；移动 Panel 时内部 Widget 一起移动。通过 Widgets Structure 面板拖放加入。
### Specific 属性
无（纯容器，仅有通用属性）。
### 适用通用分组
General、Position and size、Layout、Style（Use style / Default 视变体）、Flags、States、Events、Flow。

---

## W51. Plotly
### Description
通过 JSON 指定 chart data / layout / configuration options 来显示 Plotly 图表的 Widget。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Chart data | EXPRESSION (json) | 图表数据，详见 Plotly 文档。 |
| Layout options | EXPRESSION (json) | 布局选项，详见 Plotly 文档。 |
| Configuration options | EXPRESSION (json) | 配置选项，详见 Plotly 文档。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Events、Flow（含 Output widget handle，供 AddToInstrumentHistory 的 Plotly widget 引用）。
### Examples
- `Chart data` 用标准 Plotly trace JSON；`Layout options` 控制标题/轴；`Configuration options` 控制交互。

---

## W52. Progress (Dashboard)
### Description
显示操作执行进度的 Widget（如 0%~100%）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (integer) | 取值从 Min（0%）到 Max（100%）。 |
| Min | EXPRESSION (any) | Data 可取的最小值。 |
| Max | EXPRESSION (any) | Data 可取的最大值。 |
| Orientation | Enum | `Horizontal` / `Vertical`。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W53. Progress (EEZ-GUI)
### Description
同 W52，EEZ-GUI 变体，显示执行进度。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (integer) | 0%~100% 对应的进度值。 |
| Min | EXPRESSION (any) | 最小值。 |
| Max | EXPRESSION (any) | 最大值。 |
| Orientation | Enum | `Horizontal` / `Vertical`。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events。

---

## W54. QRCode (Dashboard)
### Description
根据给定文本与纠错级别渲染二维码。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | EXPRESSION (any) | 生成二维码的文本。 |
| Error correction | Enum | 纠错级别：`Low`（~7%）/ `Medium`（~15%）/ `Quartile`（~25%）/ `High`（~30%）。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W55. QRCode (EEZ-GUI)
### Description
同 W54，EEZ-GUI 变体。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | EXPRESSION (any) | 生成二维码的文本。 |
| Error correction | Enum | `Low`/`Medium`/`Quartile`/`High`。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events。

---

## W56. QRCode (LVGL)【重要】
### Description
渲染二维码（LVGL 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | String | 生成二维码的文本。 |
| Dark color | ThemedColor | 渲染二维码图像的前景色（暗色模块）。 |
| Light color | ThemedColor | 渲染二维码图像的背景色（亮色模块）。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 LVGL 的二维码对象（`lv_qrcode_create` / `lv_qrcode_update`）。
- `Text` 必须为 **String**，作为二维码编码内容；LVGL 变体**不暴露** Error correction 级别（仅 Dashboard/EEZ-GUI 变体有，见 W54/W55）。
- `Dark color` / `Light color` 为 `ThemedColor`（主题色），在 json2eez 流水线中解析为 LVGL 的 `lv_color_t` 前景/背景；若依赖主题切换，需确认主题中这两色已定义。
- 二维码尺寸由 Width/Height 决定，建议保持正方形且宽度可被版本整除。

---

## W57. Radio
### Description
单选组（radio group）中的一个单选按钮：一组中同时只能选中一个。同组每个 Radio 使用不同的 `Value` 与相同的 `Group variable`。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Label | EXPRESSION (string) | 显示在单选按钮旁的标签文本。 |
| Group variable | ASSIGNABLE EXPRESSION (any) | 选中该 Radio 时，把 `Value` 存入此变量。 |
| Value | EXPRESSION (any) | 选中时存入 Group variable 的值；通过比较它与 Group variable 决定该 Radio 是否被选中。 |
| Enabled | EXPRESSION (any) | 为真则启用，否则禁用。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W58. Rectangle (Dashboard)
### Description
可渲染线条/矩形的 Widget（Dashboard 变体，用于绘制几何图形/分隔线）。
### Specific 属性
无额外特有属性（具体线条/填充在 Style（Default）中配置；原文仅列出 `Visible` 等通用项）。
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W59. Rectangle (EEZ-GUI)
### Description
同 W58，EEZ-GUI 变体。
### Specific 属性
无额外特有属性（样式在 Default 中配置）。
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events。

---

## W60. Roller (EEZ-GUI)
### Description
通过触摸滚动从列表中选择一个选项的 Widget（EEZ-GUI 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (integer) | 保存选中值在 `[Min, Max]` 范围内的变量。 |
| Min | EXPRESSION (any) | 可选最小值。 |
| Max | EXPRESSION (any) | 可选最大值。 |
| Text | EXPRESSION (any) | 每个可选值显示的文本。示例：设 `Data=selected_option`(integer)，`Min=0`，`Max=Array.length(TEXTS)-1`，`TEXTS` 为 `array:string` 默认 `["Option 1","Option 2","Option 3",...]`，则本属性填 `TEXTS[selected_option]`。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events、Flow。

---

## W61. Roller (LVGL)【重要】
### Description
通过触摸滚动从列表中选择一个选项的 Widget（LVGL 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Options | EXPRESSION (array:string) | 选项列表（字符串数组）。 |
| Options type | Enum | `Literal`（每行一个选项）或 `Expression`（求值得到 `array:string`）。 |
| Selected | EXPRESSION (integer) | 选中项的**零基**索引。 |
| Selected type | Enum | `Literal` 或 `Assignable`（Assignable 时 Selected 作为变量，存储选中项零基索引）。 |
| Mode | Enum | `NORMAL`（普通滚条）/ `INFINITE`（循环/圆形滚条）。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 `lv_roller`。`Options`（`array:string`）在 json2eez 中需用 `\n` 连接后调用 `lv_roller_set_options`。
- `Selected`（零基）映射 `lv_roller_set_selected`；`Selected type=Assignable` 时生成变量绑定，运行期可读取当前选项索引。
- `Mode=INFINITE` → `LV_ROLLER_MODE_INFINITE`（首尾相接循环）；`NORMAL` → `LV_ROLLER_MODE_NORMAL`。
- 关键 json2eez 属性：`Options`/`Options type`（决定选项来源）、`Selected`/`Selected type`（决定当前值与变量绑定）、`Mode`。

---

## W62. Scale
### Description
线性刻度盘：可带范围（range）与自定义样式的区间（sections）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Scale mode | Enum | 刻度位置与方向。 |
| Min value | EXPRESSION (integer) | 刻度范围最小值。 |
| Min value type | Enum | `Literal` 或 `Expression`。 |
| Max value | EXPRESSION (integer) | 刻度范围最大值。 |
| Max value type | Enum | `Literal` 或 `Expression`。 |
| Angle range | Number | 刻度角跨度（度），如 270 表示跨 270°。 |
| Rotation | EXPRESSION (integer) | 相对 0° 位置的偏移（度）。 |
| Rotation type | Enum | `Literal` 或 `Expression`。 |
| Total tick count | Number | 总刻度数。 |
| Major tick every | Number | 每 N 个刻度为一条主刻度。 |
| Post draw | Boolean | 启用后刻度在子对象之后绘制（如刻度含指针子对象且需画在指针之上时有用）。 |
| Draw ticks on top | Boolean | 刻度绘制在主线/主弧之上。 |
| Show labels | Boolean | 是否绘制标签。 |
| Label texts | MultilineText | 逗号分隔的自定义标签文本，替代自动生成的数字标签。 |
| Main styles | Any | 主线/主弧样式分区头。 |
| Main line width / color / opacity | Number / ThemedColor / Number | 直线模式（HORIZONTAL_TOP/BOTTOM、VERTICAL_LEFT/RIGHT）下主线宽/色/透明度(0-255)。 |
| Main arc width / color / opacity / rounded / image | Number / ThemedColor / Number / Boolean / ObjectReference | 圆弧模式（ROUND_INNER/OUTER）下主弧宽/色/透明度/是否圆角/位图源。 |
| Minor ticks styles | Any | 次刻度样式分区头。 |
| Minor ticks length / width / color / opacity | Number / Number / ThemedColor / Number | 次刻度长/宽/色/透明度。 |
| Major ticks styles | Any | 主刻度样式分区头。 |
| Major ticks length / width / color / opacity | Number / Number / ThemedColor / Number | 主刻度长/宽/色/透明度。 |
| Labels styles | Any | 标签样式分区头。 |
| Labels text color / opacity / font | ThemedColor / Number / Enum | 标签文字颜色/透明度/字体（内置或项目自定义字体）。 |
| Sections | Array | 刻度区间列表，每段定义范围与自定义样式（主线/弧、次/主刻度、标签均可独立样式；可通过 Use style 复用 Scale 样式）。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。

---

## W63. ScrollBar
### Description
配合 List / Grid Widget 在大列表中滚动。宽度>高度显示水平滚动条，否则垂直；水平条有左/右按钮，垂直条有上/下按钮。通过 `Data`（类型 `struct:$ScrollbarState`）与 List/Grid 联动。
### `struct:$ScrollbarState` 字段
- `numItems`：列表总项数。
- `itemsPerPage`：List/Grid 一页容纳项数。
- `positionIncrement`：点击左/上（后退）或右/下（前进）按钮时移动的步长。
- `position`：首个渲染项的位置，区间 `[0, numItems - itemsPerPage]`；List/Grid 渲染 `position` ~ `position + itemsPerPage`。
- 交互改变 position 的方式：左/上按钮减 increment；右/下按钮加 increment；拖动滑块设到区间任意值；点击滑块与按钮之间区域做整页进退（page up/down = ±itemsPerPage）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (struct:$ScrollbarState) | 绑定 `struct:$ScrollbarState` 类型变量。 |
| Left button text | String | 左/上按钮内文本（通常用图标字体单个字符）。 |
| Right button text | String | 右/下按钮内文本。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events、Flow。

---

## W64. Select
### Description
类似 Container，下面挂多个子 Widget，但只显示其中一个（由 `Data` 表达式结果决定）。用于根据变量值动态改变页面结构。子 Widget 通过 Widgets Structure 拖放加入，顺序由拖放决定。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (boolean) | 表达式结果必须是要显示的子 Widget 的**零基索引**（0 显示第一个，1 显示第二个……）。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events、Flow。

---

## W65. Slider (Dashboard)
### Description
通过移动滑块从列表中选择一个值的 Widget（Dashboard 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (double) | 保存选中值（在 `[Min, Max]` 内）的变量。 |
| Min | EXPRESSION (double) | 最小值。 |
| Max | EXPRESSION (double) | 最大值。 |
| Step | EXPRESSION (double) | 数值粒度（步长）。 |
| View min | EXPRESSION (double) | 显示的最小值。 |
| View max | EXPRESSION (double) | 显示的最大值。 |
| Enabled | EXPRESSION (any) | 为真则启用，否则禁用。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events、Flow。

---

## W66. Slider (EEZ-GUI)
### Description
同 W65，EEZ-GUI 变体。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (integer) | 保存选中值（在 `[Min, Max]` 内）的变量。 |
| Min | EXPRESSION (any) | 最小值。 |
| Max | EXPRESSION (any) | 最大值。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events、Flow。

---

## W67. Slider (LVGL)【重要】
### Description
通过移动滑块选择一个或两个值的 Widget（LVGL 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Min | EXPRESSION (integer) | 可选最小值。 |
| Min type | Enum | `Literal` 或 `Expression`。 |
| Max | EXPRESSION (integer) | 可选最大值。 |
| Max type | Enum | `Literal` 或 `Expression`。 |
| Mode | Enum | `NORMAL`（普通）/ `SYMMETRICAL`（从 0 画到当前值，需负最小值+正最大值）/ `RANGE`（同时设起值 Value left 与终值 Value）。 |
| Value left | EXPRESSION (integer) | RANGE 模式下的起始（左）值。 |
| Value left type | Enum | `Literal` 或 `Assignable`（变量存储起始值）。 |
| Preview value left | String | 可选；编辑器内滑块左值预览。 |
| Value | EXPRESSION (integer) | 选中值；RANGE 模式下为终（右）值。 |
| Value type | Enum | `Literal` 或 `Assignable`（变量存储选中值）。 |
| Preview value | String | 可选；编辑器内滑块值预览。 |
| Enable animation | Boolean | 启用则值变化带动画；动画时长由样式（LVGL 8.4 的 “Anim time” 或 9.1 的 “Anim duration”）控制。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 `lv_slider`。`Min`/`Max` → `lv_slider_set_range`；`Value` → `lv_slider_set_value`；`Value left`（RANGE）→ `lv_slider_set_left_value`。
- `Mode`：`NORMAL`→`LV_SLIDER_MODE_NORMAL`，`SYMMETRICAL`→`LV_SLIDER_MODE_SYMMETRICAL`（**必须** Min<0<Max），`RANGE`→`LV_SLIDER_MODE_RANGE`（同时用 Value left / Value）。
- `Value type`/`Value left type = Assignable` 时生成变量绑定，运行期可读取/写入滑块值。
- 关键 json2eez 属性：`Min`/`Max`/`Mode`/`Value`/`Value left`/`Enable animation`。

---

## W68. Span
### Description
**Work in progress**：可加入项目并生成创建代码，但更多功能需自定义代码（如 `ui_init()` 之后）。本质上是一个多文本 span 容器。
### Specific 属性
无特有属性（仅有通用 General / Position and size / Style / Flags / States / Events / Flow）。
### 适用通用分组
全部通用分组（LVGL 模式）。

---

## W69. Spinbox
### Description
**Work in progress**：数字微调框，生成创建代码，更多逻辑需自定义。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Digit count | Number | 位数（不含小数点与符号）。 |
| Separator position | Number | 小数点前的位数。 |
| Min | Number | 最小值。 |
| Max | Number | 最大值。 |
| Rollover | Boolean | 启用循环：到最小/最大后跳到另一端；禁用则停在极限值。 |
| Step | EXPRESSION (integer) | 设置光标所在位（如 1 指向最低位），仅可为 10 的倍数。 |
| Step type | Enum | `Literal` 或 `Assignable`（变量存储步长）。 |
| Value | EXPRESSION (integer) | 当前选中值。 |
| Value type | Enum | `Literal` 或 `Assignable`（变量存储值）。 |
### 适用通用分组
General、Position and size、Style（Use style / Default 视变体）、Flags、States、Events、Flow。

---

## W70. Spinner (Dashboard)
### Description
显示某个操作进行中/加载中的动画（Dashboard 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Visible | EXPRESSION (boolean) | 可见性（通常按加载状态切换显示/隐藏）。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W71. Spinner (LVGL)【重要】
### Description
显示某个操作进行中/加载中的动画（LVGL 变体）。
### Specific 属性
无额外特有属性（LVGL 变体仅含通用分组；旋转时间/弧长由样式决定）。
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 `lv_spinner`（`lv_spinner_create`）。动画由 LVGL 内部驱动，旋转周期/弧长通过样式（spin time、arc length）配置，无专有属性暴露。
- 开关状态不依赖 Checked；显示/隐藏用通用 Flags 的 `Hidden` 或 Position 的 `Visible` 控制。

---

## W72. Switch (Dashboard)
### Description
开关 Widget，用于开/关选项（Dashboard 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (any) | 布尔变量：开=true，关=false。 |
| Enabled | EXPRESSION (any) | 为真则启用，否则禁用。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W73. Switch (EEZ-GUI)
### Description
开关 Widget（EEZ-GUI 变体；文档中亦称为 Checkbox 风格的开关）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (boolean) | 布尔变量：开=true，关=false。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events。

---

## W74. Switch (LVGL)【重要】
### Description
开关 Widget，用于开/关选项（LVGL 变体）。
### Specific 属性
无额外特有属性（开/关状态通过通用 States 的 `Checked` 表达）。
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 `lv_switch`（`lv_switch_create`、`lv_switch_on/off`、`lv_switch_get_state`）。
- 开/关状态在 json2eez 中映射为 **Checked 状态**：`Checked`(EXPRESSION boolean) 为 true 即开；也可走 `lv_obj_add/remove_state(obj, LV_STATE_CHECKED)`。
- 没有独立的 `Value`/`Data` 属性（与 Dashboard/EEZ-GUI 变体不同），需通过绑定 Checked 状态或事件（如 VALUE_CHANGED）读写。

---

## W75. Tab
### Description
应作为 Tabview 的子 Widget 使用（详见 W78 Tabview）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Tab name | EXPRESSION (string) | 选项卡名称。 |
| Tab name type | Enum | 名称是否由表达式计算（Literal / Expression）。 |
### 适用通用分组
General、Position and size、Layout、Style、Flags、States、Events、Flow。

---

## W76. Table
### Description
**Work in progress**：表格 Widget，仅生成创建代码，更多逻辑需自定义。
### Specific 属性
无特有属性（仅有通用 General / Position and size / Style / Flags / States / Events / Flow）。
### 适用通用分组
全部通用分组（LVGL 模式）。

---

## W77. Tabulator
### Description
显示/编辑表格的 Widget，底层使用 Tabulator 库。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (json) | 表格数据（参见 Tabulator 的 Load Data From Array/JSON）。 |
| Basic options | Object | 基础表格选项（参见 Tabulator 文档）。 |
| Advanced options | EXPRESSION (json) | 覆盖基础选项的 JSON；因为是 Expression，可在运行期条件化修改。 |
| Persistent configuration | EXPRESSION (json) | 存储持久化配置的变量。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style、Events、Flow。

---

## W78. Tabview【重要】
### Description
Tab 视图对象，用选项卡组织内容。两种配置：
1. 直接在 Tabview 下放置 Tab Widget；
2. 在 Tabview 下加两个容器：第一个是 tab Bar，第二个是 tab Content；此时 Tab 放在 Content 容器内（用于分别样式化 Bar 与 Content）。
通过 Widgets Structure 面板拖放 Tab 到 Tabview。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Position | Enum | 选项卡栏位置（可置于任一侧：TOP/BOTTOM/LEFT/RIGHT）。 |
| Size | Number | 选项卡栏尺寸：垂直布局时为高度，水平布局时为宽度。 |
| Active tab | EXPRESSION (integer) | 当前激活选项卡的**零基**索引。 |
| Selected tab type | Enum | `Literal` 或 `Assignable`（Assignable 时 Active tab 作为变量，存储当前选中索引）。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 `lv_tabview`（`lv_tabview_create`、子对象为 `lv_tab`）。
- `Position` → `lv_tabview_set_tab_position`（TOP/BOTTOM/LEFT/RIGHT）；`Size` → `lv_tabview_set_tab_size`；`Active tab` → `lv_tabview_set_act`（零基）。
- `Selected tab type = Assignable` 时生成变量绑定，可读写当前激活页。
- **关键 json2eez 属性**：Tab 必须是 Tabview 的直接子对象（或置于 Content 容器）；`Active tab` 决定初始/运行期页；`Position` 决定栏方向。

---

## W79. Terminal
### Description
显示终端窗口：用户输入的任意文本逐字符通过 `onData` 输出；也可通过 Flow 的 Data 属性把文本送入终端。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (string) | 送入终端的文本。需添加 string 或 stream 类型的 Flow 输入并把其名填入本属性：string 类型每次收到字符串即写入终端（可多次）；stream 类型则监听流上新数据并写入（如把 ExecuteCommand 的 stdout/stderr 接到终端）。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style、Events、Flow。

---

## W80. Textarea【重要】
### Description
文本区域 Widget：含 Label 与光标，可添加文本/字符；长行自动换行，文本过长可滚动。支持**单行模式**与**密码模式**。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | EXPRESSION (string) | 要显示的文本。 |
| Text type | Enum | 选择文本是否由表达式计算。 |
| Placeholder | String | 文本区为空时显示的占位文本。 |
| One line mode | Boolean | 启用单行模式：高度自动仅显示一行、忽略换行、禁用自动换行。 |
| Password mode | Boolean | 启用密码模式：若字体含 •(U+2022) 则输入字符延时/新字符输入后转为 •；否则用 `*`。 |
| Accepted characters | String | 接受的字符列表，其它字符被忽略。 |
| Max text length | Number | 限制最大字符数。 |
### 适用通用分组
General、Position and size、Layout、Style（Use style）、Flags、States、Events、Flow。
### LVGL 对象映射 / json2eez 备注
- 映射到 `lv_textarea`（`lv_textarea_create`、`lv_textarea_set_text`、`lv_textarea_set_placeholder_text`）。
- `One line mode` → `LV_TEXTAREA_MODE_ONE_LINE`；`Password mode` → `lv_textarea_set_password_mode(true)`（bullet 字符 • 或 `*`）。
- `Accepted characters` → `lv_textarea_set_accepted_chars`；`Max text length` → `lv_textarea_set_max_length`。
- **键盘绑定**：LVGL 文本输入需配合 `lv_keyboard`，调用 `lv_keyboard_set_textarea(kb, ta)` 关联；json2eez 中通常需显式放置 Keyboard Widget 并绑定到本 Textarea（这是 LVGL 文本输入流水线的关键步骤）。

---

## W81. Text (Dashboard)
### Description
显示文本的 Widget（Dashboard 变体，多行文本，表达式驱动）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | EXPRESSION (any) | 要显示的文本（静态需加引号；含变量则编辑器显示表达式本身）。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
| Name（编辑期显示名，位于 General 组） | String | 当 Text 表达式无法编辑期计算时，设编辑器内显示文本（也显示在 Widgets Structure）。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events。

---

## W82. Text (EEZ-GUI)
### Description
显示单行文本的 Widget（EEZ-GUI 变体）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Text | EXPRESSION (any) | 要显示的文本（静态加引号；含变量则显示表达式）。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
| Hide "Widget is outside of its parent" warning | Boolean | 隐藏越界警告。 |
| Name（编辑期显示名） | String | 同 W81 的编辑期显示名。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events（含 Focused 样式）。

---

## W83. TextInput【重要】
### Description
用于输入文本的 Widget（Dashboard 风格的输入控件）。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (any) | 存储输入文本的变量。 |
| Read only | EXPRESSION (any) | 为真则只读（禁用用户输入）。 |
| Placehoder | EXPRESSION (any) | 未输入时显示的提示文本（**注：源文件原文拼写为 “Placehoder”**，实际即 Placeholder）。 |
| Password | Boolean | 输入密码时启用，输入时显示 `*` 替代字符。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing）、Layout、Style（Default）、Events（Event handlers）、Flow（Output widget handle / Inputs / Outputs / Catch error）。
### LVGL 对象映射 / json2eez 备注
- 该 Widget 属于 Dashboard 输入体系（非纯 LVGL），其键盘绑定由 Dashboard 的输入处理负责（聚焦时弹出/接管键盘）。
- `Value` 变量在输入过程中持续更新；`Read only` 用于展示型输入；`Password` 控制掩码。
- 在 json2eez 流水线中，它作为可绑定 `Value` 的输入控件存在；如需与 LVGL 键盘联动，应遵循 Dashboard 的键盘处理约定。

---

## W84. TileView【重要】
### Description
**Work in progress**：可加入项目并生成创建代码，但更多功能需自定义（如 `ui_init()` 之后）。LVGL tile view 用于平铺可滚动的“瓷砖”页面。
### Specific 属性
无特有属性（仅有通用 General / Position and size / Style / Flags / States / Events / Flow）。
### 适用通用分组
全部通用分组（LVGL 模式）。
### LVGL 对象映射 / json2eez 备注
- 在 LVGL 8 中映射到 `lv_tileview`（LVGL 9 已移除该部件，需自行以容器+滚动实现）。
- 滚动方向由通用 Flags 的 `Scroll direction` 决定：`HOR`/`VER`/`ALL`（瓷砖按方向排列，一次显示一个 tile）。
- tile 必须是 TileView 的直接子对象；json2eez 中通过 `Scroll direction` 确定布局方向，子对象即各 tile 页面。

---

## W85. ToggleButton
### Description
可在两种状态间切换的按钮：Default 与 Checked。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (boolean) | false=Default 状态，true=Checked 状态。 |
| Text1 | String | Default 状态下显示的文本。 |
| Text2 | String | Checked 状态下显示的文本。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events。

---

## W86. UpDown
### Description
通过递减/递增按钮选择单个值的 Widget。
### Specific 属性
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (integer) | 保存在 `[Min, Max]` 内选中值的变量。 |
| Down button text | String | 递减按钮内文本（通常用图标字体字符）。 |
| Up button text | String | 递增按钮内文本。 |
| Min | EXPRESSION (any) | 最小值。 |
| Max | EXPRESSION (any) | 最大值。 |
| Visible | EXPRESSION (boolean) | 可见性。 |
### 适用通用分组
Position and size（Resizing + Hide warning）、Layout、Style（Default）、Events、Flow。

---

## W87. Window
### Description
**Work in progress**：窗口 Widget，仅生成创建代码，更多逻辑需自定义。
### Specific 属性
无特有属性（仅有通用 General / Position and size / Style / Flags / States / Events / Flow）。
### 适用通用分组
全部通用分组（LVGL 模式）。

---

## 附录：变体对照速查

| Widget | Dashboard | EEZ-GUI | LVGL | 备注 |
|--------|:---------:|:-------:|:----:|------|
| QRCode | W54 | W55 | W56 | LVGL 无 Error correction；用 Dark/Light color |
| Roller | — | W60 | W61 | LVGL 用 Options/Selected/Mode |
| Slider | W65 | W66 | W67 | LVGL 含 Mode(RANGE/SYMMETRICAL) |
| Spinner | W70 | — | W71 | LVGL 无专有属性，靠样式驱动 |
| Switch | W72 | W73 | W74 | LVGL 用 Checked 状态表示开/关 |
| Text | W81 | W82 | — | 显示文本 |
| Progress | W52 | W53 | — | 进度条 |
| Rectangle | W58 | W59 | — | 几何绘制 |

**Work in progress 类（仅生成骨架）**：W45 Menu、W46 MessageBox、W68 Span、W76 Table、W84 TileView、W87 Window。
**JSON / 数据驱动类**：W51 Plotly（json）、W63 ScrollBar（struct:$ScrollbarState）、W77 Tabulator（json）。
**LVGL 重要变体（含对象映射说明）**：W56、W61、W67、W71、W74、W78、W80、W83、W84。
