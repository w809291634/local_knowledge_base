# EEZ Studio Actions 参考手册：A47 – A92

> 来源：`reference_guide_raw.txt`（EEZ Studio Reference Guide - Actions 章节，第 231–332 页）
> 范围：A47 MQTTEvent 至 A92 WriteSetting，共 46 个 Action。
> 约定：英文标识符（属性名、类型、枚举值、系统结构体名等）均按原文保留；说明文字为中文。

## 通用属性说明（所有 Action 共有）

本范围内绝大多数 Action 都带有以下三组“通用”属性。为避免逐条重复，集中说明如下，每个 Action 不再赘述，但均属于其属性集的一部分：

- **General / Description**（String）：组件描述，显示在 Project 编辑器/查看器中组件下方；主工具栏可一键显示/隐藏所有组件描述。
- **Flow / Inputs**（Array）：用户可自由添加的附加组件输入，用于在属性表达式中求值所需数据时接收额外数据。每个输入有 Name 和 Type；Name 在表达式中引用，Type 用于检查是否有对应类型的连线接入。
- **Flow / Outputs**（Array）：用户可添加的附加组件输出，用于发送数据。例如可在 Loop 组件中把该输出名填到 Variable 属性处，此时 Loop 不在每一步修改变量内容，而是通过该输出发送当前值。
- **Flow / Catch error**（Boolean）：勾选后组件新增一个 `@Error` 输出；若组件执行期间出错，Flow 从该输出继续，传递的数据为错误的文本描述。
- **Position and size / Align and distribute**（Any）：对齐与分布图标。选中 2 个及以上组件时出现对齐图标，选中 3 个及以上时出现分布图标。

> 若某 Action 的“Specific”（特有）属性为空，则其属性集仅由上述通用属性构成。

---

## A47. MQTTEvent

### Description
通过此 Action 可添加一个或多个连接（MQTT）的事件处理器（event handlers）。执行完此 Action 后，可以调用 `MQTTConnect` Action（注：本范围内为 `MQTTInit` 先初始化连接对象，再 `MQTTEvent` 绑定事件，最后连接）。用于处理来自 MQTT 连接的异步事件。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:MQTTConnection) | — | 要处理其事件的 MQTT 服务器连接对象。 |
| Event handlers | Array | — | 待处理事件列表。每个列表项需选择 Event、Handler type，可选 Action。Event 可选值见下；Handler type 可为 Flow 或 Action（选 Flow 则添加一个输出，事件触发时 Flow 从该输出继续；选 Action 则必须设置 Action，即事件触发时执行的 User action 名）。 |

**Event（事件类型）可选值：**
- `Connect` – 连接成功或重连成功时发出。
- `Reconnect` – 连接终止后尝试重连时发出。
- `Close` – 连接终止后发出。
- `Disconnect` – 收到 broker 的 disconnect 包时发出。
- `Offline` – 客户端离线时发出。
- `End` – 执行 `MQTTDisconnect` Action 时发出。
- `Error` – 客户端无法连接或解析出错时发出。
- `Message` – 客户端收到已订阅主题（用 `MQTTSubscribe` 订阅）的发布包时发出。通过输出发送 `struct:$MQTTMessage` 类型数据，其成员：`topic`（主题名）、`payload`（收到的消息内容）。

### Inputs
- `seqin` – SEQ | OPTIONAL：标准顺序输入。

### Outputs
- `seqout` – SEQ | OPTIONAL：标准顺序输出。

### Examples
- MQTT 示例项目。

### LVGL/嵌入式 UI 关联
- `Message` 事件携带的 `struct:$MQTTMessage`（含 `topic`/`payload`）是嵌入式仪表盘接收云端消息的核心通道；配合 OnEvent/A91 Watch 可实现 MQTT 数据驱动界面刷新。
- 事件驱动的 Handler type 选择 Flow 时，事件会“注入”一个新的 Flow 执行分支，适合在嵌入式端做异步响应（如收到指令后切换页面、更新变量）。

---

## A48. MQTTInit

### Description
创建并初始化一个 MQTT 连接对象，连接参数通过属性定义。此 Action 必须先执行，之后调用 `MQTTEvent` Action 绑定事件（再连接）。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | ASSIGNABLE EXPRESSION (object:MQTTConnection) | — | 将被创建并初始化的连接对象，类型 object:MQTTConnection。 |
| Protocol | EXPRESSION (string) | — | 连接所用协议，可选 `"mqtt"` 或安全连接 `"mqtts"`。 |
| Host | EXPRESSION (string) | — | 要连接的 MQTT 服务器名称。 |
| Port | EXPRESSION (integer) | 1883 | 连接使用的端口号，默认 1883。 |
| User name | EXPRESSION (string) | — | 连接授权用户名；不使用可留空。 |
| Password | EXPRESSION (string) | — | 连接授权密码；不使用可留空。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- MQTT 示例项目。

### LVGL/嵌入式 UI 关联
- 嵌入式设备（如 STM32 + EEZ-GUI）通过 `MQTTInit` 建立与 broker 的连接；`Protocol` 选 `mqtts` 时需注意设备端 TLS 资源占用。

---

## A49. MQTTPublish

### Description
向所选主题发布一条消息。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:MQTTConnection) | — | MQTT 服务器连接名。 |
| Topic | EXPRESSION (string) | — | 消息发布的主题。 |
| Payload | EXPRESSION (string) | — | 要发布的消息内容。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### LVGL/嵌入式 UI 关联
- 可用 `Payload` 携带从界面控件采集的数值（经 SetVariable / 表达式拼接）上报到云端。

---

## A50. MQTTSubscribe

### Description
必须在成功连接 MQTT 服务器后、针对每个要订阅的主题立即执行。若服务器对该主题发布了数据包，会通过 `MQTTEvent` 的 `Message` 事件收到通知。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:MQTTConnection) | — | MQTT 服务器连接名。 |
| Topic | EXPRESSION (string) | — | 要订阅的主题名。可订阅具体主题，或使用通配符。 |

**通配符规则：**
- `+`：单层层级通配符。例如 `sensors/+/temperature/+`。
- `#`：剩余所有层级的通配符，必须是订阅字符串的最后一个字符。例如对主题 `a/b/c/d`，`a/#`、`a/b/#`、`a/b/c/#`、`+/b/c/#`、`#` 均匹配，而 `a/b/c`、`b/+/c/d`、`+/+/+` 不匹配。

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- MQTT 示例项目。

---

## A51. MQTTUnsubscribe

### Description
取消订阅某个主题。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:MQTTConnection) | — | MQTT 服务器连接名。 |
| Topic | EXPRESSION (string) | — | 要取消订阅的主题。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- MQTT 示例项目。

---

## A52. NoOp

### Description
此 Action 什么也不做，即 Flow 执行直接通过 `seqout` 继续。常用于占位、留待后续填充，或仅用于显示名称。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Name | String | — | 在 Flow 内组件视图中显示的名称。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

---

## A53. OnEvent（重要：事件驱动 UI）

### Description
用于处理**当前所在页面（page）内广播的事件**。当页面或键盘触发事件时，绑定在该页面 Flow 中的 `OnEvent` Action 会被触发，Flow 从 `seqout` 继续。这是 EEZ-GUI 嵌入式 UI 中实现“事件驱动界面”的核心机制。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Event | Enum | — | 要处理的事件。可用页面事件见下。 |

**可用页面事件：**
- `Page open` – 页面变为活动页时发出，例如用 `ShowPage` Action 显示该页时。
- `Page close` – 页面变为非活动页（被隐藏）时发出。
- `Keydown` – 键盘上有按键被按下时发出。会向事件输出发送一个**键盘名称字符串**（文档以 link 标注；输出即下方 `seqout`）。

### Inputs
- 无额外输入（仅通用 `seqin`，但此 Action 实际通过页面事件触发；其属性集中未单列独立数据输入）。

### Outputs
- `seqout` – SEQ | **MANDATORY**：当所选事件发出时，Flow 从此输出继续。

### Examples
- 键盘/Keypad/MessageBox 示例项目常用于演示 `Keydown`。

### LVGL/嵌入式 UI 关联（重点）
- **页面生命周期绑定**：把 `OnEvent` 放在某个 page 的 Flow 里，选 `Page open` 可在页面显示时做初始化（如读取设置、刷新数据）；选 `Page close` 可做离开页面时的清理/保存。
- **键盘事件**：`Keydown` 让嵌入式设备（无物理键盘时）能捕获屏幕软键盘或外部按键事件，从而驱动界面逻辑（例如按 Enter 确认、按方向键切换焦点）。
- **事件广播范围**：仅限 Action 所在的 page 内部广播，因此事件处理需与该页面绑定；跨页面通信应改用全局变量 + `Watch` 或消息机制。
- 注意文档原文同时提到 `Keydown` “A string with keyboard name is sent to the event output”，而输出表中只列了 `seqout`（MANDATORY）。实际项目中键盘名一般通过捕获按键的控件/表达式取得，OnEvent 本身提供的是“事件触发 → 继续 Flow”的钩子。

---

## A54. Output

### Description
向 User action 或 User widget 添加一个数据输出。用于在自定义 action/widget 中向调用方返回数据。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Name | String | — | 输出名称。 |
| Type | String | — | 输出数据类型。 |

### Inputs
- `seqin` – SEQ | **MANDATORY**：从此输入接收数据，随后转发给 User action 的调用方。

### Outputs
- （无独立数据输出属性；数据通过组件自身的命名输出对外提供，由 `Name`/`Type` 定义。）

### LVGL/嵌入式 UI 关联
- 在自定义 widget 中，`Output` 是向外部 Flow 暴露状态的标准方式（例如自定义仪表控件把当前读数作为输出）。

---

## A55. OverrideStyle（重要：控件运行时样式覆盖）

### Description
该 Action 会**用一个样式替换另一个样式**，使得所有使用该样式的 Widget 在替换后都使用新样式。适用于想在运行时动态改变某个 Widget 外观的场景。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| From | ObjectReference | — | 将被替换掉的样式（style 对象引用）。 |
| To | ObjectReference | — | 用来替换现有样式的新样式（style 对象引用）。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### LVGL/嵌入式 UI 关联（重点）
- **作用对象是“样式”而非“单控件”**：`OverrideStyle` 通过 `From`/`To` 两个 `ObjectReference` 指向项目中的 Style 对象，执行后所有引用 `From` 样式的控件都会改用 `To` 样式。这是批量换肤/主题切换的底层机制。
- **如何定位 Widget**：若要只改某个具体控件的样式，思路是让该控件单独引用一个专用样式，再用 `OverrideStyle` 替换这个专用样式；或直接通过控件的样式属性引用。EEZ 的 Style 在 LVGL 概念中对应 `lv_style_t`，替换即改变控件所绑定的 style 指针。
- **可覆盖的样式属性**：由于是整体样式替换，所有 style 成员（背景色/渐变、边框宽度/颜色/圆角、文本字体/颜色/对齐、padding、尺寸、阴影、线型等 LVGL style 属性）一并切换，而非单独某一属性。若需“单属性微调”，本 Action 不直接支持，应改用 A73 `SetVariable` 配合控件专属属性表达式，或定义多套 Style 互相替换。
- **典型用途**：暗/亮主题切换、告警状态高亮、不同语言/布局下的样式适配。

---

## A56. PlayAudio

### Description
播放音频文件。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Audio file | EXPRESSION (string) | — | 音频文件路径。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

---

## A57. PrintToPDF

### Description
打印 Widget 内容到 PDF。当前**仅支持 Tabulator widget** 的打印。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Widget | EXPRESSION (widget) | — | 指向 Tabulator widget 的引用。参见各 widget 的 “Output widget handle” 属性了解如何获取该引用。 |
| Options | EXPRESSION (json) | — | 通过 JSON 指定打印选项，字段如下。 |

**Options（JSON）字段：**
- `landscape` (boolean, 可选) – 纸张方向；true 横向，false 纵向，默认 false。
- `scale` (number, 可选) – 网页渲染缩放比例，默认 1。
- `pageSize` (string | Size, 可选) – 生成 PDF 的页面尺寸，可为 `A0`/`A1`/`A2`/`A3`/`A4`/`A5`/`A6`/`Legal`/`Letter`/`Tabloid`/`Ledger`，或含英寸宽高的 Object，默认 `Letter`。
- `margins` (Object, 可选)：
  - `marginType` (string, 可选) – `"default"` 或 `"custom"`。
  - `top`/`bottom`/`left`/`right` (number, 可选) – 上下左右页边距（英寸），默认约 1cm（≈0.4 英寸）。

**示例 JSON：**
```json
{
  "landscape": true,
  "scale": 1,
  "pageSize": "A4",
  "margins": {
    "marginType": "custom",
    "top": 0.8, "bottom": 0.8, "left": 0.8, "right": 0.8
  }
}
```

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- Tabulator Examples。

---

## A58. PythonEnd

### Description
停止一个正在运行的 Python 脚本。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Handle | EXPRESSION (integer) | — | 执行 `PythonRun` 时获取的句柄，用于确定要停止哪个脚本（因可能同时运行多个脚本）。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。
- `handle` – DATA(integer) | **MANDATORY**：也可通过此输入传入句柄。若句柄已通过 `Handle` 属性从变量获取，可在 “Flow - Inputs” 中移除该输入。

### Outputs
- `seqout` – SEQ | OPTIONAL。

---

## A59. PythonRun

### Description
运行一个 Python 脚本，并把运行脚本的句柄发送到 `handle` 输出。该句柄供 `PythonEnd`（停止脚本）或 `PythonSendMessage`（从 Flow 向脚本发消息）使用——因为同一时刻可能启动多个脚本，必须用句柄区分。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Script source option | Enum | — | 脚本来源，三选一：`Inline script` / `Inline script as expression` / `Script file`。 |
| Inline script | Python | — | 选 `Inline script` 时在此填写脚本源码。 |
| Inline script as expression | EXPRESSION (string) | — | 选 `Inline script as expression` 时，填写求值为脚本源码字符串的表达式。 |
| Script file | EXPRESSION (string) | — | 选 `Script file` 时填写 `.py` 文件路径。 |
| Python path | EXPRESSION (string) | — | python 命令的完整路径。若已在系统 PATH 中可设为空字符串 `""`。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `handle` – DATA(integer) | OPTIONAL：运行脚本的句柄，供 `PythonEnd`/`PythonSendMessage` 使用。
- `message` – DATA(string) | OPTIONAL：脚本内打印到 stdout 的所有内容都经此输出发送，即脚本向 Flow 发消息；反之 Flow→脚本用 `PythonSendMessage`。

### Examples
- Charts 示例。

---

## A60. PythonSendMessage

### Description
从 Flow 向一个正在运行的 Python 脚本发送消息。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Handle | EXPRESSION (integer) | — | `PythonRun` 获取的句柄，确定发往哪个脚本（可同时运行多个）。 |
| Message | EXPRESSION (string) | — | 要发送的消息。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。
- `handle` – DATA(integer) | **MANDATORY**：也可经此输入传句柄；若已用 `Handle` 属性从变量获取，可在 “Flow - Inputs” 移除。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- Charts 示例。

---

## A61. ReadSetting（重要：持久化设置）

### Description
对给定的 Key 名，从 `.eez-project-runtime-settings` 文件返回已保存的值；若该 Key 不存在则返回 `null`。该文件与**持久变量（persistent variables）**所在的文件相同。

> 注意：WriteSetting 与 ReadSetting 用于把“希望 Dashboard 项目重启后仍然保留”的设置存入/读出该文件。使用**持久变量**更方便，因为无需专门执行存/取 Action。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Key | EXPRESSION (string) | — | 要取值的键名字符串。 |

### Inputs
- `seqin` – SEQ | **MANDATORY**。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `value` – DATA(any) | **MANDATORY**：所取 Key 的值经此输出发送。

### LVGL/嵌入式 UI 关联（重点）
- 持久化用户偏好（如语言选择、主题、校准值、网络配置）使其跨重启保留，是嵌入式仪表盘“设置不丢失”的标准做法。
- 与 A73 `SetVariable` 区别：`SetVariable` 仅改内存变量（重启即失）；`ReadSetting`/`WriteSetting` 落盘到 runtime-settings 文件。
- 推荐：能用持久变量则用持久变量；仅在需要自定义 Key/Value 管理时才用这对 Action。

---

## A62. Regexp

### Description
使用按正则表达式语法编写的模式，在给定字符串或流（stream）中搜索。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Pattern | EXPRESSION (string) | — | 用于搜索的正则表达式。 |
| Text | EXPRESSION (string) | — | 待搜索文本，可为字符串或流。 |
| Global | EXPRESSION (boolean) | — | 是否搜索模式的所有出现（true）还是仅第一个（false）。 |
| Case insensitive | EXPRESSION (boolean) | — | 搜索是否忽略大小写。 |

### Inputs
- `seqin` – SEQ | OPTIONAL：开始时使用一次。
- `next` – SEQ | OPTIONAL：用此输入获取下一个匹配。
- `stop` – SEQ | OPTIONAL：停止进一步搜索，随后 Flow 立即经 `done` 输出继续。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `match` – DATA(struct:$RegExpResult) | **MANDATORY**：搜索匹配结果，类型为 `struct:$RegexpMatch`，字段：
  - `index` (integer) – 匹配在字符串中的从 0 开始的索引。
  - `texts` (array:string) – 数组，第 1 项为匹配文本，其后每项对应一个捕获组（capturing group）。
  - `indices` (array:array:integer) – 每项表示子串匹配的范围；数组下标与 `texts` 对应（第 1 个为整体匹配，第 2 个为第 1 捕获组，依此类推）。每项本身为两元素数组 `[start, end]`。
- `done` – DATA(string) | OPTIONAL：搜索完成（无更多匹配）时 Flow 经此继续。

### Examples
- RegExp String、RegExp Stream。

---

## A63. SCPI

### Description
在所选仪器上执行一条或多条 SCPI 命令/查询。所有命令/查询执行完后，Flow 经 `seqout` 继续。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Instrument | EXPRESSION (object:Instrument) | — | 执行命令/查询的仪器对象。**仅**在 Dashboard 项目中、仪器被远程连接时存在（可同时开多个连接）。EEZ-GUI 项目中此属性不存在，因为总是用执行 Flow 的设备本身。 |
| Scpi | TEMPLATE LITERAL | — | SCPI 命令/查询列表，每条命令/查询单独一行。可在命令/查询内插入 Flow 表达式（置于两花括号之间）。 |
| Timeout (ms) | EXPRESSION (integer) | — | 等待查询结果的毫秒数；超时产生 Timeout 错误，可在 `Catch error` 开启时经 `@Error` 处理。设为 `null` 则用 Instrument Connect 对话框中的超时。 |
| Delay (ms) | EXPRESSION (integer) | — | 发送新命令/查询前必须等待的最小毫秒数；设为 `null` 则用 Instrument Connect 对话框中的延迟。 |

**查询结果去向（两种）：**
- **发到 Flow 输出**：在 “Flow - Outputs” 中新增输出，写为 `output_name=query?`。
- **存到变量**：写为 `variable_name=query?` 或 `{assignable_expression}=query?`（后者用于存入结构成员/数组）。例如：
  - `fw_ver=SYSTem:CPU:FIRMware?` → 结果存变量 `fw_ver`。
  - `slots[{ch_idx}].u_min=...?` 等形式存入 `array:struct:Slot`。

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- BB3 Dashboard、Plotly、Rigol Waveform Data、Screen Capture。

---

## A64. SelectInstrument

### Description
打开选择仪器的对话框，所选仪器经 `instrument` 输出发送。若全局仪器对象变量设为 **Persistent**，则 Dashboard 启动时自动打开选择对话框，无需此 Action；若不希望启动时自动弹窗，则不要把全局仪器变量的 Persistent 勾上，可后续用此 Action 选择。

### Properties（Specific）
- 无特有属性（仅通用属性）。

### Inputs
- `seqin` – SEQ | **MANDATORY**。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `instrument` – DATA(object:Instrument) | **MANDATORY**：所选仪器经此输出。

---

## A65. SelectLanguage

### Description
在多语言项目（即添加了 Texts 特性的项目）中切换活动语言，切换后页面上所有文本以新语言显示。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Language | EXPRESSION (any) | — | 将成为新活动语言的 ID。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- Multi-Language、Multi-Language Dashboard。

### LVGL/嵌入式 UI 关联
- 嵌入式多语种设备通过此 Action 切换界面语言，配合 Texts 特性实现所有文本热更新。

---

## A66. SerialConnect

### Description
连接串口。连接成功则 Flow 经 `seqout` 继续；出错且开启 `Catch error` 时可捕获。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:SerialConnection) | — | 用于串口通信的连接名。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- SerialPort。

---

## A67. SerialDisconnect

### Description
断开串口连接，之后 Flow 经 `seqout` 继续。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:SerialConnection) | — | 要终止的连接名。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- SerialPort。

---

## A68. SerialInit

### Description
创建并初始化一个 Serial 连接对象，参数经属性定义。此 Action 必须先执行，之后调用 `SerialConnect`。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | ASSIGNABLE EXPRESSION (object:SerialConnection) | — | 将创建并初始化的连接对象。 |
| Port | EXPRESSION (object:string) | — | 串口名。 |
| Baud rate | EXPRESSION (object:number) | — | 串口波特率。 |
| Data bits | EXPRESSION (object:number) | — | 数据位，允许 5/6/7/8。 |
| Stop bits | EXPRESSION (object:number) | — | 停止位，允许 1 或 2。 |
| Parity | EXPRESSION (object:string) | — | 校验位，允许 `"none"`/`"even"`/`"mark"`/`"odd"`/`"space"`。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

---

## A69. SerialListPorts

### Description
获取系统检测到的串口列表，并经 `ports` 输出发送。

### Properties（Specific）
- 无特有属性（仅通用属性）。

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `ports` – DATA(array:struct:$SerialPort) | **MANDATORY**：端口列表，类型 `array:$SerialPort`。系统结构 `$SerialPort` 成员：
  - `manufacturer` (string) – 连接设备制造商名。
  - `serialNumber` (string) – 端口序列号。
  - `path` (string) – 串口路径，用于 `SerialInit` 的 Port 属性。

---

## A70. SerialRead

### Description
把经所选串口连接收到的读取流（read stream）发送到 `data` 输出。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:SerialConnection) | — | 串口连接名。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `data` – DATA(stream) | **MANDATORY**：读取的流发送到的输出。

### Examples
- SerialPort。

---

## A71. SerialWrite

### Description
向串口发送一个字符串。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Connection | EXPRESSION (object:SerialConnection) | — | 串口连接名。 |
| Data | EXPRESSION (string) | — | 发送到串口字符串。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- SerialPort。

---

## A72. SetPageDirection（UI 导航）

### Description
用于把页面布局从 LTR（左到右）切换为 RTL（右到左），或反之。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Direction | Enum | — | 所选页面布局：`LTR` 或 `RTL`。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### LVGL/嵌入式 UI 关联（重点）
- 面向 RTL 语言（阿拉伯语、希伯来语等）的嵌入式界面，用此 Action 整体翻转页面布局方向，使控件排列、文本对齐符合 RTL 习惯。
- 与 A65 `SelectLanguage` 常配合使用：切换至 RTL 语言时一并调用 `SetPageDirection(RTL)`。

---

## A73. SetVariable（重要：变量赋值）

### Description
用于为一个或多个变量设置新值。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Set variable entries | Array | — | 待设置变量列表。列表每个元素包含：给定变量名，新值由对其求值表达式得到。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### LVGL/嵌入式 UI 关联（重点）
- 这是界面状态管理最核心的 Action：控件绑定变量后，用 `SetVariable` 改变量即可驱动 UI 刷新（例如进度条、标签文本、开关状态）。
- 支持**一次设置多个变量**（列表项）；每项 = 变量名 + 表达式，表达式可引用其他变量、输入、函数。
- 与 A91 `Watch` 配合：修改变量后，`Watch` 侦测到变化并推送给界面。
- 注意：普通变量重启即失；需要持久则改用 A61/A92 或持久变量。

---

## A74. ShowFileInFolder

### Description
在系统文件管理器中显示指定文件，尽可能同时选中该文件。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| File path | EXPRESSION (string) | — | 要在文件管理器中显示的文件路径。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- Screen Capture。

---

## A75. ShowKeyboard（重要：嵌入式屏上软键盘）

### Description
打开用于文本输入的键盘页面。键盘页面必须存在于项目中，且其 **ID 必须为 2**。键盘页面也可通过 Input Widget 打开。参见 “Keyboard, Keypad and Message Box” 示例了解键盘页面定义方式。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Label | EXPRESSION (string) | — | 键盘页面上显示的标签（如正在输入值的参数名）。 |
| Inital text | EXPRESSION (string) | — | 输入框中显示的初始（默认）文本。 |
| Min chars | EXPRESSION (integer) | — | 输入文本的最小长度。 |
| Max chars | EXPRESSION (integer) | — | 输入文本的最大长度。 |
| Password | Boolean | — | 隐藏输入文本（如用户密码）。启用后每个字符显示为 `*`。 |

### Inputs
- `seqin` – SEQ | **MANDATORY**。

### Outputs
- `result` – DATA(string) | **MANDATORY**：输入文本发送到的输出。
- `canceled` – DATA(null) | OPTIONAL：按取消按钮时 Flow 经此继续。

### Examples
- Keyboard, Keypad and Message Box；stm32f469i-disco-eez-flow-demo。

### LVGL/嵌入式 UI 关联（重点）
- 在无物理键盘的嵌入式触摸屏上，这是文本录入的标准入口；页面 ID=2 是 EEZ 运行时的硬性约定。
- 与 Input Widget 二选一：Input Widget 也能唤起键盘，但 `ShowKeyboard` 可在任意 Flow 节点主动弹出并取回 `result`。
- `Password` 模式适合密码/密钥录入；`Min/Max chars` 做输入约束。

---

## A76. ShowKeypad（重要：嵌入式屏上数字键盘）

### Description
打开用于数值输入的数字键盘（keypad）页面。数字键盘页面必须存在于项目中，且其 **ID 必须为 3**。也可通过 Input Widget 打开。参见 “Keyboard, Keypad and Message Box” 示例了解定义方式。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Label | EXPRESSION (string) | — | 键盘页面上显示的标签（如参数名）。 |
| Inital value | EXPRESSION (float) | — | 输入框中显示的初始（默认）数值。 |
| Min | EXPRESSION (integer) | — | 输入数值必须 ≥ 此值。 |
| Max | EXPRESSION (integer) | — | 输入数值必须 ≤ 此值。 |
| Precision | EXPRESSION (float) | — | 输入数值的舍入精度，例如最多两位小数则填 `0.01`。 |
| Unit | EXPRESSION (string) | — | 输入时显示的单位。 |

### Inputs
- `seqin` – SEQ | **MANDATORY**。

### Outputs
- `result` – DATA(float) | **MANDATORY**：输入数值发送到的输出。
- `canceled` – DATA(null) | OPTIONAL：按取消按钮时 Flow 经此继续。

### Examples
- stm32f469i-disco-eez-flow-demo；Keyboard, Keypad and Message Box。

### LVGL/嵌入式 UI 关联（重点）
- 嵌入式设备上参数（温度、电压、阈值等）数值录入的标准入口；页面 ID=3 为运行时约定。
- `Min/Max/Precision/Unit` 组合提供输入校验与展示，远高于裸 `ShowKeyboard` 的数值体验。
- 取回的 `result` (float) 通常经 A73 `SetVariable` 写入绑定控件，即时刷新界面。

---

## A77. ShowMessageBox

### Description
用于显示 Info、Error 或 Question 类型的消息框。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Message type | Enum | — | 消息框类型：`Info` / `Error` / `Question`。 |
| Message | EXPRESSION (string) | — | 要显示的消息内容。 |
| Buttons | EXPRESSION (array:string) | — | 仅 Question 类型需定义。期望字符串数组，每个字符串映射到一个按钮，如 `["Save", "Don't Save", "Cancel"]`。需在 “Flow - Outputs” 中为每个按钮添加一个输出，按下该按钮时 Flow 经对应输出继续。 |

### Inputs
- `seqin` – SEQ | **MANDATORY**。

### Outputs
- `seqout` – SEQ | OPTIONAL（Info/Error 类型用；Question 类型则按按钮经各自输出继续）。

### Examples
- Keyboard, Keypad and Message Box。

### LVGL/嵌入式 UI 关联
- 嵌入式人机交互的确认/告警弹窗；Question 的多按钮需按按钮名在 Outputs 中添加对应输出分支。

---

## A78. ShowPage（重要：页面导航）

### Description
设置一个新的活动页面：前一个页面被隐藏，新页面被显示。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Page | ObjectReference | — | 要显示的新页面名（页面对象引用）。 |

### Inputs
- `seqin` – SEQ | **MANDATORY**。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### LVGL/嵌入式 UI 关联（重点）
- 这是**页面切换/导航的主入口**：菜单跳转、子页面进入、登录后跳转主页等都靠它。
- 与 A53 `OnEvent` 配合：目标页面的 `Page open`/`Page close` 事件会触发，可在页面进入时做初始化、离开时做保存。
- 被隐藏页面不会被销毁，状态通常保留（取决于变量作用域），再次 `ShowPage` 回来可保持上下文。

---

## A79. SortArray

### Description
对数组变量排序，并经 `result` 输出返回结果：**不做原地排序**（不修改原数组变量内容）。允许类型：`array:integer`、`array:float`、`array:double`、`array:struct`。若排序 `array:struct`，还需指定结构名与排序字段名。另有升/降序、字符串排序是否忽略大小写两个选项。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Array | EXPRESSION (array:any) | — | 待排序的数组变量。 |
| Structure name | ObjectReference | — | 当数组为 `array:struct` 时，选择结构名。 |
| Structure field name | Enum | — | 当数组为 `array:struct` 时，选择按哪个字段排序。 |
| Ascending | Boolean | — | 排序模式（启用=升序，否则降序）。 |
| Ignore case | Boolean | — | 字符串排序时是否忽略大小写。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `result` – DATA(any) | **MANDATORY**：排序后的数组经此输出。

---

## A80. Start（重要：Flow 入口）

### Description
Flow 启动时**第一个执行**的 Action。把此 Action 的输出连接到你想要首先执行的下一个 Action。

### Properties（Specific）
- 无特有属性（仅通用属性）。

### Inputs
- （无输入；这是 Flow 的起点。）

### Outputs
- `seqout` – SEQ | **MANDATORY**：连接到 Flow 启动后要首先执行的 Action。

### LVGL/嵌入式 UI 关联（重点）
- 每个 Flow 的唯一入口；嵌入式设备开机/页面加载时从 `Start` 顺流执行初始化（连接外设、读取设置、显示首页等）。
- 与 A78 `ShowPage` 常结合：Start → 读取持久设置 → ShowPage(首页)。

---

## A81. SwitchCase

### Description
`Cases` 列表中的表达式从第一个开始逐个求值。第一个求值结果为 true 的表达式，其 `Then` 输出被用作 Flow 继续执行的出口；除非定义了 `With value` 表达式，否则向该输出传递值 `true`。若所有 case 都不为 true，可在列表末尾加一个 `When` 填 `true` 的 case，使其永远求值 true 并从该输出退出，防止 Flow 停滞。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Cases | Array | — | 每个列表元素包含：`When`（求值为真的表达式）、`Then output`（求值 true 时 Flow 继续的输出名）、`With value`（可选，设为表达式则把该值传到输出，否则传 `true`）。 |

### Inputs
- （通用 `seqin` 等；本 Action 无额外数据输入。）

### Outputs
- 由 `Cases` 中定义的 `Then output` 名称决定（每个 case 一个命名输出）；外加通用 `seqout`（可选）。

---

## A82. TabulatorAction

### Description
在给定 Tabulator widget 上执行一个动作。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Widget | EXPRESSION (widget) | — | 指向 Tabulator widget 的引用（见各 widget 的 “Output widget handle” 属性了解获取方式）。 |
| Tabulator action | Enum | — | 要执行的动作：`Get sheet data` 或 `Download`。 |
| Lookup | EXPRESSION (string) | — | 若动作为 `Get sheet data`，此为此处要获取的 sheet 名；为空则获取当前活动 sheet。 |
| File name | EXPRESSION (string) | — | 若动作为 `Download`，此为默认下载文件名。 |
| Download type | Enum | — | 若动作为 `Download`，下载文件类型：`CSV` / `JSON` / `HTML`。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- Tabulator Examples。

---

## A83. TCPConnect

### Description
连接到 TCP 服务器。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Socket | ASSIGNABLE EXPRESSION (object:TCPSocket) | — | 将创建并初始化的 socket 对象，类型 object:TCPSocket。 |
| IP Address | EXPRESSION (object:string) | — | 服务器 IP 地址。 |
| Port | EXPRESSION (object:number) | — | 服务器接受连接的 TCP 端口。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL（注：源文 outputs 区段在 TCPConnect 处未展开列出，按通用规则应有可选 `seqout`）。

---

## A84. TCPDisconnect

### Description
断开与 TCP 服务器的连接，之后 Flow 经 `seqout` 继续。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Socket | EXPRESSION (object:TCPSocket) | — | 要断开的 socket 对象。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- TCP CLient、TCP Server。

---

## A85. TCPEvent

### Description
通过此 Action 可添加一个或多个 TCP socket 能接收的事件处理器。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Socket | EXPRESSION (object:TCPSocket) | — | 要监听事件的 socket 对象。 |
| Event handlers | Array | — | 待处理事件列表。每项需选 Event、Handler type，可选 Action。Handler type 可为 Flow（事件触发时 Flow 经添加的输出继续）或 Action（设 Action 名，事件触发时执行该 User action）。 |

**Event 可选值：**
- `Ready` – socket 就绪可使用。
- `Data` – 收到数据时。
- `Close` – socket 完全关闭后。
- `End` – 对端信号传输结束、可读侧关闭。
- `Error` – 出错时（随后直接调用 `close`）。
- `Timeout` – socket 因空闲超时时（仅通知空闲，需手动断开）。

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- TCP CLient、TCP Server。

---

## A86. TCPListen

### Description
绑定 TCP 端口并监听 incoming 连接。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Port | EXPRESSION (object:number) | — | 绑定的端口。 |
| IP Address | EXPRESSION (object:string) | — | 绑定的地址。 |
| Max. Connections | EXPRESSION (object:number) | — | 允许的最大活动接入连接数。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。
- `end` – SEQ | OPTIONAL：停止监听并解除端口绑定，将触发 `close` 输出。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `connection` – DATA(object:TCPSocket) | **MANDATORY**：接入连接的 socket 经此输出发送。

---

## A87. TCPWrite

### Description
向 TCP socket 写入数据。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Socket | EXPRESSION (object:TCPSocket) | — | 写入数据的 socket。 |
| Data | EXPRESSION (object:string) | — | 要写入的数据。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- TCP CLient、TCP Server。

---

## A88. TestAndSet

### Description
测试一个布尔变量：若为 false 则置为 true 并经 `seqout` 继续；若为 true 则把它重新放回 Flow 执行队列（即此 Action 等待直到该变量变为 false）。此测试与置位作为**单一原子（不可中断）操作**完成，因此适用于“确保某个 Flow 片段在某一时刻只执行一次”的场景——在进入该片段前用此 Action，在片段退出时用 `SetVariable` 把变量重新置 false。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Variable | ASSIGNABLE EXPRESSION (boolean) | — | 要测试并置位的变量。 |

### Inputs
- `seqin` – SEQ | OPTIONAL：标准顺序输入。

### Outputs
- `seqout` – SEQ | OPTIONAL：变量变为 false 时 Flow 经此继续。

### Examples
- Tetris：在 `do_action` User action（检测到键盘按键按下时调用）开头用 `TestAndSet` 作用于 `busy` 变量，退出前把 `busy` 置 false，从而保证两个 Action 不会同时执行。

### LVGL/嵌入式 UI 关联
- 嵌入式端防止并发重入（如快速连按按键导致多次触发）的轻量锁机制。

---

## A89. UDP In

### Description
用此 Action 输出在指定 UDP 端口收到的消息。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Listen for | Enum | — | 选 UDP 或 Multicast 模式。 |
| Group | EXPRESSION (string) | — | 选 Multicast 模式时，指定要加入的多播组。 |
| Local interface | EXPRESSION (string) | — | 多播组的本地网络接口；不指定则由操作系统自选并加入。 |
| On port | EXPRESSION (integer) | — | 要接收消息的端口。 |
| Using | Enum | — | 使用 IPV4 或 IPV6 地址。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `message` – DATA(struct:$UDPMessage) | **MANDATORY**：收到的消息，类型 `struct:$UDPMessage`，字段：
  - `payload`：收到的消息负载（blob），用 `Blob.toString()` 转为字符串。
  - `address`：远端 IP 地址。
  - `port`：远端 IP 端口。

### Examples
- UDP CLient、UDP Server。

---

## A90. UDP Out

### Description
向指定的 UDP 主机和端口发送消息。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Send a | Enum | — | 发送 UDP / Multicast / Broadcast 消息。 |
| To port | EXPRESSION (integer) | — | 消息发送到的端口。 |
| Address | EXPRESSION (string) | — | 消息发送到的地址。 |
| Group | EXPRESSION (string) | — | 选 Multicast 模式时指定多播组。 |
| Local interface | EXPRESSION (string) | — | 多播组本地网络接口；不指定则系统自选。 |
| Ipv | Enum | — | 使用 IPV4 或 IPV6 地址。 |
| Bind to | Enum | — | 绑定随机或固定端口。 |
| Outport | EXPRESSION (integer) | — | 选固定端口时，用此指定固定端口。 |
| Payload | EXPRESSION (string) | — | 要发送的消息负载。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### Examples
- UDP CLient、UDP Server。

---

## A91. Watch（重要：实时侦测变化）

### Description
在 Flow 执行的整个期间，此 Action 在后台求值默认表达式；若结果发生变化，就把新值转发到 `changed` 输出。Flow 启动时先求值一次并转发，之后**仅当结果发生变更**时才转发。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Expression | EXPRESSION (any) | — | 要持续求值的表达式。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。
- `changed` – DATA(any) | **MANDATORY**：表达式的值在开始时传递一次，之后仅当结果有变化时才经此输出传递。

### LVGL/嵌入式 UI 关联（重点）
- 嵌入式 UI 实时刷新的利器：把要监视的变量/表达式（如传感器读数、状态标志）放进 `Expression`，其 `changed` 输出接到更新控件的 Flow，即可在数据变化时自动更新界面，无需轮询。
- 常与 A73 `SetVariable` 形成闭环：某处 `SetVariable` 改值 → `Watch` 侦测到变化 → 推送给显示控件。
- 注意它是“后台持续求值”，适合绑定少量关键变量，避免过多 Watch 影响性能。

---

## A92. WriteSetting（重要：持久化设置）

### Description
此 Action 把指定 Key 加入 `.eez-project-runtime-settings` 文件（与持久变量同一文件）；若该 Key 已存在，则用 `Value` 更新其值。

> 注意：WriteSetting 与 ReadSetting 用于把“希望 Dashboard 项目重启后保留”的设置存入/读出该文件。使用**持久变量**更方便，因为无需专门执行存/取 Action。

### Properties（Specific）

| 名称 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| Key | EXPRESSION (string) | — | 要添加/更新的键名字符串。 |
| Value | EXPRESSION (any) | — | 要创建或更新的键值。 |

### Inputs
- `seqin` – SEQ | OPTIONAL。

### Outputs
- `seqout` – SEQ | OPTIONAL。

### LVGL/嵌入式 UI 关联（重点）
- 与 A61 `ReadSetting` 成对，实现设置“落盘持久化”。典型流程：用户改设置 → `WriteSetting(Key, Value)` 保存；项目重启 → `ReadSetting(Key)` 读回并 `SetVariable` 恢复界面。
- 持久变量是更优替代方案；仅在需要自定义 Key/Value 命名空间或兼容既有文件时选用本对 Action。

---

## 附：本范围系统结构体速查

| 结构体 | 出现于 | 主要成员 |
|--------|--------|----------|
| `struct:$MQTTMessage` | A47 | `topic` (string)、`payload` |
| `struct:$RegExpResult` / `$RegexpMatch` | A62 | `index` (integer)、`texts` (array:string)、`indices` (array:array:integer) |
| `struct:$SerialPort` | A69 | `manufacturer` (string)、`serialNumber` (string)、`path` (string) |
| `struct:$UDPMessage` | A89 | `payload` (blob)、`address`、`port` |

## 附：嵌入式 UI 重点 Action 索引
- 页面/导航：`A53 OnEvent`、`A72 SetPageDirection`、`A78 ShowPage`、`A80 Start`
- 输入控件：`A75 ShowKeyboard`、`A76 ShowKeypad`、`A77 ShowMessageBox`
- 状态/刷新：`A73 SetVariable`、`A91 Watch`
- 持久化：`A61 ReadSetting`、`A92 WriteSetting`
- 运行时外观：`A55 OverrideStyle`
