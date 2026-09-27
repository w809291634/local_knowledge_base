# EEZ Studio 参考指南摘录：变量、样式与色彩主题、位图、字体、文本

> 本文档提取自 EEZ Studio Reference Guide（参考手册）第 8–12 章，面向本地知识库的软件使用笔记。
> 覆盖章节：P8 Variables、P9 Styles and Color themes、P10 Bitmaps、P11 Fonts、P12 Texts。
> 约定：所有英文标识符（属性名、函数名、常量名等）保持原文，不翻译。

---

# P8. Variables（变量）

## P8. 概述

- 变量（variable）用于存储可以在后续被修改的数据。
- 启用了 Flow 支持的项目（Project with Flow support）可以拥有 **全局变量（global variables）** 和 **局部变量（local variables）**：
  - 全局变量：在所有 Flow 中均可见。
  - 局部变量：仅在定义它的那个 Flow 内部可见。
- 未启用 Flow 支持的项目只能拥有全局变量，且这些变量必须是 **Native（原生）** 变量，即由原生代码（C++）管理。
- 添加变量：使用 **Variables panel（变量面板，Fig. 83）**，会弹出一个对话框用于定义变量的基本参数（Name、Type、Default value）。
- 编辑变量参数：在 Variables panel 中选中变量后，使用 **Properties panel（属性面板）** 进行编辑（EEZ-GUI / LVGL / Dashboard 三种项目分别对应 Fig. 84 / Fig. 85 / Fig. 86）。

### 变量属性（Properties panel 字段说明）

| 字段 | 说明 |
|------|------|
| **Id** | 仅 EEZ-GUI 项目特有。用于 Page、Action、Global Variable、Style、Font、Bitmap、Colors 等资源。在项目编辑器中这些资源通过 name 引用，但构建（build）后 name 不再使用，改用数值 ID。此字段可选：不指定时构建时自动分配 ID；若希望某对象始终获得同一个 ID，则需手动定义。典型用途：主项目（如 EEZ BB3 的 `modular-psu-firmware.eez-project`）被 BB3 Applets 和 BB3 MicroPython scripts 引用时，需要固定 ID。⚠️ 一旦设置 ID 不应再改动，否则所有依赖它的 BB3 脚本都需重新构建。 |
| **Name** | 变量在其他部分通过 name 引用。命名规则：以字母或下划线 `_` 开头，后接零个或多个字母、数字或下划线；不允许空格。 |
| **Description** | 可选字段，变量的描述。 |
| **Type** | 变量存储的数据类型。添加变量时，建议的默认值取决于所选类型（如 Integer 默认 0，Boolean 默认 False）。 |
| **Native** | 变量由原生代码（C++）管理。Dashboard 项目不能拥有 Native 变量。 |
| **Default value** | Flow 启动时变量的初始值，使用 JSON 表示法（https://www.json.org/json-en.html）。例如：`123`、`"Hello"`、`true`。Struct 类型：`{ "member1": 42, "member2": "Hello" }`；Array 类型：`[1, 2, 3]` 或 `["string1", "string2", "string3"]`。 |
| **Default value list** | 仅在不启用 EEZ Flow 的 EEZ-GUI 项目中支持。 |
| **Used in** | 见项目 Settings 中的 Configurations（章节 P13.2.1）。 |
| **Persistent（仅全局变量）** | 将变量的最后一个值保存到 `.eez-runtime-settings` 文件中，使下次项目运行时使用该值而非默认值。仅 Dashboard 项目支持。 |

## P8.1. Variables usage in the project with EEZ Flow enabled（启用 EEZ Flow 时变量的用法）

- 变量中存储的数据可以通过 **表达式（expression）** 访问。
- 用于处理变量的 Action 组件：
  - **Evaluate**：计算表达式（可使用变量），并通过 "result" 数据线发送结果。
  - **Watch**：监视变量值的变化。Flow 启动时总是先通过 Changed 数据线发送当前值，之后每次值变化都发送。
  - **SetVariable**：设置新的变量值。允许多个条目，每个条目包含 variable 与 expression 字段；Flow 执行时计算所得的表达式结果存入变量。
  - **SwitchCase / Compare / IsTrue**：根据变量值进行 Flow 分支的 Action。
- 变量也用于 **Widget 组件**：某些 Widget 属性可定义为表达式。这种情况下，该属性值会随表达式在 Flow 执行过程中变化。例如 Label widget 可显示某个变量的内容，并在该变量被修改时实时更新。

## P8.2. Variable types（变量类型）

### P8.2.1. Basic/Primitive types（基础/原始类型）

| 类型 | 说明 |
|------|------|
| **Integer** | 有符号 32 位整数（Signed 32-bit integer）。 |
| **Float** | IEEE 4 字节浮点数（IEEE 4-byte floating-point）。 |
| **Double** | IEEE 8 字节浮点数（IEEE 8-byte floating-point）。 |
| **Boolean** | 可保存 true 或 false。 |
| **String** | 字符序列。 |
| **Date** | Unix 时间戳（Unix timestamp）。 |
| **Blob** | 二进制大对象（Binary large object，**仅 Dashboard 项目**）。 |
| **Stream** | 数据流（**仅 Dashboard 项目**）。 |
| **Any** | 可保存任意数据类型。 |

### P8.2.2. Structures（结构体）
- 结构体类型在 Variables panel 的 **Structs 区段** 中定义。
- Struct 类型变量存储多个数据值，每个通过成员名（member name）访问；每个成员由其 name 与 type 定义。
- 结构体只能用于启用了 EEZ Flow 的项目。

### P8.2.3. Enums（枚举）
- 枚举类型在 Variables panel 的 **Enums 区段** 中定义。
- Enum 类型变量存储整型数据值，但只能包含受限的一组值；每个枚举成员由 name 与整数值（integer value）定义。

### P8.2.4. Objects（对象）
- 与 struct 类似，对象变量可保存多个值，每个通过成员名访问。成员名取决于对象变量的类型。例如：Instrument connection（仪器连接）、PostgreSQL connection（PostgreSQL 连接）。详见其他章节。
- 对象变量 **只能用于 Dashboard 项目**。

### P8.2.5. Arrays（数组）
- 数组变量存储多个数据值。

### P8.2.6. JSON objects（JSON 对象）
- JSON 是 Dashboard 项目中结构体的替代方案（**目前 JSON 仅支持 Dashboard 项目！**）。
- 结构体字段在开发时固定，运行时无法用新字段名扩展；而 JSON 值完全开放，开发时无需指定结构，运行时可构建任意 JSON 值。可认为 **结构体是静态类型（statically typed），JSON 是动态类型（dynamically typed）**。
- 一个 JSON 变量可以赋给 struct 或 array 变量，反之亦然。

### P8.2.7. Expressions（表达式）
- 表达式包含如何在 Flow 执行期间计算某个数据值的指令；其代码定义类似于 JavaScript 或其他类 C 语言。
- 表达式元素：

| 表达式元素 | 说明 / 示例 |
|-----------|------------|
| 字面量值（Literal value） | 例：`42`、`"Hello"`、`true` |
| 变量名（Variable names） | 例：`my_var` |
| 输入名（Input names） | 通过输入名检索数据输入中存储的数据。例：`input_name` |
| 二元运算符（Binary operator） | 例：`my_integer_var + 1` |
| 逻辑运算符（Logical operator） | 例：`my_integer_var < 10` |
| 一元运算符（Unary operator） | 例：`-my_integer_var` |
| 三元运算符（Ternary operator） | 例：`my_integer_var == 1 ? true : false`（当 my_integer_var 为 1 时求值 true，否则 false） |
| 函数调用（Function calls） | 例：`String.length(my_string_var)` |
| 括号 `()` | 指定求值顺序。例：`"Counter: " + (a + 1)` |
| 访问符 `.` | 结构体类型成员访问符。例：`my_struct_var.member1` |
| 访问符 `[]` | 数组元素访问符。例：`my_array_var[3]`、`my_array_var[index]` |
| 枚举值（Enum value） | 例：`MyEnumTypeName.Member1` |

- 表达式示例：
  - `var[i].member1`：`var` 是包含 struct 的数组，其成员为 `member1`；`i` 为整数变量；求值为第 i 个元素的 `member1` 值。
  - `var == State.START || var == State.EMPTY`：`var` 为 enum:State 类型，State 枚举有两个成员 START、EMPTY；当 var 为其中之一时求值 True。

### P8.2.8. Literals（字面量）

| 类型 | 说明 / 示例 |
|------|------------|
| Integer | `42` |
| Float 或 double | `01.03.14`（注：原文示例，疑似日期式写法，保留原文） |
| String | `"Hello world!"` |
| Template literals（模板字符串） | 以反引号 `` ` `` 包裹，支持多行字符串与内嵌表达式插值。例：`` `Measured voltage is ${voltage_var} V` `` 等同于 `"Measured voltage is " + voltage_var + " V"`。 `${...}` 内可为复杂表达式，如 `` `Progress: ${Math.round(factor, 2) * 100}%` ``。也支持多行字符串（见原文 HTML 示例）。 |
| Translated string（翻译字符串） | `T"text_resource_id"`（前缀 T 为强制要求）。 |
| Boolean | `true` 或 `false` |
| JSON | `` json`{ "a": 1, "b": 2, "c": { "arr": [1, 2, 3] } }` ``。详见 https://www.json.org/json-en.html |

### P8.2.9. Binary Operators（二元运算符）
- 每个二元运算符需要两个参数，书写于两参数之间，如 `<arg1> + <arg2>`。

**Addition `+`（加法）规则：**
- 任一参数为字符串则结果为字符串。例：`voltage + " V"` 当 voltage 为 `1.5` 时求值 `"1.5 V"`。
- 任一参数为 double 则结果为 double。
- 一个参数为 float、另一个为 float 或 integer 时，结果为 float。
- 两个参数均为 integer 时结果为 integer。

**类型组合结果表（加法 +）：**

| arg1 \ arg2 | integer | float | double | string | boolean | other_type |
|-------------|---------|-------|--------|--------|---------|------------|
| integer | integer | float | double | string | integer | err |
| double | double | double | double | string | double | err |
| float | float | float | double | string | float | err |
| string | string | string | string | string | string | err |
| boolean | integer | float | double | string | integer | err |
| other_type | err | err | err | err | err | err |

**Subtraction `-`（减法）结果表：**

| arg1 \ arg2 | integer | float | double | boolean | other_type |
|-------------|---------|-------|--------|---------|------------|
| integer | integer | float | double | integer | err |
| double | double | double | double | double | err |
| float | float | float | double | float | err |
| boolean | integer | float | double | integer | err |
| other_type | err | err | err | err | err |

**Multiplication `*`（乘法）结果表：**

| arg1 \ arg2 | integer | float | double | boolean | other_type |
|-------------|---------|-------|--------|---------|------------|
| integer | integer | float | double | integer | err |
| double | double | double | double | double | err |
| float | float | float | double | float | err |
| boolean | integer | float | double | integer | err |
| other_type | err | err | err | err | err |

**Division `/`（除法）结果表：**

| arg1 \ arg2 | integer | float | double | boolean | other_type |
|-------------|---------|-------|--------|---------|------------|
| integer | integer | float | double | integer | err |
| double | double | double | double | double | err |
| float | float | float | double | float | err |
| boolean | double | float | double | double | err |
| other_type | err | err | err | err | err |

**Remainder `%`（取余）结果表：**

| arg1 \ arg2 | integer | float | double | boolean | other_type |
|-------------|---------|-------|--------|---------|------------|
| integer | integer | float | double | integer | err |
| double | double | double | double | double | err |
| float | float | float | double | float | err |
| boolean | integer | float | double | integer | err |
| other_type | err | err | err | err | err |

**Left shift `<<`（左移）结果表：**

| arg1 \ arg2 | integer | boolean | other_type |
|-------------|---------|---------|------------|
| integer | integer | integer | err |
| boolean | integer | integer | err |
| other_type | err | err | err |

**Right shift `>>`（右移）结果表：**

| arg1 \ arg2 | integer | boolean | other_type |
|-------------|---------|---------|------------|
| integer | integer | integer | err |
| boolean | integer | integer | err |
| other_type | err | err | err |

**Binary AND `&`（按位与）结果表：**

| arg1 \ arg2 | integer | boolean | other_type |
|-------------|---------|---------|------------|
| integer | integer | integer | err |
| boolean | integer | integer | err |
| other_type | err | err | err |

**Binary OR `|`（按位或）结果表：**

| arg1 \ arg2 | integer | boolean | other_type |
|-------------|---------|---------|------------|
| integer | integer | integer | err |
| boolean | integer | integer | err |
| other_type | err | err | err |

**Binary XOR `^`（按位异或）结果表：**

| arg1 \ arg2 | integer | boolean | other_type |
|-------------|---------|---------|------------|
| integer | integer | integer | err |
| boolean | integer | integer | err |
| other_type | err | err | err |

### P8.2.10. Logical operators（逻辑运算符）
- 逻辑运算符也是二元运算符，结果为 Boolean 值。

| 类型 | 说明 |
|------|------|
| `==` | Equal to（等于） |
| `!=` | Not equal（不等于） |
| `<`  | Greater than（大于，原文如此标注） |
| `>`  | Less than（小于，原文如此标注） |
| `<=` | Less than or equal to（小于等于） |
| `>=` | Greater than or equal to（大于等于） |
| `&&` | And（与） |
| `||` | Or（或） |

### P8.2.11. Unary operators（一元运算符）

| 类型 | 说明 |
|------|------|
| `-` | Negate the value（取负） |
| `~` | Binary invert（按位取反） |
| `!` | Logical invert（逻辑取反） |

### P8.2.12. Conditional (ternary) operator（条件/三元运算符）
- 唯一需要三个操作数的运算符：条件后跟问号 `?`，条件为真时执行的表达式后跟冒号 `:`，最后为条件为假时执行的表达式。

## P8.3. Functions（函数）

### P8.3.1. System
- **System.getTick**：获取从 Flow 执行开始至今经过的毫秒数。参数：None。返回值：毫秒值，类型 Integer。

### P8.3.2. Flow
- **Flow.index**：当前 List / Grid widget 中元素的索引（详见这两个 widget 的说明）。参数：`index`（Integer）—— 嵌套 List/Grid 时，用 0 表示最内层，1 表示上一层的 List/Grid，依此类推。返回：元素索引，类型 Integer。
- **Flow.isPageActive**：若在某 page 内执行，且当前该 page 为活动页则返回 true，否则 false。参数：None。返回：Boolean。
- **Flow.pageTimelinePosition**：若在 page 或 custom widget 内执行，返回该 page / custom widget 动画时间线的当前位置。参数：None。返回：时间线位置，类型 Boolean（原文标注）。
- **Flow.makeValue**：创建 Struct 类型的新值。参数：`structName`（String，结构体名）、`value`（JSON，结构体名/值）。返回：创建的 struct 值，类型 Struct。
- **Flow.makeArrayValue**：创建 array 类型的新值。参数：`value`（JSON，数组值）。返回：创建的 array 值，类型 Array。
- **Flow.languages**：获取多语言项目中定义的语言列表（字符串数组）。参数：None。返回：语言数组，类型 Array:string。
- **Flow.translate**：翻译文本资源 ID，等同于 `T"textResourceID"`。参数：`textResourceID`（String）。返回：翻译后的字符串，类型 String。
- **Flow.parseInteger**：将给定字符串解析为整数。参数：`str`（String）。返回：解析的整数，类型 Integer。
- **Flow.parseFloat**：将给定字符串解析为 float。参数：`str`（String）。返回：Float。
- **Flow.parseDouble**：将给定字符串解析为 double。参数：`str`（String）。返回：Double。

### P8.3.3. Date
- **Date.now**：返回当前日期。参数：None。返回：当前 datetime，类型 Now（原文）。
- **Date.toString**：将给定日期转换为字符串。参数：`date`（Date）。返回：Date string，类型 String。
- **Date.toLocaleString**：将给定日期转换为 locale 字符串。参数：`date`（Date）。返回：String。
- **Date.fromString**：将字符串转换为日期。参数：`dateStr`（String）。返回：Date。
- **Date.getYear**：从日期取年份。参数：`date`（Date）。返回：Integer。
- **Date.getMonth**：从日期取月份（1–12）。参数：`date`（Date）。返回：Integer。
- **Date.getDay**：从日期取当月日（1–31）。参数：`date`（Date）。返回：Integer。
- **Date.getHours**：取小时（0–23）。返回：Integer。
- **Date.getMinutes**：取分钟（0–59）。返回：Integer。
- **Date.getSeconds**：取秒（0–59）。返回：Integer。
- **Date.getMilliseconds**：取毫秒（0–999）。返回：Integer。
- **Date.make**：由参数构造日期。参数：`year`(Integer)、`month`(Integer)、`day`(Integer)、`hours`(Integer)、`minutes`(Integer)、`seconds`(Integer)、`milliseconds`(Integer)。返回：构造的 Date。

### P8.3.4. Math
- **Math.sin**：返回弧度角 x 的正弦（介于 -1 与 1 之间）。参数：`x`（Integer|Float|Double）。返回：Float|Double。
- **Math.cos**：返回弧度角 x 的余弦（介于 -1 与 1 之间）。参数：`x`（Integer|Float|Double）。返回：Float|Double。
- **Math.pow**：返回底数的指数次幂。参数：`base`（Integer|Float|Double）、`exponent`（Integer|Float|Double）。返回：Float|Double。
- **Math.log**：返回 x 的自然对数（以 e 为底），x ≥ 0。返回：Float|Double。
- **Math.log10**：返回 x 的以 10 为底的对数，x ≥ 0。返回：Float|Double。
- **Math.abs**：返回绝对值。若 x 为负（含 -0）返回 -x，否则返回 x；结果恒为非负数或 0。返回：Integer|Float|Double。
- **Math.floor**：向下取整，返回 ≤ x 的最大整数（等同于 `-Math.ceil(-x)`）。返回：Integer|Float|Double。
- **Math.ceil**：向上取整，返回 ≥ x 的最小整数（等同于 `-Math.floor(-x)`）。返回：Integer|Float|Double。
- **Math.round**：四舍五入为最接近的整数。返回：Integer|Float|Double。
- **Math.min**：返回输入参数中的最小值。参数：`value1, …, valueN`（Integer|Float|Double，零个或多个）。返回：Integer|Float|Double。
- **Math.max**：返回输入参数中的最大值。参数：`value1, …, valueN`（Integer|Float|Double，零个或多个）。返回：Integer|Float|Double。

### P8.3.5. String
- **String.length**：返回字符串长度。参数：`string`（String）。返回：Integer。
- **String.substring**：返回从 start 索引（含）到 end 索引（不含）的子串；若不提供 end 则到字符串末尾。参数：`string`(String)、`start`(String，起始索引)、`end`(可选，String，排除索引)。返回：String。
- **String.find**：搜索字符串并返回指定子串首次出现的索引；未找到返回 -1。参数：`string`(String)、`substring`(String)。返回：索引，类型 String（原文标注）。
- **String.padStart**：用另一字符串（必要时多次）填充当前字符串，直到达到给定长度。参数：`string`(String)、`targetLength`(Integer，目标长度；≤ str.length 时原样返回)、`padString`(String，填充串；超出部分从末尾截断)。返回：String。
- **String.split**：以分隔符将字符串拆分为有序子串数组。参数：`string`(String)、`separator`(Integer，分隔模式)。返回：Array:string。

### P8.3.6. Array
- **Array.length**：给定数组的元素个数。参数：`array`（Array|json）。返回：Integer。
- **Array.slice**：返回数组从 start 到 end（不含 end）的浅拷贝新数组，原数组不变。参数：`array`(Array)、`start`(Integer，起始零基索引)、`end`(可选，Integer，结束零基索引)。返回：Array。
- **Array.allocate**：创建给定大小的新数组。参数：`size`（Array，尺寸数值）。返回：Array。
- **Array.append**：将元素追加到数组末尾并返回新数组（原文描述段落误写为字符串分割，按函数名理解）。参数：`array`(Array|json)、`value`(Any，要追加的元素值)。返回：Array。
- **Array.insert**：在指定位置插入元素并返回新数组，原数组不变。参数：`array`(Array|json)、`position`(Integer，零基插入索引)、`value`(Any)。返回：Array。
- **Array.remove**：移除指定位置的元素并返回新数组，原数组不变。参数：`array`(Array|json)、`position`(Integer，零基索引)。返回：Array。
- **Array.clone**：数组的深拷贝。参数：`array`(Array)。返回：Array。

### P8.3.7. JSON
- **JSON.get**：获取 JSON 对象的属性值。参数：`json`(json)、`property`(string，属性路径，如 `"users.3.name"`)。返回：属性值，可为另一 JSON 对象、number、string、boolean 或 date。
- **JSON.clone**：JSON 对象的深拷贝。参数：`json`(json)。返回：json。

### P8.3.8. LVGL
- **LVGL.MeterTickIndex**：用途见 LVGL Meter Widget 说明（章节 W33）。参数：None。返回：索引号，类型 integer。

## P8.4. Expression Builder（表达式构建器）
- 表达式在 Action 与 Widget 组件中均受支持。每个可由表达式求值的组件属性都带有 `...` 图标，点击可打开 **Expression Builder（Fig. 87）**。
- 表达式既可手动输入，也可通过 Expression Builder 构建。

---

# P9. Styles and Color themes（样式与色彩主题）

## P9.1. Overview（概述）
- 样式（Styles）便于定义一整套视觉属性，并统一各 widget 的外观。
- 样式属性可在多个层级（scope）设置，即存在多种作用域：
  - **Local（局部）**：基础层级/作用域，所有样式属性仅应用于该 Widget。当要在多个 Widget 上复用同一套样式时，可使用 Styles panel 中定义的 **Project style（项目样式）**。
  - 使用 Project style 可实现一致性（相似用途的 Widget 外观一致）与可维护性（改动一处自动传播到所有使用该样式的 Widget）。
- 样式属性是**可继承的**：一个 Style 的某属性可继承另一个 Style 的对应属性（子样式继承父样式的所有属性）。
- 此外，所有包含颜色定义的样式属性都可从 **Color Theme（色彩主题）** 继承颜色（见 P9.4.2）。

## P9.2. Style properties（样式属性）
- 选中 Widget 后，局部定义的样式参数位于 Widget 属性面板的 **Style 子区段（Fig. 88 中 (2)）** 内。
- 属性数量与 Style 区段的呈现取决于项目类型（Fig. 88 为 EEZ-GUI；Fig. 89 为 Dashboard 的 Button；Fig. 90 为 LVGL 的 Label）。
- 样式属性数量还随 Widget 类型与 Project 类型变化。具有多状态（Default、Focused、Disabled 等）的 Widget 可为每个状态分别定义样式属性。

## P9.3. Project Styles（项目样式）
- Project style 有独立面板（(1)），可搜索、添加、删除。选中某 Project style 后，所有属性显示在 Properties panel（(5)，与 Widget/Action 共用），样式名显示在顶部（(4)）。
- 样式列表下方有预览区。EEZ-GUI 项目样式有两种预览：使用 Color / Background Color 时（(2)），以及使用 Active Color / Active back. color 时（(3)）。LVGL 项目的预览区见 Fig. 92（(6)）。

### P9.3.1. Creating a new Style（创建新样式）
- 新建 Project style 需定义唯一 **Name（Fig. 93）**。在 LVGL 项目中还需选择该样式将应用于哪种 **Widget type（Fig. 94）**。
- 也可直接从选中 Widget 的局部样式，通过 Use Style 属性的弹出菜单中的 **Create New Style** 选项新建 Project style。
- 弹出菜单项：

| 菜单项 | 说明 |
|--------|------|
| **Reset All Modification** | 重置（清除）所有局部修改。 |
| **Create New Style** | 用当前选中 Widget 的样式设置创建新 Project style（弹出如 Fig. 93 / Fig. 94 的对话框）。创建成功后也会赋值给该 Widget。 |
| **Update Style** | 用局部修改更新该 Widget 所引用的 Project style；因此这些局部修改会应用到所有使用该 Project style 的其他 Widget。 |

## P9.4. Style hierarchy（样式层级/继承）
- Project style 可继承属性：子（child）样式继承其父（parent）样式的所有属性。"子—父"关系在 Project style 表中显示，改变位置即可设置/重置子关系。继承可多级：一个 child 可成为另一个 child 的 parent（例：Style `edit_value_active_M_center` 有两个 child：`edit_value_active_S_center` 与 `edit_value_active_M_left`；其中 child `edit_value_active_S_center` 又是 `icon_and_text_S` 与 `edit_value_active_S_center_icon` 的 parent）。
- LVGL 项目的 Project style 还定义了 Widget type，因此只能在**相同 Widget type** 的样式间建立子—父关系。LVGL 的 Style panel（Fig. 97）除样式名外还显示 Widget type 图标（(4)），以便判断某样式能否成为某 parent 的 child。
- 设置 child 位置通过拖拽（drag & drop，Fig. 98）完成：按住要成为 child 的样式（(1)），拖到将作为 parent 的样式上直到出现导航线（(2)），向右移动使线相对 parent 名称缩进，松手后该样式即缩进显示于 parent 下方（(3)）。重置 child 位置同样用拖拽（Fig. 99）。

### P9.4.1. 从调色板（palette）设置样式属性颜色
- 含颜色定义的属性可通过两种方式设置，第一种使用 **Color picker（取色器）**。
- 在 Project style 列表（(1)）选中样式后其名称出现在 Properties panel（(2)），点击要设色的属性（(3)）打开 Color picker；移动光标选色，其 hex 与 RGB 值会同时显示在下部，也可直接输入 hex / RGB 值。

### P9.4.2. 使用 Color theme 设置样式属性颜色
- 另一种方式使用 Color theme：在 Theme panel（(1)）选择色彩主题，在 Styles panel 选择要设色的 Project style；在 Properties panel（(3)）显示该样式所有属性；在 Theme panel 选择要赋予的颜色（(4)），拖拽到该属性名称字段（(5)）即可。
- 也可直接输入 Color theme 中的颜色名（如 `status_ok`）来设置属性颜色。

## P9.5. Style attributes（样式属性）

> 说明：以下分 EEZ-GUI、Dashboard、LVGL 三类项目列出样式属性。

### P9.5.1. EEZ-GUI project（EEZ-GUI 项目）
- 以 LineChart widget 为例，它有多个样式定义：Normal、Title、Legend、X axis、Y axis、Marker（(1)）。首个属性 **Use style（(2)）** 决定从哪个 Project style 继承属性，可对每个样式定义分别设置。更改 Use style 会立即将所选 Project style 的属性传播到 widget 对应属性（(3)）。
- 所有含颜色值的属性要么是 hex 颜色（如 `#4beef2`），要么是 Color theme 中定义的颜色名。
- 属性列表：

| 属性 | 说明 |
|------|------|
| **Use style** | 本 widget 从中继承样式属性的 Style 名称。若有局部修改属性，则局部修改优先于该样式定义。可为空（表示不继承任何 Style，仅用局部设置）。 |
| **Font** | Widget 内显示文本所用的字体。 |
| **Align horizontal** | 水平文本对齐（Horizontal text alignment）。 |
| **Align vertical** | 垂直文本对齐（Vertical text alignment）。 |
| **Color** | 文本颜色。 |
| **Background color** | Widget 背景色。 |
| **Background image** | Widget 的背景图像。 |
| **Active color** | Widget 处于 active 状态时的文本颜色。例：Button 被点击时；Text widget 启用 Blink 时在 Normal 与 Active 间周期切换。 |
| **Active back. color** | Widget 处于 active 状态时的背景色。 |
| **Focus color** | Widget 处于 focus（聚焦）状态时的文本颜色。 |
| **Focus back. color** | Widget 处于 focus 状态时的背景色。 |
| **Border size** | 绘制边框所用的线宽。 |
| **Border radius** | 边框圆角半径。可用 1、2 或 4 个以空格分隔的数字，含义：• `radius`：四角同值；• `radius1 radius2`：top-left / bottom-right 为 radius1，top-right / bottom-left 为 radius2；• `radius1 radius2 radius3 radius4`：依次为 top-left、top-right、bottom-right、bottom-left。 |
| **Border color** | 绘制边框所用的颜色。 |
| **Padding** | 文本偏移量。可用 1、2 或 4 个以空格分隔的数字：• `padding`：四边同值；• `padding1 padding2`：padding1 为上下、padding2 为左右；• `<p1> <p2> <p3> <p4>`：依次为上、右、下、左。 |
| **Opacity** | 0 = 完全透明，255 = 完全不透明。 |
| **Blink** | 启用后 Widget 在 Normal 与 Active 状态间周期切换。用不同的 normal / active 颜色实现闪烁效果。 |

### P9.5.2. Dashboard project（Dashboard 项目）
- Dashboard 项目样式基于 **CSS** 样式（https://developer.mozilla.org/en-US/docs/Web/CSS）。
- **Use style** 属性功能同 EEZ-GUI 项目。
- 每个样式属性都有 **Help 链接（Fig. 107）** 打开 Mozilla 上对应 CSS 属性说明页。可参考 CSS 文档了解以下属性：
  - Font family
  - Font weight
  - Font style
  - Align horizontal
  - Align vertical
  - Direction
  - Color
  - Background color
  - Background image
  - Active color
  - Active back. color
  - Focus color
  - Focus back. color
  - Border size
  - Border radius
  - Border style
  - Padding
  - Opacity
  - Box shadow
- 使用 **Blink 属性（(1)）** 实现闪烁（Fig. 108）；启用后可在 CSS preview（(2)）中查看生成的 CSS。可使用 **Additional CSS 区段** 输入任意自定义 CSS 属性（(3)）。CSS preview 为只读区段，汇总该样式生成的所有 CSS 属性，包括父样式与局部修改（注释为 `/* inline style */`）。

### P9.5.3. LVGL project（LVGL 项目）★重要
- LVGL 项目的样式定义按 **Parts（部件）、States（状态）、Categories（类别）** 分组。每个 Widget type 可有不同 Parts，可分别用样式定制。
- 示例（Fig. 109）：Slider widget 有三个 Parts：**Main、Indicator、Knob（(1)）**。每个 Part 可分别定义六个可能 State 的属性：**Default、Checked、Pressed、Checked|Pressed、Disabled、Focused（(2)）**。每个 State 可定义 **72 个属性**，归入 **11 个 Categories**（如 Position and Size、Padding、Background 等（(3)））。
- 与 EEZ-GUI / Dashboard 不同，LVGL 样式属性是通过勾选属性名左侧的复选框来启用的。
- 类别名、状态名、部件名处会显示已修改属性数量的提示（Fig. 110）。
- 更多 LVGL widget 样式说明见官方页面：
  - https://docs.lvgl.io/latest/en/html/overview/style.html
  - 各属性解释列表：https://docs.lvgl.io/latest/en/html/overview/style.html#properties
- ⚠️ 原文未逐一列出 72 个属性名与默认值（指向 LVGL 官方 style 属性文档）。但需明确：LVGL 样式按 Part × State × Category 组织，每个 Category 含一组属性。11 个 Categories（原文明确举例）至少包含：
  - **Position and Size（位置与尺寸）**
  - **Padding（内边距）**
  - **Background（背景）**
  - 其余 Categories 原文未列全名，仅说明共 11 类、72 个属性。已知 LVGL 标准样式类别（供参考，原文建议查官方文档）通常还包括：Border（边框）、Outline（轮廓）、Shadow（阴影）、Text（文本）、Line（线条）、Image（图像）、Arc（弧线）、Radius/Transform 等。请以 LVGL 官方文档为准。

### P9.5.4. Inheriting local Style attributes（继承局部样式属性）
- 局部样式可用于创建 Project style（并可赋给其他 Widget）。同样，Use style 用于从 Style panel 定义的 Project style 列表中设置局部样式（Fig. 111）。LVGL 项目中 Project style 关联特定 Widget type，因此只显示对应 Widget type 的 Project style 列表（Fig. 112）。
- 除列表选择外，也可直接输入有效名称（区分大小写）设置样式。
- 在 EEZ-GUI 与 Dashboard 项目中，每个属性右侧有指示器显示该属性是否局部修改过：已修改（实心方块，Fig. 113）/ 未修改（空心方块）；未修改时鼠标悬停会显示其所继承的 Project style 名称（Fig. 114）。
- 已修改属性可还原为从所设样式继承的原值：在指示器弹出菜单中选择 **Reset**（Fig. 115）；若属性定义的是背景色，菜单中还会出现设为透明背景的选项（Fig. 116）。

---

# P10. Bitmaps（位图）

- Bitmap panel（Fig. 117）列出项目中可用的位图。项目可包含无限数量的位图；选中位图（(2)）后可看到像素尺寸（(3)）与图像预览（(4)）。

## P10.1. Adding a bitmap（添加位图）
- 添加位图时弹出对话框，参数数量随项目类型不同（Fig. 118 EEZ-GUI / Fig. 119 Dashboard / Fig. 120 LVGL）。

| 字段 | 说明 |
|------|------|
| **Name** | 位图在其他部分通过 name 引用。 |
| **Image** | 从本地存储选择位图文件。 |
| **Bits per pixel（仅 EEZ-GUI）** | 色深：16（RGB565）或 32（RGBA，即 24 位色 + Alpha 通道）。 |
| **Color format（仅 LVGL）** | 见 https://docs.lvgl.io/8.3/overview/image.html#color-formats |

## P10.2. Bitmap properties（位图属性）
- EEZ-GUI 项目的位图属性（Fig. 121）如下表。

| 字段 | 说明 |
|------|------|
| **Id（仅 EEZ-GUI）** | 位图是项目中通过 name 引用的资源之一；构建后改用数值 ID。可选：不指定时构建时分配；若需固定 ID 则需定义（如 BB3 主项目被 Applets / MicroPython 脚本引用）。⚠️ 一旦设置不应改动，否则依赖它的 BB3 脚本需重建。 |
| **Name** | 位图通过 name 引用；可用 `...` 按钮改名。 |
| **Description** | 可选，位图描述。 |
| **Image** | 图像文件本身，嵌入保存在项目文件内。支持复制到剪贴板（(1)）、从剪贴板粘贴（(2)）、从本地加载（(3)）。 |
| **Bits per pixel（仅 EEZ-GUI）** | 16 = RGB565；32 = RGBA。 |
| **Style（仅 EEZ-GUI）** | 仅当 Bits per pixel = 16 时启用。仅使用整个 style 中的背景色；若默认位图中有透明像素，则显示背景色。 |
| **Always add to the generated code（仅 EEZ-GUI）** | 构建（生成源码）时，默认只将项目中用到的位图插入源码。若某位图用于原生代码而非 EEZ Studio 项目，可用此选项强制将其加入源码。 |
| **Color format（仅 LVGL）** | 见 https://docs.lvgl.io/8.3/overview/image.html#color-formats |

- LVGL Color format 常量名与 EEZ Studio 取值对应关系：

| LVGL 常量名 | EEZ Studio 值 |
|-------------|---------------|
| LV_IMG_CF_ALPHA_1_BIT | ALPHA 1 BIT |
| LV_IMG_CF_ALPHA_2_BIT | ALPHA 2 BIT |
| LV_IMG_CF_ALPHA_4_BIT | ALPHA 4 BIT |
| LV_IMG_CF_ALPHA_8_BIT | ALPHA 8 BIT |
| LV_IMG_CF_INDEXED_1_BIT | INDEXED 1 BIT |
| LV_IMG_CF_INDEXED_2_BIT | INDEXED 2 BIT |
| LV_IMG_CF_INDEXED_4_BIT | INDEXED 4 BIT |
| LV_IMG_CF_INDEXED_8_BIT | INDEXED 8 BIT |
| LV_IMG_CF_RAW | RAW |
| LV_IMG_CF_RAW_CHROMA | RAW CHROMA |
| LV_IMG_CF_RAW_ALPHA | RAW ALPHA |
| LV_IMG_CF_TRUE_COLOR | TRUE COLOR |
| LV_IMG_CF_TRUE_COLOR_ALPHA | TRUE COLOR ALPHA |
| LV_IMG_CF_TRUE_COLOR_CHROMA_KEYED | TRUE COLOR CHROMA |
| LV_IMG_CF_RGB565A8 | RGB565A8 |

- **Export bitmap file**：用于导出嵌入的图像。

## P10.3. Using a bitmap（使用位图）
- 位图可用于 **Bitmap widget（EEZ-GUI 与 Dashboard 项目）** 或 **Image widget（LVGL 项目）**，也可用于 Style。
- Dashboard 项目示例（Fig. 122）：将 Bitmap widget（(1)）加到页面；在 Specific 区段选择要用的位图（(2)），例中为名为 `background` 的位图（(3)）。
- 若 Widget 尺寸小于所选位图，位图会超出 Widget 边界（Fig. 123）。此时可用 **Resize to Fit Bitmap（(4)）** 使 Widget 尺寸适配位图（Fig. 124）。⚠️ 该选项仅在 Widget 当前尺寸与位图尺寸不匹配时可见。

---

# P11. Fonts（字体）★LVGL 字体流程为重点

- EEZ Studio 项目支持字体处理。使用前需在项目 Settings（Fig. 125）的 General 区段（(1)）启用 **Fonts** 选项（(2)）。
- 字体由取自 TTF 或 OTF 文件的一个或多个字符转换而成的抗锯齿位图（anti-aliased bitmaps）组成。
- 字体仅对 **EEZ-GUI 与 LVGL** 项目定义使用；**Dashboard 项目不使用字体**（Dashboard 使用矢量字体，按名称选择，对应 Style 的 Font Family 属性）。
- EEZ-GUI 项目的字体编辑选项多于 LVGL 项目，故分两小节描述。

## P11.1. EEZ-GUI project fonts（EEZ-GUI 项目字体）

### P11.1.1. Add new font（添加新字体）
- 在 Fonts panel 选择 **Add item**，弹出对话框（Fig. 126）。

| 字段 | 说明 |
|------|------|
| **Name** | 项目中使用的字体名称。 |
| **Font file** | 从本地存储选择字体文件。 |
| **Rendering engine** | 渲染引擎，可为 **FreeType**（https://freetype.org/）或 **OpenType**（https://opentype.js.org/），负责将矢量转为位图格式。 |
| **Font site (points)** | 字号，单位为 points（pt）。换算公式：1 pt = 1.333 px。 |
| **Create characters** | 若取消勾选，添加字体时不创建任何字符（字符可后加）。若勾选，则需选择要创建的字符范围；若想要所有字符为空，可用 **Create blank characters**。此选项鲜用，可用于创建 icon fonts（图标字体）。 |
| **From character** | 要创建的起始字符的十进制编号（如 32 = 0x20 = 空格）。 |
| **To character** | 要创建的结束字符的十进制编号。 |
| **Create blank characters** | 启用后所有添加的字符均为空。 |

- 字体添加成功并创建所需字符后，可在表格中查看（Fig. 127）；选中字符时右侧显示放大预览。

### P11.1.2. Add character（添加字符）
- 字体加入项目后，可添加新字符或删除已有字符（Fig. 128）。添加新字符时弹出对话框（Fig. 129）。

| 字段 | 说明 |
|------|------|
| **File path** | 本地字体文件路径；可删除已有或添加新路径。 |
| **Font size (points)** | 字号（pt）。换算：1 pt = 1.333 px。 |
| **Add option** | **Add single character at the end**：在表末尾添加单个字符；**Add characters from range**：从定义范围添加两个及以上字符；**Add missing characters**：仅在启用多语言（Texts panel，见 P12）且某字符串中存在字体未包含的字符时可用。 |
| **Create blank characters** | 启用后所有添加字符均为空。 |

## P11.2. LVGL project fonts（LVGL 项目字体）★关键：与 gen_fonts.py 流程相关

### P11.2.1. Add new font（添加新字体）
- LVGL 项目的字体处理使用库 **https://github.com/lvgl/lv_font_conv**。
- 在 Fonts panel 选择 **Add item**，弹出对话框（Fig. 130）。

| 字段 | 说明 |
|------|------|
| **Name** | 项目中使用的字体名称。 |
| **Font file** | 从本地存储选择字体文件。 |
| **Bits per pixel** | **1、2、4 或 8 位**。定义抗锯齿所用的灰阶数（shades）。数值越大字符越柔和，但字体占用存储空间也越大。 |
| **Font size (pixels)** | 字号，单位为像素（px）。 |
| **Ranges** | 定义要包含的**字符范围（ranges）和/或字符**。 |
| **Symbols** | 要包含的**字符列表（字符符号）**。 |

- 选中字体的属性见 Fig. 131，选中字符的属性见 Fig. 132；所有属性均为信息性（不可改），仅 Font 的 **Description** 可编辑（P.94）。

> 要点（对 gen_fonts.py 流程的意义）：
> 1. LVGL 字体由 TTF/OTF + `lv_font_conv` 生成，关键参数为 **字号(px)、bpp(1/2/4/8)、Ranges、Symbols**。
> 2. **Ranges** 与 **Symbols** 共同决定最终二进制字体包含哪些字形——`gen_fonts.py` 应据此收集项目所需 Unicode 码点范围与离散字符。
> 3. **bpp** 直接权衡显示质量与 Flash/RAM 占用，应与资源预算匹配。
> 4. 字体通过 **Name** 被 Widget 的样式（Style 中的 Font 属性）引用；LVGL 中 Widget 的 Style 关联特定 Widget type，字体引用需与所用 Style 一致。

### P11.2.2. Edit characters（编辑字符）
- 字体创建后，唯一可做的编辑是添加或删除字符。需在 Fig. 133 选择 **Add or Remove Characters**，通过对话框（Fig. 134）定义要加入字体表的 **Ranges 和/或 Symbols**。

> 注：LVGL 项目字体不支持像 EEZ-GUI 那样逐字符编辑位图，只能在"字符集合"层面增删（即重新运行 lv_font_conv 合并 Ranges/Symbols）。

---

# P12. Texts（文本 / 多语言）

- 支持多语言文本的项目可在 New Project Examples（Fig. 135）中找到，可作为多语言项目的起点。
- 多语言目前**仅 EEZ-GUI 与 Dashboard 项目**支持。

## P12.1. Texts panel（文本面板）
- Texts panel（Fig. 136）用于多语言文本编辑，包含三个选项卡（tab）：

| Tab | 说明 |
|-----|------|
| **Text resources（(1)）** | 所有多语言文本的 ID 列表。每个 Resource ID 都应有所有已定义语言的翻译。 |
| **Languages（(2)）** | 语言管理。 |
| **Statistics（(3)）** | 翻译统计。 |

- 所有已定义语言的文本内容可在 Properties（(4)）中查看。
- 项目中语言数量与文本资源数量**无限制**。添加新 Language 弹出对话框（Fig. 138）；添加新多语言 Text resource 弹出对话框（Fig. 139）。
- 翻译完整度可通过每个 Resource ID 与 Language 的进度条轻松检查；整体翻译统计显示在 Statistics tab（(3)）。Fig. 137 为全部翻译完成的示例。
- 运行时使用 **SelectLanguage** action 选择活动语言。
- 在表达式中使用本地化文本的两种方法：
  1. 使用特殊字面量 `T"<text resource ID>"`。例如 `T"Hello, world!"`（其中 "Hello, world!" 是 Text Resources tab 中的某个 ID）。
  2. 使用函数 `Flow.translate("<text resource ID>")`。例如 `Flow.translate("Hello, world!")`。
  - 由于更简单，推荐第一种方法。
- 若某语言当前无翻译，则使用文本资源 ID 本身；因此建议将该 ID 设为与某一语言（如英语）的翻译相同，以便作为回退（fallback）。

## P12.2. XLIFF Import/export（XLIFF 导入/导出）
- **XLIFF（XML Localization Interchange File Format）** 是基于 XML 的格式，用于标准化本地化数据在工具间的传递，也是 CAT（计算机辅助翻译）工具交换的通用格式。
- 借助该格式，专业译者可先用熟悉的工具准备翻译，再交付给开发者插入 EEZ Studio 项目。
- Import / Export 文本资源的 XLIFF 选项位于 **Language panel**。
- **导入（Import）**：弹出对话框（Fig. 140），需选择 XLIFF 文件路径，以及要将文本字符串导入到的**语言**（下拉框列出所有已定义语言）。
- **导出（Export，Fig. 141）**：需定义 **Source language（源语言）** 与 **Target language（目标语言）**，以及 **XLIFF 文件格式版本（1.2 或 2.0，取决于翻译工具支持）**。Fig. 142 为在 Poedit 中打开的导出 XLIFF 文件示例（源语言 GB，目标语言 FR）。

---

## 速查索引（关键标识符）

- **变量**：Variables panel、Properties panel、global / local / Native、Structs、Enums、Expressions、Binary/Logical/Unary/Ternary operators、Expression Builder。
- **函数**：System.getTick、Flow.*、Date.*、Math.*、String.*、Array.*、JSON.*、LVGL.MeterTickIndex。
- **样式**：Project style、Use style、Style hierarchy（child/parent）、Color theme、EEZ-GUI / Dashboard(CSS) / LVGL(Parts×States×Categories) 三类属性；Border radius / Padding 的多值语法；Opacity(0–255)；Blink。
- **位图**：Bits per pixel(16/32)、Color format(LVGL 常量映射)、Always add to generated code、Resize to Fit Bitmap、Bitmap/Image widget。
- **字体**：EEZ-GUI（FreeType/OpenType、pt、Create characters/blank）；LVGL（**lv_font_conv**、**Bits per pixel 1/2/4/8**、**Font size (pixels)**、**Ranges**、**Symbols**）。
- **文本**：Texts panel(Text resources/Languages/Statistics)、`T"..."` / `Flow.translate`、SelectLanguage、XLIFF 1.2/2.0 导入导出。
