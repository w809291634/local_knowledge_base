# EEZ Studio Actions 参考文档（A1 – A46）

> 本文档从 EEZ Studio Reference Guide 提取 **Actions** 章节 A1 至 A46 的详细用法说明，
> 用于本地知识库。所有标识符（Action 名、属性名、输入/输出名、枚举值等）均保持英文原样，
> 描述文字为中文。
>
> 覆盖范围：A1 AddToInstrumentHistory、A2 Animate、A3 CatchError、A4 ClipboardWrite、
> A5 CloseStream、A6 CollectStream、A7 Comment、A8 Compare、A9 ConnectInstrument、
> A10 Constant、A11 Counter、A12 CSVParse、A13 CSVStringify、A14 DateNow、A15 Delay、
> A16 DisconnectInstrument、A17 DynamicCallAction、A18 End、A19 Error、A20 Eval JS、
> A21 Evaluate、A22 ExecuteCommand、A23 FileAppend、A24 FileOpenDialog、A25 FileRead、
> A26 FileSaveDialog、A27 FileWrite、A28 FocusWidget、A29 GetInstrument、
> A30 GetInstrumentProperties、A31 HTTP、A32 Input、A33 InstrumentRead、
> A34 InstrumentTerminal、A35 InstrumentWrite、A36 IsTrue、A37 JSONParse、
> A38 JSONStringify、A39 Label IN、A40 Label OUT、A41 Log、A42 Loop、A43 LVGL、
> A44 Modbus、A45 MQTTConnect、A46 MQTTDisconnect。

---

## 通用属性（所有 Action 共有）

除各 Action "Specific" 专属属性外，几乎每个 Action 都包含以下三组通用属性区块。
为避免重复占用篇幅，此处统一说明，后续各 Action 仅在出现差异或需要强调时再提示。

### General（通用信息）
- **Description** `String`：组件的描述文字，显示在 Project editor/viewer 中组件下方；
  主工具栏可一键隐藏/显示所有组件的描述。

### Flow（数据流）
- **Inputs** `Array`：用户可自由添加的附加组件输入，用于在计算属性中的表达式时接收额外数据。
  每个输入有名称和类型；名称可在表达式中引用，类型用于 `project Check` 检查是否有对应类型的数据线连入。
- **Outputs** `Array`：用户可自由添加的附加组件输出，用于向外发送数据。每个输出有名称和类型。
  例如在 Loop 组件中，可将输出名用于 Variable 属性，此时 Loop 不会在每一步修改变量内容，
  而是通过该输出发送当前值。
- **Catch error** `Boolean`：若勾选，则组件会新增一个 `@Error` 输出；当该组件在 Flow 执行期间
  发生错误时，Flow 会经由该输出继续执行，传递的数据为错误的文本描述。

### Position and size（位置与尺寸）
- **Align and distribute** `Any`：对齐与分布图标。选中两个及以上组件时显示对齐图标，
  选中三个及以上时显示分布图标。

### 序列输入/输出约定
- **seqin** / **seqout**：大多数 Action 拥有标准序列输入 `seqin`（SEQ）和标准序列输出 `seqout`（SEQ），
  其是否 MANDATORY（必填）或 OPTIONAL（可选）在各自章节注明。

---

## A1. AddToInstrumentHistory

### 描述
用于向仪器的 History 视图添加新条目。目前仅支持添加 **Chart（图表）** 或 **Widget**
（Tabulator、Plotly 或 LineChart 控件）。例如在 Rigol Waveform Data 示例中，
通过该 Action 添加一个图表，成功添加后会在仪器 History 中显示（测试信号采集示例）。

### 属性（Specific）
| 名称 | 类型 | 默认值/取值 | 含义 |
|------|------|------------|------|
| Instrument | EXPRESSION (object:Instrument) | — | 要在其 History 中添加条目的仪器对象 |
| Item type | Enum | "Chart" / "Widget" | 要添加的条目类型 |
| Chart description | EXPRESSION (string) | — | 图表在 History 中的描述（仅 Item type=Chart） |
| Chart data | EXPRESSION (blob) | — | 包含样本的字符串或 blob（仅 Chart） |
| Chart sampling rate | EXPRESSION (float) | — | 采样率，即每秒样本数 SPS（仅 Chart） |
| Chart offset | EXPRESSION (double) | — | 公式 `offset + sample_value * scale` 中的偏移量，用于把样本值转换为 y 轴位置（仅 Chart） |
| Chart scale | EXPRESSION (double) | — | 显示样本时使用的 `offset + sample_value * scale` 比例（仅 Chart） |
| Chart format | EXPRESSION (string) | 见下 | Chart data 的格式（仅 Chart），取值：`"float"`（32 位小端 float blob）、`"double"`（64 位小端 float blob）、`"rigol-byte"`（8 位无符号整数 blob）、`"rigol-word"`（16 位无符号整数 blob）、`"csv"`（CSV 字符串，取第一列） |
| Chart unit | EXPRESSION (integer) | — | Y 轴显示的单位（X 轴始终为时间）（仅 Chart） |
| Chart color | EXPRESSION (string) | — | 深色背景下图表线条颜色（仅 Chart） |
| Chart color inverse | EXPRESSION (string) | — | 浅色背景下图表线条颜色（仅 Chart） |
| Chart label | EXPRESSION (string) | — | 图表标签（仅 Chart） |
| Chart major subdivision horizontal | EXPRESSION (integer) | — | 水平主分划（仅 Chart） |
| Chart major subdivision vertical | EXPRESSION (integer) | — | 垂直主分划（仅 Chart） |
| Chart minor subdivision horizontal | EXPRESSION (integer) | — | 水平次分划（仅 Chart） |
| Chart minor subdivision vertical | EXPRESSION (integer) | — | 垂直次分划（仅 Chart） |
| Chart horizontal scale | EXPRESSION (double) | — | 默认图表视图中的 X 轴缩放因子（仅 Chart） |
| Chart vertical scale | EXPRESSION (double) | — | 默认图表视图中的 Y 轴缩放因子（仅 Chart） |
| Widget | EXPRESSION (widget) | — | 对 Tabulator、Plotly 或 LineChart 控件的引用（仅 Item type=Widget）；参见 Output widget handle 属性了解如何获取该引用 |

（其余 General / Flow / Position 通用属性参见文首"通用属性"）

### 输入
- **seqin** `SEQ | MANDATORY`：标准序列输入。

### 输出
- **seqout** `SEQ | OPTIONAL`：标准序列输出。
- **id** `DATA(string) | OPTIONAL`：所添加 History 条目的 ID。可在 Chart Widget 中用来在
  仪表盘内显示该图表 History 条目。

### 示例
- Rigol Waveform Data

### UI 相关性
主要用于把采集到的数据（如示波器波形）以图表形式呈现到仪器 History；与 Plotly / LineChart
控件配合时，需通过控件的 `Output widget handle` 获取 widget 引用。

---

## A2. Animate

### 描述
若此 Action 用在 Page 或 User Widget 内部，它会把动画时间线位置从一处（From 属性）移动到另一处
（To 属性），并以给定速度（Speed 属性）播放。
若要瞬间跳到某一位置（To 属性），可将 Speed 设为 0——此时 From 值无意义（可设成与 To 相同）。
表达式 `Flow.pageTimelinePosition()` 可用于 From 属性，使动画从当前位置开始。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| From | EXPRESSION (float) | 起始位置，单位秒 |
| To | EXPRESSION (float) | 结束位置，单位秒 |
| Speed | EXPRESSION (float) | 决定动画时长。若为 1，则动画持续 `From - To` 秒；设为 2 表示两倍速，设为 0.5 表示两倍慢。若想让动画持续特定时间 T，可用公式 `T / (From - To)`，例如 T=0.5s、From=1s、To=3s 则 Speed = 0.5/(3-1) = 0.25。设为 0 时执行时立即跳到 To 位置 |

### 输入
- **seqin** `SEQ | OPTIONAL`：标准序列输入。

### 输出
- **seqout** `SEQ | OPTIONAL`：标准序列输出，在动画结束（即到达 To 位置）时激活。

### 示例
- Animation
- sld-eez-flow-demo

### UI 相关性
**核心 LVGL/UI 动画 Action**。驱动 Page/User Widget 的动画时间线，配合 `Flow.pageTimelinePosition()`
可实现基于当前位置的补间动画；在 UI 调试工具箱中常用于演示页面切换、控件进场等动画效果。

---

## A3. CatchError

### 描述
该 Action 捕获位于其所在 Flow 内、或由其执行所创建的任何子 Flow（例如调用 User action 时创建的
子 Flow）中发生的所有错误。

### 属性
仅有通用 General / Flow / Position 属性（见文首）。注意它同样带有 `Catch error` 通用属性。

### 输入
无额外 Specific 输入；仅有通用部分。

### 输出
- **seqout** `SEQ | OPTIONAL`：标准序列输出。
- **Message** `DATA(string) | MANDATORY`：发送所捕获错误描述的输出。

### UI 相关性
通用的错误兜底处理组件，可置于 Flow 末尾统一捕获异常，便于调试与日志记录。

---

## A4. ClipboardWrite

### 描述
将 `data` 属性指定的数据写入剪贴板，数据可以是文本或图像。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Data | EXPRESSION (any) | 写入剪贴板的数据，可为 string 或 blob。若为 blob 则视为图像 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`

### UI 相关性
可用于把界面文本/截图（blob 图像）复制到系统剪贴板，便于 UI 调试时导出结果。

---

## A5. CloseStream

### 描述
关闭给定的 stream。关闭后该 stream 不再接收新内容。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Stream | EXPRESSION (any) | 要关闭的 stream |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`

---

## A6. CollectStream

### 描述
将 stream 拼接成字符串。stream 数据以分块（chunks）到来，这些分块被拼接成字符串并发送到 `data`
输出。在 stream 生命周期内，该 Action 可多次通过 `data` 发送当前已收集字符串；当 stream 关闭后，
Flow 执行经由 `seqout` 输出继续。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Stream | EXPRESSION (any) | 其内容将被拼接成字符串的 stream |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`：stream 关闭后 Flow 经此输出继续。
- **data** `DATA(string) | MANDATORY`：拼接后的字符串经此输出发送；在 stream 生命周期内可多次发送，
  每次包含截至当时收集到的所有数据（字符串随时间增长）。

### 示例
- RegExp Stream

---

## A7. Comment

### 描述
该 Action 对 Flow 执行没有任何影响，仅用于在 Flow 中添加注释。

（无 Specific 属性、无额外输入/输出，仅有通用部分。）

---

## A8. Compare

### 描述
根据运算符比较表达式；若结果为真，Flow 经 True 输出继续，否则经 False 输出继续。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| A | EXPRESSION (any) | 比较左侧表达式 |
| B | EXPRESSION (any) | 比较右侧表达式。当运算符为 NOT 时不使用 |
| C | EXPRESSION (any) | 仅用于 BETWEEN 运算符：检查 `A >= B` 且 `A <= C` |
| Operator | Enum | 可选运算符，见下 |

**Operator 取值：**
- `=` ：A 等于 B（A == B）
- `<` ：A 小于 B
- `>` ：A 大于 B
- `<=` ：A 小于等于 B
- `>=` ：A 大于等于 B
- `<>` ：A 不等于 B（A != B）
- `NOT` ：A 不成立（!A）
- `AND` ：A 与 B 均为真（A && B）
- `OR` ：A 或 B 为真（A || B）
- `XOR` ：A 或 B 为真但不同时为真（A ^^ B）
- `BETWEEN` ：A 介于 B 与 C 之间（A >= B AND A <= C）

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`：标准序列输出。
- **True** `SEQ | OPTIONAL`：表达式为真时用于继续 Flow 的输出。
- **False** `SEQ | OPTIONAL`：表达式为假时用于继续 Flow 的输出。

### UI 相关性
条件分支组件，常用于 UI 逻辑中根据变量/控件状态决定走不同分支。

---

## A9. ConnectInstrument

### 描述
发起与仪器的**异步**连接，即该 Action 不会等待连接完成才退出到 seqout，而是立即退出。
可用 `instrument_variable.isConnected` 检查是否已连接。例如可在 Watch Action 中监视该表达式，
以捕捉连接建立的时刻，从而开始发送 SCPI 命令。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument | EXPRESSION (object:Instrument) | 要连接的仪器对象 |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | OPTIONAL`

---

## A10. Constant

### 描述
将设定的常量经 `value` 数据输出发送。该表达式**不得使用变量**。示例：`"string"`、`42`、
`3.14159265`、`true`、`Math.sin(0.5)`。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (string) | 其结果被发送到 value 输出的表达式；不可使用变量 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **value** `DATA(any) | MANDATORY`：发送所设常量的数据输出。

### UI 相关性
向 Flow 提供固定值（如颜色、阈值、字符串），常用于 UI 控件属性初始化或比较基准。

---

## A11. Counter

### 描述
用于将 Flow 的特定部分执行给定次数。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Count value | EXPRESSION (integer) | 定义循环中重复次数的表达式 |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | MANDATORY`：在达到给定重复次数前，Flow 每次经此输出继续。
- **done** `SEQ | OPTIONAL`：达到给定重复次数后，Flow 经此输出继续。

---

## A12. CSVParse

### 描述
解析 CSV 字符串，构造出设定类型的值，并经由 `result` 输出发送。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Input | EXPRESSION (string) | 要解析的 CSV 字符串 |
| Delimiter | EXPRESSION (string) | 字段分隔符，默认 `,` |
| From | EXPRESSION (integer) | 要处理的起始记录，1-based（第一条记录为 1 而非 0） |
| To | EXPRESSION (integer) | 要处理的最后记录，1-based |

### 输入
- **seqin** `SEQ | OPTIONAL`
- **text** `DATA(string) | MANDATORY`：接收待解析 CSV 字符串的输入。若不需要（即想通过 Input
  属性的任意表达式解析字符串），可在 Flow - Inputs 列表中删除此输入。

### 输出
- **seqout** `SEQ | OPTIONAL`
- **result** `DATA(any) | MANDATORY`：构造出的值发送至此输出，其值类型必须在 Flow - Outputs
  中指定。例如示例 CSV 应构造为 `array:CountryCity`，其中 `CountryCity` 结构含两个 string 字段
  `country` 与 `city`（结构名由开发者任意取）。

### 示例
- CSV

---

## A13. CSVStringify

### 描述
将 Flow 值转换为 CSV 字符串并发送到 `result` 输出。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Input | EXPRESSION (any) | 将被转换为 CSV 字符串的 Flow 值 |
| Delimiter | EXPRESSION (string) | 字段分隔符，默认 `,` |
| Header | EXPRESSION (boolean) | 若为 True，第一条记录将包含列名 |
| Quoted | EXPRESSION (boolean) | 若为 True，所有非空字段都会被引号包裹，即使无需包裹 |

### 输入
- **seqin** `SEQ | OPTIONAL`
- **input** `DATA(string) | MANDATORY`：接收待转换 Flow 值的输入。若不需要可在 Flow - Inputs 中删除。

### 输出
- **seqout** `SEQ | OPTIONAL`
- **result** `DATA(string) | MANDATORY`：构造的 CSV 字符串经此输出发送。

### 示例
- CSV

---

## A14. DateNow

### 描述
将当前时间（数据类型为 Date）经 `value` 数据输出发送。

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **value** `DATA(date) | MANDATORY`：发送当前时间的数据输出。

---

## A15. Delay

### 描述
在 Flow 执行中插入暂停。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Milliseconds | EXPRESSION (integer) | Flow 经 seqout 恢复执行前的暂停时长（毫秒） |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | MANDATORY`

---

## A16. DisconnectInstrument

### 描述
发起与仪器的**异步**断开连接，即不会等待断开完成才退出到 seqout，而是立即退出。
可用 `instrument_variable.isConnected` 检查是否已断开。例如可在 Watch Action 中监视该表达式，
以捕捉断开发生的时刻。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument | EXPRESSION (object:Instrument) | 要断开连接的仪器对象 |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | OPTIONAL`

---

## A17. DynamicCallAction

### 描述
执行一个名称在事先**未知**、而是在 Flow 执行期间确定的 User action（例如其名称可来自变量）。
这种 User action 必须**没有输入和输出**，只有 Start 和 End Actions。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Action | EXPRESSION (string) | 要执行的 User action 名称，通过执行时计算该表达式获得 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`

---

## A18. End

### 描述
用于终止 Flow 的执行。
- 若在 Page 内：表示应用执行结束。若是 Project editor 内执行的 Dashboard 项目，则从 Run 模式
  切换到 Edit 模式；若是运行在仪器上的 Dashboard，则执行被中断并显示 Start 按钮可重启；若是作为
  独立应用的 Dashboard，则应用被关闭。
- 若在 User action 内：表示 User action 执行结束，并激活调用该 User action 处的标准序列线。
- 若在 User widget 的 Flow 内：此 Action 无效。

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
无额外输出（仅有通用部分）。

---

## A19. Error

### 描述
该 Action 抛出一个错误，随后可被位于同一 Flow 或其父 Flow（任意祖先 Flow）中的 CatchError Action 捕获。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Message | EXPRESSION (string) | 描述错误类型的文本消息，该消息会被 CatchError Action 接收 |

### 输入
- **seqin** `SEQ | OPTIONAL`

---

## A20. Eval JS

### 描述
计算一个 JavaScript 表达式，并将结果经 `result` 输出发送。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Expression | TEMPLATE LITERAL | 要计算的 JavaScript 表达式。花括号 `{}` 内可插入 EEZ Flow 表达式，例如 `Math.random() * {num_items}` 中的 `{num_items}` 是 Flow 表达式，会先取 Flow 中 `num_items` 变量值再交给 JS 计算 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **result** `DATA(any) | MANDATORY`：发送 JS 表达式计算结果。默认输出类型为 `any`，
  建议改为具体类型。

### UI 相关性
在 UI 逻辑中执行任意 JS 计算（如随机值、数学运算），非常灵活。

---

## A21. Evaluate

### 描述
计算给定表达式并将结果经 `data` 输出（输出名 `result`）传递。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Expression | EXPRESSION (any) | 要计算的表达式 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **result** `DATA(any) | MANDATORY`：发送表达式计算值的数据输出。

### UI 相关性
最基础的"求值并传递"组件，常用于从变量/表达式中派生 UI 显示值。

---

## A22. ExecuteCommand

### 描述
执行外部命令（程序），命令可在 PATH 中，也可指定完整路径。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Command | EXPRESSION (string) | 命令名，即要执行的命令的完整文件路径 |
| Arguments | EXPRESSION (array:string) | 传递给命令的字符串参数数组 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **stdout** `DATA(stream) | OPTIONAL`：来自 stdout 的 stream 值。可用 CollectStream 收集为字符串、
  重定向到 Terminal 控件、用 RegExp 解析等。
- **stderr** `DATA(stream) | OPTIONAL`：来自 stderr 的 stream 值，用途同上。
- **finished** `DATA(integer) | OPTIONAL`：命令成功完成后经此输出继续；若发生错误则抛出异常
  （若启用 Catch error 可捕获）。

### 示例
- RegExp Stream

---

## A23. FileAppend

### 描述
向文件追加数据；若文件不存在则创建。数据可为 string 或 blob。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| File path | EXPRESSION (string) | 要写入的文件完整路径 |
| Content | EXPRESSION (string) | 要写入的内容，可为 string 或 blob。若为 blob 则忽略 encoding 属性 |
| Encoding | EXPRESSION (string) | 字符串内容的编码，可选：`"ascii"`、`"base64"`、`"hex"`、`"ucs2"`、`"ucs-2"`、`"utf16le"`、`"utf-16le"`、`"utf8"`、`"utf-8"`、`"binary"`、`"latin1"` |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`

---

## A24. FileOpenDialog

### 描述
显示系统文件打开对话框，并将设定的文件路径经 `file_path` 输出发送。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Filters | EXPRESSION (array:string) | 限制对话框内显示的文件类型，例如 `["PNG Images|png", "JPG Images|jpg", "GIF Images|gif"]`。可选，未设置则显示所有文件 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **file_path** `DATA(string) | MANDATORY`：发送所设定文件路径的输出。

### UI 相关性
UI 文件选择场景（如让用户挑选图片/数据文件加载到仪表盘）。

---

## A25. FileRead

### 描述
以 string 或 blob 形式读取文件内容并发送到 `content` 输出。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| File path | EXPRESSION (string) | 要读取的文件完整路径 |
| Encoding | EXPRESSION (string) | 输入数据编码，可选同 FileAppend。若 encoding 为 `"binary"` 则返回 blob 值，否则返回 string 值 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **content** `DATA(any) | MANDATORY`：文件内容输出。

---

## A26. FileSaveDialog

### 描述
显示系统文件保存对话框，并将设定的文件路径经 `file_path` 输出发送。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| File name | EXPRESSION (string) | 默认使用的文件名 |
| Filters | EXPRESSION (array:string) | 同 FileOpenDialog 的过滤器 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **file_path** `DATA(string) | MANDATORY`（见文档结构，输出含此；此外无额外输出列示）

---

## A27. FileWrite

### 描述
向文件写入数据，若文件已存在则替换。数据可为 string 或 blob。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| File path | EXPRESSION (string) | 要写入的文件完整路径 |
| Content | EXPRESSION (string) | 要写入的内容，可为 string 或 blob。若为 blob 则忽略 encoding |
| Encoding | EXPRESSION (string) | 内容编码，可选同 FileAppend |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`

### 示例
- CSV
- Screen Capture

### UI 相关性
Screen Capture 示例说明可结合截图（blob）写入文件，用于 UI 调试结果保存。

---

## A28. FocusWidget

### 描述
将控件置于焦点（Puts widget in focus）。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Widget | EXPRESSION (widget) | 对控件的引用。参见 Output widget handle 属性了解如何获取该引用 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`

### UI 相关性
**直接 UI 控件操作**：控制焦点切换，配合 `Output widget handle` 获取 widget 引用使用。

---

## A29. GetInstrument

### 描述
按 ID 检索仪器对象。仪器 ID 可在两处找到：在 Instruments Home 页面选中仪器时的 Instrument Properties，
以及仪器 Terminal 标签页头部。当你想访问特定仪器（即不想用对话框方式选择仪器）时使用此 Action。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument ID | EXPRESSION (string) | 要检索其对象的仪器 ID |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **instrument** `DATA(object:Instrument) | MANDATORY`：检索到的对象发送至此输出。

---

## A30. GetInstrumentProperties

### 描述
通过该 Action 可检索在 IEXT 仪器扩展中定义的仪器属性。例如在 Rigol Waveform Data 示例中，
想检索仪器有多少通道、每个通道用什么颜色。需要先定义 Flow 变量类型为
`struct:InstrumentProperties`（含 `channels` 成员，类型为 `array:InstrumentPropertiesChannel`，
其中含 `color` 等字段），再在一步中检索所有通道信息。之后可用
`Array.length(properties.channels)` 取通道数，用 `properties.channels[0].color` 取第 1 通道颜色。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument | EXPRESSION (object:Instrument) | 要检索属性的仪器 |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **properties** `DATA(any) | MANDATORY`：检索到的属性发送至此输出。

### 示例
- Rigol Waveform Data

---

## A31. HTTP

### 描述
发送 HTTP 请求并返回响应。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Method | Enum | HTTP 方法：GET、POST、PUT、PATCH、DELETE、HEAD、OPTIONS、CONNECT 或 TRACE |
| Url | EXPRESSION (string) | 请求的 url |
| Headers | Array | 发送到服务器的头列表，每项需设置头名称和字符串值 |
| Body | EXPRESSION (string) | 当选择 POST、PUT 或 PATCH 时发送给服务器的消息体 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **status** `DATA(integer) | OPTIONAL`：响应的状态码。
- **result** `DATA(string) | OPTIONAL`：收到的响应消息体。

### 示例
- Simple HTTP

### UI 相关性
可用来从网络 API 拉取数据渲染到 UI，或向服务器提交表单。

---

## A32. Input

### 描述
向 User action 或 User widget 添加数据输入。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Name | String | 输入名称 |
| Type | String | 输入数据类型 |

### 输入
（作为 User action/widget 的输入定义，无 seqin 之外的额外 Specific 输入）

### 输出
- **seqout** `SEQ | MANDATORY`：调用方传给 User action 的数据经此输出传递。

### UI 相关性
User widget 的参数化接口，用于把外部数据传入可复用控件逻辑。

---

## A33. InstrumentRead

### 描述
用于从仪器读取数据。通常用于实现专有（非 SCPI）命令协议的仪器。该 Action 将读取的 stream
发送到 `data` 输出。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument | EXPRESSION (object:Instrument) | 要读取数据的仪器对象 |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **data** `DATA(stream) | MANDATORY`：读取的 stream 发送至此输出。

---

## A34. InstrumentTerminal

### 描述
该控件用于与仪器交互。它由多个部分组成，部分可通过关联属性隐藏。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument | EXPRESSION (object:Instrument) | 选中的仪器对象 |
| Show connection status bar | EXPRESSION (boolean) | 显示/隐藏仪器连接状态栏 |
| Show shortcuts | EXPRESSION (boolean) | 显示/隐藏快捷键面板 |
| Show help | EXPRESSION (boolean) | 显示/隐藏命令帮助面板 |
| Show side bar | EXPRESSION (boolean) | 显示/隐藏带历史搜索选项的侧边栏 |
| Visible | EXPRESSION (boolean) | 若表达式为真则控件可见，为假则隐藏；可留空（始终可见） |
| Resizing | Any | 页面启用 "Scale to fit" 时控制缩放时控件位置/尺寸计算方式（Pin to edge / Fix size），二者互斥规则见原文 |
| Left | Number | 相对页面或父控件的 X 位置（像素）。支持 `+ - * /` 及括号数学表达式 |
| Top | Number | Y 位置（像素） |
| Width | Number | 宽度（像素） |
| Height | Number | 高度（像素） |
| Absolute pos. | String | 相对页面的绝对位置（只读） |
| Align and distribute | Any | 对齐/分布图标 |
| Center widget | Any | 水平/垂直居中图标 |
| Tab title | EXPRESSION (string) | 若控件是 Docking Manager 布局容器的子项，设置其所在标签的标题 |
| Event handlers | Array | 事件处理定义列表。每项需定义 Event（如 CLICKED）、Handler type（Flow 或 Action）、Action（若 Handler type=Action 则指定 User action 名） |
| Output widget handle | Boolean | 若启用则新增名为 `@Widget` 的输出，运行时控件创建后发送 widget 类型值，可用于需要控件引用的其他 Flow 部分（如 AddToInstrumentHistory 的 Plotly widget 属性） |

### 输入/输出
- 通用 Flow 的 Inputs / Outputs / Catch error 均适用。
- 额外输出 `@Widget`（当 Output widget handle 启用）。

### 示例
- BB3 SCPI Terminal and Dashboard

### UI 相关性
**仪器交互控件**，本身即 UI 组件；其 `Output widget handle`、`Event handlers`、`Visible`、
`Resizing` 等属性直接与 UI 布局、事件、引用相关。

---

## A35. InstrumentWrite

### 描述
向仪器发送字符串。通常用于实现专有（非 SCPI）命令协议的仪器。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Instrument | EXPRESSION (object:Instrument) | 要写入字符串的仪器对象 |
| Data | EXPRESSION (string) | 发送给仪器的字符串 |

### 输入
- **seqin** `SEQ | MANDATORY`

### 输出
- **seqout** `SEQ | OPTIONAL`

---

## A36. IsTrue

### 描述
计算设定表达式，若为真则 Flow 经 Yes 输出继续，否则经 No 输出。这两个输出至少有一个须用线连到输入。
默认添加 Value 输入并测试其真假；若要测试其他表达式，应在 Flow 属性中删除该输入并填入所需表达式。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (boolean) | 要测试其结果的表达式 |

### 输入
- **seqin** `SEQ | OPTIONAL`
- **value** `DATA(any) | MANDATORY`：接收待测试 Value 的输入。若不需要可在 Flow - Inputs 中删除。

### 输出
- **seqout** `SEQ | OPTIONAL`
- **Yes** `SEQ | OPTIONAL`：表达式为真时继续 Flow。
- **No** `SEQ | OPTIONAL`：表达式为假时继续 Flow。

### UI 相关性
条件判断组件，UI 状态分支常用（如判断某开关状态）。

---

## A37. JSONParse

### 描述
解析 JSON 字符串，构造设定类型的值并经由 `result` 输出发送。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (string) | 要解析的 JSON 字符串 |

### 输入
- **seqin** `SEQ | OPTIONAL`
- **text** `DATA(string) | MANDATORY`：接收待解析 JSON 字符串的输入；若不需要可在 Flow - Inputs 中删除。

### 输出
- **seqout** `SEQ | OPTIONAL`
- **result** `DATA(json) | MANDATORY`：构造的值发送至此，值的类型须在 Flow - Outputs 中指定。
  示例 JSON 数组元素含 `country`(string) 与 `city`(string)，应构造为 `array:CountryCity`。

### 示例
- JSON

---

## A38. JSONStringify

### 描述
将 Flow 值转换为 JSON 字符串并发送到 `result` 输出。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (any) | 将被转换为 JSON 字符串的 Flow 值 |
| Indentation | EXPRESSION (integer) | 生成 JSON 字符串使用的缩进量 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **result** `DATA(string) | MANDATORY`：构造的 JSON 字符串发送至此。

### 示例
- JSON

---

## A39. Label IN

### 描述
与 Label OUT Action 配合使用。所有进入 Label OUT 的线都会在同名 Label IN（同一 Flow 内，
即 Page 或 User Action）处汇合。不允许跨 Flow 跳转。可有多个 Label OUT 但只有一个同名 Label IN。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Label | String | 连接 Label IN 与 Label OUT 的标签名 |

### 输出
- **seqout** `SEQ | MANDATORY`：标准序列输出。

---

## A40. Label OUT

### 描述
与 Label IN 配合使用（同 A39 描述：同一 Flow 内汇合，不允许跨 Flow，多个 Label OUT 对应一个
同名 Label IN）。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Label | String | 连接 Label IN 与 Label OUT 的标签名 |

### 输入
- **seqin** `SEQ | MANDATORY`

---

## A41. Log

### 描述
计算设定表达式并将结果显示在 Logs 面板。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Value | EXPRESSION (string) | 其结果将显示在 Logs 面板的表达式 |

### 输入
- **seqin** `SEQ | OPTIONAL`
- **value** `DATA(string) | MANDATORY`：接收要显示在 Log 面板的 Value 的输入；若不需要可在
  Flow - Inputs 中删除（显示其他表达式时）。

### 输出
- **seqout** `SEQ | OPTIONAL`

### UI 相关性
**UI 调试利器**：在 Flow 运行中输出变量/状态到 Logs 面板，是 UI 调试工具箱最常用的调试输出手段。

---

## A42. Loop

### 描述
用于循环执行 Flow 的特定部分。该 Action 应放在要循环执行的 Flow 部分开头，从 `start` 输入进入；
在该部分结尾应返回到本 Action 的 `next` 输入。每次经过本 Action，设定变量的值会从 From 按 Step
改变到 To。在迭代完成前 Flow 会经过 `(From - To + 1) / Math.abs(step)` 次，随后经 Done 输出。
若想在到达 To 前停止循环，只需不再返回 `next` 输入即可。也可用 SetVariable 改变迭代变量以跳过
一个或多个步骤。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Variable | ASSIGNABLE EXPRESSION (integer) | 决定循环次数的变量，其值会被改变并测试是否需要新迭代 |
| From | EXPRESSION (integer) | 变量的初始值 |
| To | EXPRESSION (integer) | 变量的最终值 |
| Step | EXPRESSION (integer) | 每次经过时变量改变的值，可为正数或负数 |

### 输入
- **start** `SEQ | MANDATORY`：进入此输入时，变量设为 From 值，Flow 经 seqout 继续。
- **next** `SEQ | MANDATORY`：进入此输入时，变量按 Step 改变；若 Step 为正则测试是否 `<= To`，
  若为负则测试是否 `>= To`。未超过 To 则经 seqout 继续，否则经 Done 输出。

### 输出
- **seqout** `SEQ | MANDATORY`：迭代期间 Flow 经此输出继续。
- **done** `SEQ | OPTIONAL`：迭代完成时经此输出继续。

### 示例
- Loop

### UI 相关性
循环刷新 UI 列表/重复动画/批量更新控件时常用。

---

## A43. LVGL

### 描述
执行一个或多个 LVGL 特定的动作（Performs one or more LVGL specific actions）。这是与 LVGL/UI
最相关的核心 Action，可从 Flow 中直接调用大量 LVGL API 来切换屏幕、设置控件属性、播放动画等。

### 属性（Specific）

#### A43.2.1 Actions `Array`
要执行的动作列表。可用动作如下（每个动作带各自的参数）：

**屏幕（Screen）管理：**
- **Change Screen**：切换屏幕到指定屏幕
  - Screen：要切换到的屏幕
  - Fade mode：从上一页移动到新页时的动画选择
  - Speed：动画时长（毫秒）
  - Delay：动画开始前延迟（毫秒）
  - Use stack：将活动屏幕压入栈
- **Change to Previous Screen**：切换到上一屏幕
  - Fade mode / Speed / Delay（同上）
- **Create Screen**：创建屏幕（须在 Settings - Build 中启用 "Screens lifetime support"）
  - Screen：要创建的屏幕
- **Delete Screen**：删除屏幕（同上须启用 Screens lifetime support）
  - Screen：要删除的屏幕
- **Is Screen Created**：检查屏幕是否已创建（同上须启用）
  - Screen：屏幕
  - Store result into：存储屏幕状态的布尔变量

**对象坐标与尺寸（Obj X/Y/Width/Height）：**
- **Obj Set X / Obj Get X**：设置/获取对象的 x 坐标
  - Object / X（或 Store result into 存结果）
- **Obj Set Y / Obj Get Y**：设置/获取对象的 y 坐标
  - Object / Y（或 Store result into）
- **Obj Set Width / Obj Get Width**：设置/获取对象宽度
  - Object / Width（或 Store result into）
- **Obj Set Height / Obj Get Height**：设置/获取对象高度
  - Object / Height（或 Store result into）

**样式（Style）：**
- **Set Obj Style Prop**：设置样式中某属性的值
  - Object（Widget）、Property（要设置的样式属性）、Value（属性值）、Part（要设置属性的对象部分）、State（要设置属性的对象状态）
- **Obj Set Style Opa / Obj Get Style Opa**：设置/获取对象不透明度
  - Object、Opacity（0-255，或 Store result into）
- **Obj Add Style**：给对象添加样式（Object、Style）
- **Obj Remove Style**：移除对象样式（Object、Style）

**标志（Flag）：**
- **Obj Set Flag Hidden**：设置对象 hidden 标志（Object、Hidden）
- **Obj Add Flag / Obj Clear Flag / Obj Has Flag**：添加/清除/检查标志
  - Object、Flag（或 Store result into 存结果）

**状态（State）：**
- **Obj Set State Checked**：设置对象 checked 状态（Object、Checked）
- **Obj Set State Disabled**：设置对象 disabled 状态（Object、Disabled）
- **Obj Add State / Obj Clear State / Obj Has State**：添加/清除/检查状态
  - Object、State（或 Store result into）

**特定控件（Widget）操作：**
- **Arc Set Value**：设置圆弧值（Object、Value）
- **Arc Rotate Obj to Angle**：将对象旋转到圆弧（旋钮）当前角度
  - Object（圆弧）、Obj to rotate（要旋转的对象）、Offset（半径偏移，<0 表示更小半径）
- **Bar Set Value**：设置进度条值（Object、Value 0-100、Animated 是否动画）
- **Button Matrix Set Button Ctrl / Clear Button Ctrl**：设置/清除按钮矩阵按钮属性
  - Object、Button id（0 起始索引，不计入换行）、Ctrl（OR 组合属性，如 `LV_BUTTONMATRIX_CTRL.NO_REPEAT | LV_BUTTONMATRIX_CTRL.CHECKABLE`）
- **Calendar Set Today Date**：设置今日日期（Object、Year、Month[1..12]、Day[1..31]）
- **Calendar Set Showed Date**：设置当前显示日期（Object、Year、Month）
- **Calendar Set Highlighted Date**：设置高亮日期（Object、Year、Month、Day）
- **Calendar Get Pressed Date**：获取当前按下日期
  - Object、Store year into、Store month into、Store day into（整数变量）
- **Dropdown Set Selected**：设置下拉框选中项（Object、Selected 索引）
- **Image Set Src**：设置图像源（Object、Src 字符串）
- **Image Set Angle**：设置图像角度（Object、Angle，0.1° 精度，如 45.8° 设 458）
- **Image Set Zoom**：设置图像缩放（Object、Zoom，256 为不缩放，512 双倍，128 半倍）
- **Keyboard Set Textarea**：设置键盘对应的文本区（Object、Textarea）
- **Label Set Text**：设置标签文本（Object、Text）
- **QR Code Update**：更新二维码文本（Object、Text）
- **Roller Set Selected**：设置 Roller 选中项（Object、Selected 索引、Animated）
- **Slider Set Value**：设置滑块值（Object、Value、Animated）
- **Slider Set Value Left**：设置滑块左旋钮值（Object、Value left、Animated）
- **Slider Set Range**：设置滑块最小/最大值（Object、Min、Max）
- **Tabview Set Active Tab / Get Active Tab**：设置/获取 Tabview 活动标签
  - Object、Tab（0 起始索引）、Animated（或 Store result into 存索引）

**组（Group）焦点管理：**
- **Group Focus Obj**：聚焦对象（Object）
- **Group Focus Next / Prev**：聚焦组内下/上一个对象（Group）
- **Group Get Focused**：获取组内聚焦对象（Group、Store result into）
- **Group Focus Freeze**：冻结/释放焦点（Group、Enabled：true 冻结，false 释放）
- **Group Set Wrap**：设置 next/prev 是否环绕（Group、Enabled：true 环绕）
- **Group Set Editing**：手动设置模式（Group、Enabled：true 编辑模式，false 导航模式）

**动画（Anim）：** 以下动画动作参数结构相同：Object、Start、End、Delay（毫秒）、Time（毫秒）、
Relative（Start/End 是相对当前值还是绝对值）、Instant（是否立即应用 Start 值）、Path（动画路径）。
- **Anim X**：动画对象 x 坐标
- **Anim Y**：动画对象 y 坐标
- **Anim Width**：动画对象宽度
- **Anim Height**：动画对象高度
- **Anim Opacity**：动画对象不透明度
- **Anim Image Zoom**：动画图像缩放
- **Anim Image Angle**：动画图像角度

#### 通用属性（General / Flow / Position）
- **Description** `String`
- **Inputs** `Array`、**Outputs** `Array`、**Catch error** `Boolean`
- **Align and distribute** `Any`

### 输入
- **seqin** `SEQ | OPTIONAL`：标准序列输入。

### 输出
- **seqout** `SEQ | OPTIONAL`：标准序列输出。

### 示例
- Change Screen

### UI 相关性
**最重要、最庞大的 LVGL/UI 桥接 Action**。几乎涵盖所有常用 LVGL 控件属性设置与屏幕切换、
对象几何/样式/状态/标志/动画操作，是"从 Flow 驱动 LVGL UI"的总入口。配合各控件的
`Output widget handle`（`@Widget` 输出）获取 widget 引用后即可精准操作目标控件。

---

## A44. Modbus

### 描述
用于向 Modbus 服务器发送 Modbus 命令。若读取线圈（coils），读取值经 `values` 输出以
`array:boolean` 类型传递；若读取寄存器（registers），则以 `array:integer` 类型经 `values` 输出传递。

> 注：文档 "Outputs" 章节仅列示了 `seqout`；`values` 输出在描述中提及，应为读取类命令自动
> 提供的输出。使用时请以实际编辑器为准。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Connection | EXPRESSION (any) | 用于发送 Modbus 命令的串口连接 |
| Server address | EXPRESSION (integer) | 0–255 的数字，用于在串口连接上选择 Modbus 服务器 |
| Command | Enum | 要发送的命令，见下 |
| Register address | EXPRESSION (integer) | 单写寄存器地址（05 Write Single Coil 或 06 Write Single Register） |
| Starting register address | EXPRESSION (integer) | 多次读写的首寄存器地址 |
| Quantity of registers | EXPRESSION (integer) | 多次读写的寄存器数量 |
| Coil value | EXPRESSION (boolean) | 单写时的线圈值（用 05 时） |
| Register value | EXPRESSION (integer) | 单写时的寄存器值（用 06 时） |
| Coil values | EXPRESSION (array:boolean) | 多写时的线圈值数组 |
| Register values | EXPRESSION (array:integer) | 多写时的寄存器值数组 |
| Timeout (ms) | EXPRESSION (integer) | 等待服务器响应的最大时间（毫秒） |

**Command 取值：**
- `01 (0x01) Read Coils`
- `02 (0x02) Read Discrete Inputs`
- `03 (0x03) Read Holding Registers`
- `04 (0x04) Read Input Registers`
- `05 (0x05) Write Single Coil`
- `06 (0x06) Write Single Register`
- `15 (0x0F) Write Multiple Coils`
- `16 (0x10) Write Multiple Registers`

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`
- **values** `DATA`（描述中提及，类型随命令为 `array:boolean` 或 `array:integer`）

---

## A45. MQTTConnect

### 描述
发起与 MQTT 服务器的连接；若连接成功则发送 Connect 事件，若出错则发送 Error 事件。若出错或
已建立的连接中断，会周期性尝试重连直至恢复，并通过 Reconnect 事件报告。这一切在后台异步进行，
直到调用 MQTTDisconnect；任何状态变化都会通过事件报告，可由 MQTTEvent Action 处理。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Connection | EXPRESSION (object:MQTTConnection) | 用于建立服务器连接的 MQTT 连接名称 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
（文档 Outputs 区未额外列示，除通用 Flow 的 Outputs/Array 与 Catch error 外，连接结果通过
MQTTEvent 异步事件上报，而非同步输出。）

---

## A46. MQTTDisconnect

### 描述
发起与服务器的连接终止，将以 Close 事件确认，随后是 End 事件。

### 属性（Specific）
| 名称 | 类型 | 含义 |
|------|------|------|
| Connection | EXPRESSION (object:MQTTConnection) | 要终止通信的服务器 MQTT 连接名称 |

### 输入
- **seqin** `SEQ | OPTIONAL`

### 输出
- **seqout** `SEQ | OPTIONAL`：Flow 立即经此输出继续，后台尝试断开服务器。

### 示例
- MQTT

---

## 备注：通用属性、输入/输出复用说明

1. 上述每个 Action 的 "General / Flow / Position and size" 区块均包含文首"通用属性"所述内容
   （Description、Inputs Array、Outputs Array、Catch error、Align and distribute），仅在各节
   省略重复列示。
2. 多个 Action 的输入/输出带 `MANDATORY`（必须连接）或 `OPTIONAL`（可选）标记，已在各节注明；
   这对 Flow 连线正确性很关键。
3. 与 UI/LVGL 强相关的 Action 已在本表中单独标注 "UI 相关性"，重点包括：
   A2 Animate、A28 FocusWidget、A34 InstrumentTerminal（含 Output widget handle）、
   A41 Log、A42 Loop、A43 LVGL（核心），以及通用的值传递类 A10 Constant、A20 Eval JS、
   A21 Evaluate、A32 Input。
