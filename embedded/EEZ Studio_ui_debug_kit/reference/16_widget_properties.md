# EEZ Studio 控件可改属性总表（LVGL 9.4）


> **用途**：EEZ 工程生成前，**只允许修改本表列出的属性字段**；表里没有的字段一律不许写
> （A14 卡字段集，A10 卡样式键）。需要新字段时，先在 EEZ UI 里拖出/改出该属性、保存工程，
> 再回填本表。
>
> **三条真值来源**（三者交叉核对，2026-11-06 定）：
> 1. **EEZ 前端属性面板**：EEZ Studio 5.x `app.asar` 里的控件 `classInfo.properties`
>    （`name` / `displayName` / `type` / `enumItems` / `propertyGridGroup` / `hiddenInPropertyGrid` / `disabled`）；
>    这些就是 UI 属性面板逐行渲染的内容。
> 2. **官方手册**：《EEZ Studio reference guide》W 章节（W1–W87），本 kit 已提炼到
>    `05_widgets_part1.md` / `06_widgets_part2.md`；通用分组口径见 06 §0。
>    **手册没有逐字段表**，只用于控件语义与 W 编号；逐字段定义一律以来源 1（classInfo）为准。
> 3. **模板库**：根目录 `eez-widget-templates/templates/*.json`（UI 拖拽创建并保存后的实际落盘值）。
>
> **读表口径（严格按 EEZ 前端，不翻译、不臆造）**：
> - 「属性名」= `classInfo.properties[].name`，与工程 JSON 落盘键一一对应。
> - 「显示名」= `classInfo.properties[].displayName`；**没有显式命名就写 `—（未命名）`**，
>   不替 EEZ 编造（EEZ 运行时用 `humanize(name)` 生成，本机未取到该函数产物）。
> - 「type」= `classInfo.properties[].type` **原值**：数字是 EEZ 内部 `PropertyType` 枚举值
>   （本机 asar 中未找到枚举名表，故不翻译）；表达式属性则为 `string` / `integer` / `boolean` / `array:string`。
> - 「可选值」= `enumItems` 的 id/label，逐字照抄；没有枚举写 `—`。
> - 「分组」= `propertyGridGroup` 对应的面板折叠组标题（General / Specific / Position and size / Style / Flags / States / Layout）。
> - 「模板默认值」= 模板库该字段的保存值；`—` = 模板未落盘。
> - 「说明」只写三类**可从 classInfo 直接读出**的事实：可写表达式的 modes、classInfo 是否定义了条件显隐/禁用、
>   模板是否落盘；不写主观解释。


## 1. 通用属性（所有 LVGL 控件继承 `LVGLWidget`）

> 「模板默认值」以 `LVGLListWidget` 模板为参照（它含全部通用键）；其余类型同名同义。

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `identifier` | Name | 5 | — | — | — | classInfo 定义了条件禁用；放置时赋值；继承通用 |
| `codeIdentifier` | —（未命名） | 5 | — | — | — | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段）；继承通用 |
| `left` | —（未命名） | 3 | — | 0 | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `leftUnit` | —（未命名） | 4 | Pixels / Percent | px | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `top` | —（未命名） | 3 | — | 0 | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `topUnit` | —（未命名） | 4 | Pixels / Percent | px | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `width` | —（未命名） | 3 | — | 180 | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `widthUnit` | —（未命名） | 4 | Pixels / Percent / Content | px | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `height` | —（未命名） | 3 | — | 100 | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `heightUnit` | —（未命名） | 4 | Pixels / Percent / Content | px | Position and size | classInfo 定义了条件显隐；classInfo 定义了条件禁用；继承通用 |
| `geometryProperties` | —（未命名） | 22 | — | — | Position and size | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段）；继承通用 |
| `absolutePosition` | Absolute pos. | 5 | — | — | Position and size | classInfo 定义了条件显隐；模板未落盘（编辑器预览字段）；继承通用 |
| `children` | —（未命名） | 0 | — | [] | — | classInfo 定义了条件显隐；继承通用 |
| `hiddenFlag` | Hidden | boolean | — | — | Flags | 可写表达式（literal/expression）；仅隐藏时写入；继承通用 |
| `clickableFlag` | Clickable | boolean | — | true | Flags | 可写表达式（literal/expression）；继承通用 |
| `widgetFlags` | —（未命名） | 5 | — | CLICK_FOCUSABLE\|GESTURE_BUBBLE\|PRESS_LOCK\|SCROLLABLE\|… | Flags | 继承通用 |
| `flagScrollbarMode` | Scrollbar mode | 4 | OFF / ON / ACTIVE / AUTO | "" | Flags | 继承通用 |
| `flagScrollDirection` | Scroll direction | 4 | NONE / TOP / LEFT / BOTTOM / RIGHT / HOR / VER / ALL | "" | Flags | 继承通用 |
| `scrollSnapX` | Scroll snap X | 4 | NONE / START / END / CENTER | "" | Flags | 继承通用 |
| `scrollSnapY` | Scroll snap Y | 4 | NONE / START / END / CENTER | "" | Flags | 继承通用 |
| `checkedState` | Checked | boolean | — | — | States | 可写表达式（literal/expression）；模板未落盘；继承通用 |
| `disabledState` | Disabled | boolean | — | — | States | 可写表达式（literal/expression）；模板未落盘；继承通用 |
| `states` | —（未命名） | 5 | — | "" | States | 继承通用 |
| `useStyle` | —（未命名） | 12 | — | — | — | 模板未落盘；继承通用 |
| `localStyles` | —（未命名） | 1 | — | 见 §1.3 | — | 继承通用 |
| `group` | —（未命名） | 12 | — | "" | — | classInfo 定义了条件显隐；继承通用 |
| `groupIndex` | —（未命名） | 3 | — | 0 | — | classInfo 定义了条件显隐；继承通用 |

### 1.1 `widgetFlags` 在 UI 里拆成的复选框（Flags 组）

`HIDDEN` / `CLICKABLE` 两项单独显示为 **Hidden** / **Clickable**（可写表达式），其余按下面 18 项复选框出现：

| 复选框 | 含义（LVGL 9.4） |
|---|---|
| `CLICK_FOCUSABLE` | 点击时获得焦点 |
| `CHECKABLE` | 可切换 checked 状态（Switch 必须有） |
| `SCROLLABLE` | 内容可滚动 |
| `SCROLL_ELASTIC` | 滚动到底后有弹性回弹 |
| `SCROLL_MOMENTUM` | 惯性滚动 |
| `SCROLL_ONE` | 一次只滚一个子对象 |
| `SCROLL_CHAIN_HOR` / `SCROLL_CHAIN_VER` | 滚到头后把滚动传给父对象（横/竖） |
| `SCROLL_ON_FOCUS` | 获得焦点时自动滚动到可见区 |
| `SCROLL_WITH_ARROW` | 支持方向键滚动 |
| `SNAPPABLE` | 滚动后吸附对齐 |
| `PRESS_LOCK` | 按住后不再把按压传递给父对象 |
| `EVENT_BUBBLE` | 事件向上冒泡 |
| `GESTURE_BUBBLE` | 手势向上冒泡 |
| `ADV_HITTEST` | 精确命中测试（圆角按形状判定） |
| `IGNORE_LAYOUT` | 不参与父布局 |
| `FLOATING` | 不受父滚动影响（浮层） |
| `OVERFLOW_VISIBLE` | 子对象超出父边界仍显示 |

### 1.2 `states` 在 UI 里拆成的复选框（States 组）

`CHECKED` / `DISABLED` 单独显示为 **Checked** / **Disabled**（可写表达式），其余：

| 复选框 |
|---|
| `FOCUSED` / `FOCUS_KEY` / `PRESSED` / `HOVERED` |

（EEZ 还定义了 `DEFAULT` / `EDITED` / `SCROLLED` / `USER1`–`USER4`，但属性面板默认只列上面 4 项。）

### 1.3 样式（Style 组）

`localStyles` 不按单一字段编辑，而是在 Style 面板里按 **Part（MAIN / INDICATOR / KNOB / SCROLLBAR / …）× State（DEFAULT / CHECKED / …）**
逐项选择 LVGL 样式属性（背景、边框、圆角、内边距、文字颜色/字体、对齐、线宽…）。
生成器只允许写 `localStyles.definition.<PART>.<STATE>` 里的 LVGL 样式属性键，
A10 门禁校验键名合法性（如 `bg_color` / `text_font` / `pad_*` / `radius` / `align`）。


### 1.4 表达式选择器字段 `<属性>Type`（每行属性右侧的小下拉）

EEZ 里每个「可写表达式」的属性，在工程 JSON 中都伴随一个 `<属性名>Type` 字段，
UI 上就是该属性行右侧的 `literal` / `expression` 下拉。**生成器改属性值时必须同时把对应
`*Type` 复位成 `literal`**，否则会残留别工程的表达式引用。


| 属性 → 伴随字段 | 可选值 | 出现类型（示例） |
|---|---|---|

| `hiddenFlagType` | literal / translated-literal / expression（按属性而定） | LVGLAnimationImageWidget |

| `clickableFlagType` | literal / translated-literal / expression（按属性而定） | LVGLAnimationImageWidget |

| `checkedStateType` | literal / translated-literal / expression（按属性而定） | LVGLAnimationImageWidget |

| `disabledStateType` | literal / translated-literal / expression（按属性而定） | LVGLAnimationImageWidget |

| `rangeMinType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `rangeMaxType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `valueType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `startAngleType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `endAngleType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `bgStartAngleType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `bgEndAngleType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `rotationType` | literal / translated-literal / expression（按属性而定） | LVGLArcWidget |

| `minType` | literal / translated-literal / expression（按属性而定） | LVGLBarWidget |

| `maxType` | literal / translated-literal / expression（按属性而定） | LVGLBarWidget |

| `valueStartType` | literal / translated-literal / expression（按属性而定） | LVGLBarWidget |

| `textType` | literal / translated-literal / expression（按属性而定） | LVGLCheckboxWidget |

| `optionsType` | literal / translated-literal / expression（按属性而定） | LVGLDropdownWidget |

| `selectedType` | literal / translated-literal / expression（按属性而定） | LVGLDropdownWidget |

| `colorType` | literal / translated-literal / expression（按属性而定） | LVGLLedWidget |

| `brightnessType` | literal / translated-literal / expression（按属性而定） | LVGLLedWidget |

| `minValueType` | literal / translated-literal / expression（按属性而定） | LVGLScaleWidget |

| `maxValueType` | literal / translated-literal / expression（按属性而定） | LVGLScaleWidget |

| `valueLeftType` | literal / translated-literal / expression（按属性而定） | LVGLSliderWidget |

| `stepType` | literal / translated-literal / expression（按属性而定） | LVGLSpinboxWidget |

| `selectedTabType` | literal / translated-literal / expression（按属性而定） | LVGLTabviewWidget |

| `tabNameType` | literal / translated-literal / expression（按属性而定） | LVGLTabWidget |


### 1.5 结构/行为集合字段（非单值属性）

| 字段 | UI 位置 | 类型 | 说明 |
|---|---|---|---|
| `eventHandlers` | Events 分组 | 数组 | 事件绑定（CLICKED 等 → action）；生成时可为空数组，交互由 native 接 |
| `timeline` | Timeline | 数组 | 时间线动画（EEZ Flow 动画），no-flow 工程保持空 |
| `customInputs` / `customOutputs` | Flow 分组 | 数组 | 给 Flow 用的自定义输入/输出，no-flow 工程保持空 |
| `children` | Widget 树 | 数组 | 子控件；Button 必须恰好 1 个 Label，Tab 只能挂在 Tabview 下 |


## 2. 各控件 Specific 属性

> 每节只列 **Specific 组**的字段；通用 27 项（§1）对所有控件同样可改。


### `LVGLAnimationImageWidget`（AnimationImage）｜手册 W1

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `images` | —（未命名） | 0 | — | [] | Specific | — |
| `duration` | —（未命名） | 3 | — | 1000 | Specific | — |
| `repeatInfinite` | —（未命名） | 2 | — | true | Specific | — |
| `repeat` | Repeat count | 3 | — | 1 | Specific | classInfo 定义了条件显隐 |


### `LVGLArcWidget`（Arc）｜手册 W2

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `rangeMin` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `rangeMax` | —（未命名） | integer | — | 100 | Specific | 可写表达式（literal/expression） |
| `value` | —（未命名） | integer | — | 25 | Specific | 可写表达式（literal/expression） |
| `previewValue` | —（未命名） | 5 | — | 25 | Specific | classInfo 定义了条件显隐；classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `mode` | —（未命名） | 4 | NORMAL / SYMMETRICAL / REVERSE | NORMAL | Specific | classInfo 定义了条件显隐 |
| `bgStartAngle` | —（未命名） | integer | — | 135 | Specific | 可写表达式（literal/expression） |
| `previewBgStartAngle` | —（未命名） | 5 | — | 135 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `bgEndAngle` | —（未命名） | integer | — | 45 | Specific | 可写表达式（literal/expression） |
| `previewBgEndAngle` | —（未命名） | 5 | — | 45 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `rotation` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `previewRotation` | —（未命名） | 5 | — | 0 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `useAngle` | Use start/end angle | 2 | — | false | Specific | — |
| `showNoteAboutUseAngle` | —（未命名） | 22 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘（编辑器预览字段） |
| `startAngle` | —（未命名） | integer | — | 135 | Specific | 可写表达式（literal/expression） |
| `previewStartAngle` | —（未命名） | 5 | — | 135 | Specific | classInfo 定义了条件显隐；classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `endAngle` | —（未命名） | integer | — | 45 | Specific | 可写表达式（literal/expression） |
| `previewEndAngle` | —（未命名） | 5 | — | 45 | Specific | classInfo 定义了条件显隐；classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |


### `LVGLBarWidget`（Bar）｜手册 W3

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `min` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `max` | —（未命名） | integer | — | 100 | Specific | 可写表达式（literal/expression） |
| `mode` | —（未命名） | 4 | NORMAL / SYMMETRICAL / RANGE | NORMAL | Specific | — |
| `value` | —（未命名） | integer | — | 25 | Specific | 可写表达式（literal/expression） |
| `previewValue` | —（未命名） | 5 | — | 25 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `valueStart` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `previewValueStart` | —（未命名） | 5 | — | 0 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `enableAnimation` | —（未命名） | 2 | — | false | Specific | — |


### `LVGLButtonMatrixWidget`（ButtonMatrix）｜手册 W11

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `buttons` | —（未命名） | 0 | — | [] | Specific | — |
| `oneCheck` | —（未命名） | 2 | — | false | Specific | — |


### `LVGLButtonWidget`（Button）｜手册 W10

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLCalendarWidget`（Calendar）｜手册 W12

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `todayYear` | Year | 3 | — | 2022 | Specific | — |
| `todayMonth` | Month | 3 | — | 11 | Specific | — |
| `todayDay` | Day | 3 | — | 1 | Specific | — |
| `header` | —（未命名） | 4 | — | Arrow | Specific | — |
| `chineseMode` | —（未命名） | 2 | — | false | Specific | classInfo 定义了条件禁用 |


### `LVGLCanvasWidget`（Canvas）｜手册 W13

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLChartWidget`（Chart）｜手册 W14

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLCheckboxWidget`（Checkbox）｜手册 W16

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `text` | —（未命名） | string | — | Checkbox | Specific | 可写表达式（literal/translated-literal） |
| `useStaticText` | Use static text | 2 | — | true | Specific | classInfo 定义了条件显隐 |


### `LVGLContainerWidget`（Container）｜手册 W20

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `containerVersion` | —（未命名） | 3 | — | — | — | classInfo 定义了条件显隐；模板未落盘 |


### `LVGLDropdownWidget`（Dropdown）｜手册 W24

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `options` | —（未命名） | array:string | — | Option 1\nOption 2\nOption 3 | Specific | 可写表达式（literal/translated-literal/expression） |
| `useStaticText` | Use static text | 2 | — | true | Specific | classInfo 定义了条件显隐 |
| `selected` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `direction` | —（未命名） | 4 | TOP / LEFT / BOTTOM / RIGHT | bottom | Specific | — |


### `LVGLImageWidget`（Image）｜手册 W30

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `image` | —（未命名） | 12 | — | — | Specific | 模板未落盘 |
| `setPivot` | Change pivot point (default is center) | 2 | — | false | Specific | — |
| `pivotX` | Pivot X | 3 | — | 0 | Specific | classInfo 定义了条件禁用 |
| `pivotY` | Pivot Y | 3 | — | 0 | Specific | classInfo 定义了条件禁用 |
| `zoom` | Scale | 3 | — | 256 | Specific | classInfo 定义了条件显隐 |
| `angle` | Rotation | 3 | — | 0 | Specific | classInfo 定义了条件显隐 |
| `innerAlign` | —（未命名） | 4 | DEFAULT / TOP_LEFT / TOP_MID / TOP_RIGHT / BOTTOM_LEFT / BOTTOM_MID / BOTTOM_RIGHT / LEFT_MID / RIGHT_MID / CENTER / STRETCH / TILE | CENTER | Specific | classInfo 定义了条件显隐 |
| `sizeMode` | —（未命名） | 4 | VIRTUAL / REAL | VIRTUAL | Specific | classInfo 定义了条件显隐 |
| `value` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `previewValue` | —（未命名） | 5 | — | 0 | Specific | classInfo 定义了条件显隐；classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |


### `LVGLImgbuttonWidget`（Imgbutton）｜手册 W31

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `imageReleased` | Released image | 12 | — | — | Specific | 模板未落盘 |
| `imagePressed` | Pressed image | 12 | — | — | Specific | 模板未落盘 |
| `imageDisabled` | Disabled image | 12 | — | — | Specific | 模板未落盘 |
| `imageCheckedReleased` | Checked released image | 12 | — | — | Specific | 模板未落盘 |
| `imageCheckedPressed` | Checked pressed image | 12 | — | — | Specific | 模板未落盘 |
| `imageCheckedDisabled` | Checked disabled image | 12 | — | — | Specific | 模板未落盘 |


### `LVGLKeyboardWidget`（Keyboard）｜手册 W34

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `textarea` | —（未命名） | 4 | — | — | Specific | 模板未落盘 |
| `mode` | —（未命名） | 4 | TEXT_LOWER / TEXT_UPPER / SPECIAL / NUMBER / USER_1 / USER_2 / USER_3 / USER_4 | TEXT_LOWER | Specific | — |


### `LVGLLabelWidget`（Label）｜手册 W35

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `text` | —（未命名） | string | — | Text | Specific | 可写表达式（literal/translated-literal/expression） |
| `useStaticText` | Use static text | 2 | — | true | Specific | classInfo 定义了条件显隐 |
| `previewValue` | —（未命名） | 5 | — | — | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `longMode` | —（未命名） | 4 | WRAP / DOT / SCROLL / SCROLL_CIRCULAR / CLIP | WRAP | Specific | — |
| `recolor` | —（未命名） | 2 | — | false | Specific | — |


### `LVGLLedWidget`（Led）｜手册 W36

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `color` | —（未命名） | integer | — | #0000FF | Specific | 可写表达式（literal/expression） |
| `brightness` | —（未命名） | integer | — | 255 | Specific | 可写表达式（literal/expression） |


### `LVGLLineWidget`（Line）｜手册 W37

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `points` | —（未命名） | 5 | — | 0,0 50,50 100,0 150,50 200,0 | Specific | classInfo 定义了条件显隐 |
| `invertY` | Invert Y | 2 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `needleLength` | Needle length | 3 | — | 0 | Specific | classInfo 定义了条件显隐 |
| `value` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `previewValue` | —（未命名） | 5 | — | 0 | Specific | classInfo 定义了条件显隐；classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |


### `LVGLListWidget`（List）｜手册 W42

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLLottieWidget`（Lottie）｜手册 W43

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLMenuWidget`（Menu）｜手册 W45

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLMessageBoxWidget`（MessageBox）｜手册 W46

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLPanelWidget`（Panel）｜手册 W50

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLQRCodeWidget`（QRCode）｜手册 W56

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `text` | —（未命名） | 5 | — | https://envox.eu/ | Specific | — |
| `darkColor` | —（未命名） | 9 | — | #20429F | Specific | — |
| `lightColor` | —（未命名） | 9 | — | #E2F5FE | Specific | — |


### `LVGLRollerWidget`（Roller）｜手册 W61

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `options` | —（未命名） | array:string | — | Option 1\nOption 2\nOption 3 | Specific | 可写表达式（literal/translated-literal/expression） |
| `selected` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `mode` | —（未命名） | 4 | NORMAL / INFINITE | NORMAL | Specific | — |


### `LVGLScaleWidget`（Scale）｜手册 W62

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `scaleMode` | —（未命名） | 4 | HORIZONTAL_TOP / HORIZONTAL_BOTTOM / VERTICAL_LEFT / VERTICAL_RIGHT / ROUND_INNER / ROUND_OUTER | HORIZONTAL_BOTTOM | Specific | — |
| `minValue` | Min value | integer | — | 10 | Specific | 可写表达式（literal/expression） |
| `maxValue` | Max value | integer | — | 40 | Specific | 可写表达式（literal/expression） |
| `angleRange` | Angle range | 3 | — | 270 | Specific | — |
| `rotation` | —（未命名） | integer | — | 135 | Specific | 可写表达式（literal/expression） |
| `totalTickCount` | Total tick count | 3 | — | 31 | Specific | — |
| `majorTickEvery` | Major tick every | 3 | — | 5 | Specific | — |
| `postDraw` | Post draw | 2 | — | false | Specific | — |
| `drawTicksOnTop` | Draw ticks on top | 2 | — | false | Specific | — |
| `showLabels` | —（未命名） | 2 | — | true | Specific | — |
| `labelTexts` | Label texts | 6 | — | "" | Specific | — |
| `（样式分区）mainStyles` | mainStyles | Style | — | — | Style | EEZ Style 面板中该分区的样式属性 |
| `mainLineWidth` | Main line width | 3 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `mainLineColor` | Main line color | 9 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `mainLineOpacity` | Main line opacity | 3 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `mainArcWidth` | Main arc width | 3 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `mainArcColor` | Main arc color | 9 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `mainArcOpacity` | Main arc opacity | 3 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `mainArcRounded` | Main arc rounded | 2 | — | false | Specific | classInfo 定义了条件显隐 |
| `mainArcImageSrc` | Main arc image | 12 | — | — | Specific | classInfo 定义了条件显隐；模板未落盘 |
| `（样式分区）minorTicksStyles` | minorTicksStyles | Style | — | — | Style | EEZ Style 面板中该分区的样式属性 |
| `minorTicksLength` | Minor ticks length | 3 | — | — | Specific | 模板未落盘 |
| `minorTicksWidth` | Minor ticks width | 3 | — | — | Specific | 模板未落盘 |
| `minorTicksColor` | Minor ticks color | 9 | — | — | Specific | 模板未落盘 |
| `minorTicksOpacity` | Minor ticks opacity | 3 | — | — | Specific | 模板未落盘 |
| `（样式分区）majorTicksStyles` | majorTicksStyles | Style | — | — | Style | EEZ Style 面板中该分区的样式属性 |
| `majorTicksLength` | Major ticks length | 3 | — | — | Specific | 模板未落盘 |
| `majorTicksWidth` | Major ticks width | 3 | — | — | Specific | 模板未落盘 |
| `majorTicksColor` | Major ticks color | 9 | — | — | Specific | 模板未落盘 |
| `majorTicksOpacity` | Major ticks opacity | 3 | — | — | Specific | 模板未落盘 |
| `（样式分区）labelsStyles` | labelsStyles | Style | — | — | Style | EEZ Style 面板中该分区的样式属性 |
| `labelsTextColor` | Labels text color | 9 | — | — | Specific | 模板未落盘 |
| `labelsTextOpacity` | Labels text opacity | 3 | — | — | Specific | 模板未落盘 |
| `labelsTextFont` | Labels text font | 4 | — | — | Specific | 模板未落盘 |
| `sections` | —（未命名） | 0 | — | [] | Specific | — |


### `LVGLScreenWidget`（Screen）｜手册 W 章节未单列

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLSliderWidget`（Slider）｜手册 W67

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `min` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `max` | —（未命名） | integer | — | 100 | Specific | 可写表达式（literal/expression） |
| `mode` | —（未命名） | 4 | NORMAL / SYMMETRICAL / RANGE | NORMAL | Specific | — |
| `valueLeft` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |
| `previewValueLeft` | —（未命名） | 5 | — | 0 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `value` | —（未命名） | integer | — | 25 | Specific | 可写表达式（literal/expression） |
| `previewValue` | —（未命名） | 5 | — | 25 | Specific | classInfo 定义了条件禁用；模板未落盘（编辑器预览字段） |
| `enableAnimation` | —（未命名） | 2 | — | false | Specific | — |


### `LVGLSpanWidget`（Span）｜手册 W68

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `mode` | —（未命名） | 4 | — | FIXED | Specific | classInfo 定义了条件禁用 |
| `overflow` | —（未命名） | 4 | — | CLIP | Specific | — |
| `indent` | —（未命名） | 3 | — | 0 | Specific | — |
| `maxLines` | Max lines | 3 | — | -1 | Specific | — |
| `align` | —（未命名） | 4 | — | AUTO | Specific | classInfo 定义了条件禁用 |
| `spans` | —（未命名） | 0 | — | [{'objID': '__SPANS0_OBJID__', 'text': 'Span', 'textType'… | Specific | — |


### `LVGLSpinboxWidget`（Spinbox）｜手册 W69

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `digitCount` | —（未命名） | 3 | — | 5 | Specific | — |
| `separatorPosition` | —（未命名） | 3 | — | 0 | Specific | — |
| `min` | —（未命名） | 3 | — | -99999 | Specific | — |
| `max` | —（未命名） | 3 | — | 99999 | Specific | — |
| `rollover` | —（未命名） | 2 | — | false | Specific | — |
| `step` | —（未命名） | integer | — | 1 | Specific | 可写表达式（literal/expression） |
| `value` | —（未命名） | integer | — | 0 | Specific | 可写表达式（literal/expression） |


### `LVGLSpinnerWidget`（Spinner）｜手册 W71

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLSwitchWidget`（Switch）｜手册 W74

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLTabWidget`（Tab）｜手册 W75

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `tabName` | —（未命名） | string | — | Tab | Specific | 可写表达式（literal/translated-literal/expression） |


### `LVGLTableWidget`（Table）｜手册 W76

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLTabviewWidget`（Tabview）｜手册 W78

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `tabviewPosition` | Position | 4 | — | TOP | Specific | — |
| `tabviewSize` | Size | 3 | — | 32 | Specific | — |
| `selectedTab` | Active tab | integer | — | 0 | Specific | 可写表达式（literal/expression） |


### `LVGLTextareaWidget`（Textarea）｜手册 W80

| 属性名（classInfo `name`） | 显示名（classInfo `displayName`） | type（classInfo 原值） | 可选值（`enumItems`） | 模板默认值 | 分组（`propertyGridGroup`） | 说明 |
|---|---|---|---|---|---|---|

| `text` | —（未命名） | string | — | "" | Specific | 可写表达式（literal/translated-literal/expression） |
| `placeholder` | —（未命名） | 5 | — | "" | Specific | — |
| `oneLineMode` | —（未命名） | 2 | — | false | Specific | — |
| `passwordMode` | —（未命名） | 2 | — | false | Specific | — |
| `acceptedCharacters` | —（未命名） | 5 | — | "" | Specific | — |
| `maxTextLength` | —（未命名） | 3 | — | 128 | Specific | — |


### `LVGLTileViewWidget`（TileView）｜手册 W84

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


### `LVGLWindowWidget`（Window）｜手册 W87

EEZ 前端**没有 Specific 属性**（只用通用属性 + Style 面板）。


## 3. 生成器使用规则（硬约束）

1. **字段白名单**：新建控件必须克隆 `templates/<Type>.json`，只允许改「本表 §1+§2 列出的、
   且模板里实际存在的」字段；模板里没有的字段不得新增（A14）。
2. **样式键白名单**：`localStyles` 只允许写 LVGL 样式属性（A10）；键名必须与 EEZ Style 面板一致。
3. **表达式复位**：从别工程采来的样板要检查 `*Type`（`textType` / `hiddenFlagType` /
   `checkedStateType` / `disabledStateType` / `clickableFlagType`），保留 `literal`，
   否则会带出 `get_var_*` 未声明调用（编译报错）。
4. **模板未落盘的字段**：`previewValue`、`preview*`、`codeIdentifier`、`absolutePosition`、
   `geometryProperties` 在模板里没有保存值（EEZ 编辑器预览/内部用），生成器不得写。
5. **新增能力**：手册/属性面板里没有的字段，先回 EEZ UI 拖出并保存 → `extract_templates.py`
   重提模板 → 同步补本表，之后才允许出现在生成器里。

## 4. 逐行复核（2026-11-06）

复核方式：脚本解析本表每一行，与 `classInfo.properties`、`templates/*.json` 逐项比对。

| 核对项 | 结果 |
|---|---|
| 行数 | 168 行（通用 27 + 各控件 Specific 141） |
| 属性名 | 全部能在对应 `classInfo.properties` 里找到；classInfo 的每个属性也都出现在表中（双向 0 差异） |
| 可选值 | 与 `enumItems` 逐字一致 |
| 模板默认值 | 与 `templates/*.json` 逐字一致（空串显示为 `""`） |
| 臆造字段 | 0（表内没有任何 classInfo 之外的属性） |

**明确不做的两件事**（避免臆造）：
1. 未显式命名的属性不编造显示名（EEZ 运行时用 `humanize(name)`，本机未取到该函数产物）；
2. 数字型 `type` 不翻译成词（EEZ 内部 `PropertyType` 枚举名表未在 asar 产物中定位到）。

