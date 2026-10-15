# 07 · .eez-project 工程 JSON 序列化语法速查（实测对照版）

> **定位**：官方手册（本目录 01–06）讲的是 Studio 的**概念与操作**，从不写
> `.eez-project` 文件的 **JSON 落盘格式**。本文补的就是这块：AI/脚本生成或
> 修改工程 JSON 时的**字段级速查**，避免「字段名猜错→静默失败/构建报错」。
>
> **来源与验证等级**（每条标注）：
> - ✅ **实测**：本工程（eez-test，Studio 0.29 + LVGL 9.4）构建通过且运行验证；
> - 📖 **手册**：Reference Guide 对应页码；
> - 🔍 **asar**：Studio 安装包 `resources/app.asar` 反编译取证（codegen 降级逻辑等）。
>
> 更新纪律：本文只收「已在真实工程里跑通」的写法；新验证一条加一条，不要凭印象预填。

---

## 1. 文件顶层结构 ✅

```json
{
  "themesVersion": …, "objID": "<uuid>",
  "settings":  { "general": {…}, "build": {…} },
  "variables": { "objID": "…", "globalVariables": [ … ] },
  "actions":   [ … ],              // User Actions 面板（数组！不是 dict）
  "userPages":  [ … ],             // 页面（本工程单页架构只有 Main 一个）
  "userWidgets": [ … ],            // 自定义部件
  "lvglStyles": [ … ], "lvglGroups": …, "fonts": [ … ],
  "bitmaps": […], "colors": …, "themes": …
}
```

- 所有节点的身份键是 **`objID`**（uuid 字符串）。自己生成时保持全局唯一即可
  （可用确定性 oid 哈希，见 json2eez `oid()`）；引用其它资源**不用 objID 的场景
  见 §7/§8（控件用 identifier 字符串、User Action 用名字字符串）**。

## 2. settings.general 关键字段 ✅

| 字段 | 本工程取值 | 说明 |
|---|---|---|
| `projectType` | `"lvgl"` | 另有 `eez-gui` / `dashboard` |
| `lvglVersion` | `"9.4.0"` | 决定 codegen 模板 |
| `flowSupport` | `true` | **开 flow 的总开关**（事件 handler/组件都依赖它） |
| `displayWidth/Height` | 800 / 480 | 画布逻辑尺寸 |
| `colorBpp` / `bitmapColorFormat` | `"16"` / `"BGR"` | 与屏幕面板匹配 |
| `embedFonts` / `embedBitmaps` | `true` | 字体/位图内嵌 |
| `cacheFonts` | `true` | ★ false 时 headless CLI 不烘焙字体（P-00xx 实证根因） |
| `darkTheme` | `true` | EEZ 原生深色主题（codegen 发 lv_theme_default_init(…, true, …)） |

`settings.build`：`configurations[]`、`files[]`（screens.c/ui.c 等代码模板）、
`useDockerDesktop`（F7 全仿真器开关）、`lvglInclude`（生成代码的 lvgl 头路径）。

## 3. 全局变量 variables.globalVariables ✅

```json
{ "objID": "…", "name": "wifi_state", "type": "integer",
  "defaultValue": "0", "persistent": false, "native": true }
```

- `type` 稳定可用的只有 **`"integer"` / `"string"`**；⚠ **布尔用 integer 0/1**
  （EEZ 对 bool 的 native get/set 签名不稳定）。
- **样式状态键透传**：DSL style 的 `MAIN` 下除 DEFAULT/CHECKED 外，`PRESSED` /
  `FOCUSED` / `DISABLED` 等均可直接用（EEZ LVGL_STATE_CODES 支持）；带状态覆盖的
  样式 EEZ 生成时**内联在 screens.c 对象创建处**（`lv_obj_set_style_*` 带
  `LV_STATE_*` 参数），**不在 styles.c** ——查生成代码别找错文件（实测 2026-10-01）。
  瞬时命令按钮（prev/next 类）无 CHECKED，必须有 PRESSED 否则点击零反馈。
- **flow 链中段向 native 发命令的唯一桥**：SetVariable 落在 native 输出变量上
  → 生成 `set_var_<name>(value)` → 用户侧转发 app_set_output。命名用 `_cmd`
  后缀表明是脉冲命令，get 不绑定（无回显误导）。
- `defaultValue` 是**字符串化的 JSON**：int 写 `"0"`，string 写 `"\"--:--\""`
  （内层引号要转义）。
- `native: true` → EEZ 生成 `vars.h` 里 `get_var_<name>/set_var_<name>` 声明，
  实现放用户侧 `native_vars.cpp`（C 函数名由变量名自动推导，无配置字段）。

## 4. User Actions（actions 顶层数组）✅

```json
{ "name": "voice_stop", "implementationType": "native",
  "description": "…", "userProperties": [] }
```

- 控件事件绑定（见 §7 eventHandlers）里 `"handlerType": "action"` 时，
  **`"action"` 字段存的是这里的 `name` 字符串**（⚠ 不是 objID —— 存 objID 会
  查找失败、生成空 CLICKED 分支且零报错）。
- 固件侧实现 `extern "C" void action_<name>(lv_event_t *e)`，三件套生成：
  actions.h / ui.c 动作表 / screens.c 回调直调。

## 5. 页面 userPages[i] 结构 ✅

```json
{ "objID": "…", "name": "Main",
  "components": [ <screen 控件树根, 以及全部 flow 组件> ],
  "connectionLines": [ … ],
  "localVariables": [ { "name": "np_playing", "type": "integer", "defaultValue": "0" } ],
  "componentGroups": [ { "description": "组名", "components": ["<objID>", …] } ],
  "userProperties": [], "left": 0, "top": 0, "width": 800, "height": 480,
  "isUsedAsUserWidget": false, "createAtStart": true, "deleteOnScreenUnload": false }
```

- **`components` 混装两类**：① screen 控件树根（type=LVGL*Widget）；② flow
  动作组件（type=*ActionComponent，浮动在画布上，left/top 只是编辑器摆位）。
- `localVariables` 无 objID 也能构建通过（Studio 不强制）。
- `componentGroups`：`components` 存组件 objID 数组；组矩形是 computed 不落盘。

## 6. 控件（LVGL*Widget）通用骨架 ✅

```json
{ "objID": "…", "type": "LVGLContainerWidget",
  "identifier": "m_np_disc",                 // ← 代码里的 objects.<identifier>
  "left": 0, "top": 0, "width": 92, "height": 92,
  "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
  "style": { "objID": "…", "useStyle": "default", "conditionalStyles": [], "childStyles": [] },
  "localStyles": { "objID": "…", "definition": { "MAIN": { "DEFAULT": { … } } } },
  "timeline": [], "eventHandlers": [], "children": [],
  "widgetFlags": "CLICK_FOCUSABLE|GESTURE_BUBBLE|…",   // 去 CLICKABLE/SCROLLABLE 直接删词
  "hiddenFlagType": "literal" | "expression",
  "hiddenFlag": true | "<表达式>",
  "clickableFlagType": "literal", "clickableFlag": false,
  "checkedStateType": "literal", "checkedState": true,
  "group": "", "groupIndex": 0 }
```

- **identifier 命名规则**：全工程唯一，`^[A-Za-z][A-Za-z0-9_]*$`；无 identifier 的
  codegen 一律 `objN`（无法沟通）。⚠ widget 的名字字段叫 **`identifier`**（不是 name）。
- **坐标相对父对象**（Studio 保存时会把绝对坐标换算掉）；`*Unit: "content"` 用于
  label 自适应尺寸。
- **hidden 三形态**：`hiddenFlagType:"literal"` + `hiddenFlag:true`；表达式绑定用
  `"hiddenFlagType":"expression"` + `hiddenFlag:"<表达式>"`（codegen 在
  tick_screen 里逐帧 evalBooleanProperty 并 diff HIDDEN flag）。
- label 绑变量：`"text": "<变量名>", "textType": "expression", "useStaticText": false`
  （裸变量名，**不加 @**）；⚠ 绑变量后静态字形收集失效，须 `"glyphs": "…"` 补种。
- tabview：`"tabs": [ … ]` 子项为 LVGLTabWidget（tabName 可写 FA 图标字符，
  字形须烘进对应字号）；`"tabSize": 0` 隐藏原生 tab 栏。

## 7. 事件绑定 eventHandlers ✅（三形态互斥，一个事件一种）

```json
"eventHandlers": [
  { "objID": "…", "eventName": "CLICKED", "handlerType": "flow",    "userData": 0 },
  { "objID": "…", "eventName": "VALUE_CHANGED", "handlerType": "flow", "userData": 0 },
  { "objID": "…", "eventName": "CLICKED", "handlerType": "action", "action": "voice_stop", "userData": 0 }
]
```

- `eventName` 常用：`CLICKED` / `VALUE_CHANGED`（tabview 滑动收尾）/ `PRESSED`。
- `handlerType:"flow"`：控件 objID 作为连线 source、**output 名 = eventName 字符串**
  （见 §9）；`"action"`：直调 User Action，不经 flow。

## 8. flow 组件序列化大全 ✅（逐个实测；输入输出端口名见 §9）

所有组件公共字段：`objID / type / left / top / width / height / customInputs: [] / customOutputs: []`。

### 8.1 LVGLActionComponent —— actions 数组顺序执行

```json
{ "type": "LVGLActionComponent",
  "actions": [
    { "objID": "…", "action": "tabviewSetActiveTab", "object": "m_ai_nav",
      "objectType": "literal", "tab": 3, "tabType": "literal",
      "animated": false, "animatedType": "literal" },
    { "objID": "…", "action": "objClearState", "object": "m_nav_chat",
      "objectType": "literal", "state": "CHECKED", "stateType": "literal" },
    { "objID": "…", "action": "tabviewGetActiveTab", "object": "m_main_nav",
      "objectType": "literal", "result": "main_page_idx" }
  ] }
```

- ⚠ `object` 存控件 **identifier 字符串**；assignable 参数（如 `result`）是
  **裸表达式字符串、没有 `xxxType` 后缀字段**（有 Type 后缀的都是 literal 参数）。
- **`animated` 必须 false**：程序切 tab/设值用动画会有竞态（铁律：程序切 tab
  一律 LV_ANIM_OFF）。
- 实测可用 action 名（codegen → 运行时 PropertyCode/调用）：
  `changeScreen` / `objAddState` / `objClearState` / `objAddFlag`(`flag:"HIDDEN"`) /
  `objClearFlag` / `tabviewSetActiveTab` / `tabviewGetActiveTab` / `objSetX` /
  `objSetY` / `objSetWidth` / `objSetHeight` / `objSetStyleOpa` / `imageSetAngle` /
  `imageSetZoom` / `labelSetText` / `arcSetValue` / `barSetValue` / `sliderSetValue`。

### 8.2 SET_PROPERTY（高层形式，codegen 降级）✅🔍

```json
{ "action": "SET_PROPERTY", "targetType": "basic", "target": "m_np_orbit_1",
  "property": "width", "animated": false,
  "value": "96 + kg * 2", "valueType": "expression" }
```

- **降级映射**（asar 实证，codegen 在构建期改写成 8.1 的具体动作）：

| targetType | property | 降级为 |
|---|---|---|
| basic | x / y / width / height / opacity / hidden / checked / disabled | objSetX / objSetY / objSetWidth / objSetHeight / objSetStyleOpa / objSetFlagHidden / objSetStateChecked / objSetStateDisabled |
| image | image / angle / zoom | imageSetSrc / imageSetAngle / imageSetZoom |
| label | （property 留空） | labelSetText |
| arc / bar / roller / slider | — | 各自 SetValue |

- `valueType: "literal"` 时 value 直接是字面量（复位动作用）。

### 8.3 SetVariableActionComponent ✅

```json
{ "type": "SetVariableActionComponent",
  "entries": [ { "objID": "…", "variable": "np_playing", "value": "1 - np_playing" } ] }
```

- 对 **native 全局变量**：codegen 直接生成 `set_var_<name>(<value>)`（进输出命令队列）；
  对**页面局部变量**：写 flowState（纯 UI 态）。

### 8.4 LoopActionComponent ✅

```json
{ "type": "LoopActionComponent", "variable": "kg",
  "from": "0", "to": "27", "step": "1", "version": 1 }
```

- from/to/step 都是**表达式字符串**；`step` 可为负（27→0 递减，闭区间 28 次执行）。
- 输入输出端口（见 §9）：body 走 `@seqout`，迭代推进连回 **`"next"`**，启动连
  **`"start"`**，结束发 **`"done"`**。
- ⚠ **无限循环 = done 自连 start**（官方 demo 同款），或外层 to 给大数。

### 8.5 DelayActionComponent ✅

```json
{ "type": "DelayActionComponent", "milliseconds": "30" }
```

- 异步挂起（重入队列），是 flow 动画的帧节拍器；毫秒为表达式字符串。

### 8.6 IsTrueActionComponent ✅

```json
{ "type": "IsTrueActionComponent", "value": "np_playing" }
```

- 输出 `True` / `False` 两条序列线（连线 output 名就叫这个）。
- ⚠ **可停动画的停止检查必须放帧级**（放外层循环要等一整圈才生效）。

### 8.7 CompareActionComponent ✅

```json
{ "type": "CompareActionComponent", "A": "set_page_idx", "B": "0", "operator": "=" }
```

- A/B/C 是裸表达式；operator 枚举 `"="`；输出 `True`/`False`（同 IsTrue）。

### 8.8 CommentActionComponent ✅（画布注释，不参与执行）

```json
{ "type": "CommentActionComponent", "identifier": "m_title_np0",
  "description": "唱片律动链", "text": "…", "collapsed": true, "expandedWidth": 340 }
```

- ⚠ 需要 **identifier**（check_identifiers 对无名字组件报错）。

### 8.9 StartActionComponent ✅（页面加载即触发，`{}` 即可，官方 demo 用它做自启动动画）

## 9. connectionLines 连线语义 ✅

```json
{ "objID": "…", "source": "<source objID>", "output": "@seqout",
  "target": "<target objID>", "input": "@seqin" }
```

| 端口 | 含义 |
|---|---|
| `@seqin` / `@seqout` | 标准顺序入/出（动作组件都有） |
| `"CLICKED"` / `"VALUE_CHANGED"` / `"PRESSED"` | **控件事件输出**（source=控件 objID，output=eventName） |
| `True` / `False` | IsTrue / Compare 的分支序列输出 |
| `start` / `next` / `done` | **Loop 专用**（没有 @seqin！）；`done→start` 自环=无限循环 |

- @seqout 可**扇出多条**连线（顺序触发多条子链）。

## 10. 表达式引擎能力与陷阱 ✅

- 支持：四则 `+ - * / %`、比较 `== != < > <= >=`（也可 `=`）、`&& || !`、
  **三目 `?:`**、位运算、`MATH_SIN/COS/ABS/FLOOR/CEIL/ROUND/MIN/MAX…`、
  `SYSTEM_GET_TICK`、字符串/数组/JSON 系列列（手册 P8.4）。
- ⚠ **陷阱 1：`/` 与 `%` 永远返回 double**（eez-flow.cpp 实证）——结果塞给
  objSetY 等整数动作会变成位型垃圾坐标（实测 disc_y=0x66666666）。
  **帧表达式必须纯整数**；小数步进用多段三目或调整步长规避。
- ⚠ **陷阱 2**：表达式里的裸名解析顺序：页面局部变量 → 全局变量；两处都不存在
  时构建期**不报错、运行期抛错**，务必核对 variables[]/localVariables 声明。

## 11. 动画能力矩阵与边界 ✅📖

| 途径 | 循环 | 可停 | 预览可见 | F7 全仿真器 | 真机 |
|---|---|---|---|---|---|
| LVGL action `PLAY_ANIMATION`（Anim Y/Width/Height/Opacity/ImageZoom/ImageAngle） | ✗ 一次性 | ✗ 无停止动作 | 静态画布 ✗ | ✓ | ✓ |
| **Loop+Delay+SET_PROPERTY flow 循环链**（官方 eez_lvgl_demo 同款） | ✓ | ✓（帧级 IsTrue） | **✓ Run 模式真实执行** | ✓ | ✓ |
| Animation timeline（页 timeline + A2 Animate） | Dashboard 专用，LVGL codegen 不消费 | — | — | — | — |

- 手册 A43（P.215–221）：LVGL 动作清单里 Anim\* 全部只有 Start/End/Delay/Time/
  Relative/Instant/Path——**没有 repeat，没有停止动作**。
- **Run 模式预览会执行 flow 并实时刷新画布**（Start/Loop/Delay/SetVariable/
  IsTrue/LVGL action）；但不模拟真实 LVGL 交互事件（滑动 SCROLL_END/
  VALUE_CHANGED 链在预览不发生）、native 变量不反映。
- F7 全仿真器：Docker+Emscripten 编真 LVGL 成 WASM；**只拷 uiDir（生成代码目录），
  不含 src/native 用户代码**。

## 12. 常见静默失败清单（写 JSON 前先过一遍）

1. eventHandler 的 `action` 写成 objID → 空 CLICKED 分支、零报错。
2. `object`/`target` 写了 assign_ids 重写**前**的旧名 → `Widget index not found`。
3. 样式值语法错（如 bg_color 漏 `0x`）→ **静默吞掉不报错**（cases/B6）。
4. `/`、`%` 进整数动作 → 位型垃圾坐标（§10 陷阱 1）。
5. 绑变量忘了 `glyphs` 补种 → 运行时字符变豆腐块（当时易误判缺字形）。
6. `cacheFonts:false` → headless 构建静默 0 字体产出。
7. 子控件超出父边界 → 被 LVGL 裁掉，画布上看起来「画了但没显示」。
8. tab 直接挂 screen（非 tabview 子对象）→ headless 能编过、GUI 报
   Invalid position of Tab widget（headless 过 ≠ 结构合法）。
9. 无 identifier 的 flow 组件没进 check_identifiers 白名单 → 生成期 FAIL
   （自己管线里的检查，非 EEZ 报错）。
10. bitmaps 条目缺 `bpp` → 该位图生成 TypeError（.c 不产出），其余文件照常
    构建成功，容易漏看（§12.5）。
11. 图片控件 `image` 名与 bitmaps[].name 不一致 → 不报错、运行时图片空白
    （构建期不校验引用，§12.5）。
12. **LVGLListWidget 不生成 objects 表条目**（lv_list_create 有、objects.X 无；
    hiddenExpr 标记也无效）→ native 侧运行时用
    `lv_obj_check_type(obj, &lv_list_class)` 递归查找（实测 2026-10-01）。
13. **native 运行时灌入的文本没有字形**（字形只按静态文本收集）→
    lv_list_add_btn 的中文变豆腐块。解法：DSL `glyphs_seed = {字体名: "字符串"}`
    预烘字形（json2eez 汇入 TEXT_BY_FONT）。

## 12.5 位图与图片控件（LVGLImageWidget）✅（2026-10-01 唱片转动实测）

**project.bitmaps 条目**（官方 eez_lvgl_demo 实证）：

```json
{ "objID": "…", "name": "np_disc",
  "image": "data:image/png;base64,…",   // PNG 以 data URL 内嵌
  "bpp": 16, "alwaysBuild": false }
```

- ⚠ **`bpp` 必填**——缺了 EEZ 位图生成器直接报
  `TypeError: Cannot read properties of undefined (reading 'toString')`，
  且该位图的 .c 不产出（其余文件照常构建，容易漏看）。
- EEZ CLI build 据此重写 `src/ui/images.c`（PNG→LVGL C 数组，RGBA 带 alpha）。

**图片控件**（TYPE_MAP `"image"` → `LVGLImageWidget`）：

```json
{ "type": "LVGLImageWidget", "identifier": "m_np_disc",
  "image": "np_disc",          // ← 位图 name（⚠ 必须与 bitmaps[].name 一致，
                               //   写错不报错、运行时图片空白）
  "pivotX": 46, "pivotY": 46,  // 旋转轴（绕中心转 = 宽高一半）
  "zoom": 256, "angle": 0 }
```

- 只有 image 能转：旋转走 `SET_PROPERTY targetType:"image" property:"angle"`
  （0.1° 单位，一圈 3600；`lv_img_set_angle` 收 int16，别超 32767）。

## 12.6 键盘与密码输入（LVGLKeyboardWidget / LVGLTextareaWidget）✅（2026-10-01 密码面板实测）

```json
// TYPE_MAP 需加映射："textarea" -> LVGLTextareaWidget，"keyboard" -> LVGLKeyboardWidget
// FLAGS：两者都要 CLICKABLE（textarea 可点聚焦、keyboard 收按键）
{ "type": "LVGLTextareaWidget", "identifier": "m_net_pwd_ta",
  "text": "", "textType": "literal", "useStaticText": true,
  "oneLineMode": true, "passwordMode": true, "maxTextLength": 64 }
{ "type": "LVGLKeyboardWidget", "identifier": "m_net_pwd_kb",
  "textarea": "<textarea 的 identifier 名>",   // ★ 不是 objID（P-0053 修正）
  "mode": "TEXT_LOWER" }                        // ⚠ 必填！缺省 codegen 生成
                                                //   LV_KEYBOARD_MODE_undefined（编译错）。
                                                //   合法值 TEXT_LOWER/TEXT_UPPER/SPECIAL/NUMBER/USER_1..4
```

- **控件引用解析（★ P-0053 修正）**：keyboard 的 textarea 是 **identifier 名**，
  **不是 objID**（asar Keyboard.js：enumItems 给 identifier 列表、check() 用
  getIdentifierByName 按名查）。写 objID 的双重后果：
  ①GUI 报 `"Textarea": "<objID>" not found`；
  ②CLI **静默略过绑定** —— screens.c 里没有 lv_keyboard_set_textarea，
    键盘与输入框实际没连上（只有真机弹面板才暴露）。
  DSL 里仍传**节点引用**（place() 前缀会原地改 id，构建期读最终 id 才不错位）——
  json2eez 用 build_page 预解析的 id→path→objID 表**只做存在性校验**，
  写入值是 id 本身（路径公式必须与 children 递归一致：`parent/id + str(i)`）。
- **键盘特殊键字形**：lv_keyboard 用 LV_SYMBOL_BACKSPACE(F55A)/OK(F00C)/
  NEW_LINE(F115)/KEYBOARD(F11C)/LEFT(F053)/RIGHT(F054)/CLOSE(F00D)——
  经 glyphs_seed 进 FA 附加源（私有区自动分流）。
- **输入文本回读**：EEZ 变量无双向绑定，最简路径 = native 直读
  `lv_textarea_get_text(objects.m_xxx)`（普通控件有 objects 条目，与 List 不同）。

## 13. 画布布局（flow 组件摆位，2026-10-01 实测）✅

flow 组件的 left/top 不影响构建，但决定编辑器画布可读性。防重叠三条铁律：

1. **渲染高度 ≈ `40 + n_actions*30`**（声明 height 只是最小值，EEZ 会随动作数
   自动长高）——行距/分区高度必须按渲染高算（留 16px 间距），按声明高排会随
   动作数线性恶化（实测 9 动作链渲染 310 vs 行距 268，互压 42px）。
2. **每条链一个专属 X 区间**：分区列宽 380；tabsync 链各占 950；新链区起点 =
   前一链区右缘之外（不要用固定偏移猜，要累加既有链区宽度）。
3. **链内单行排布**：FRAME 类组件渲染长高，多行布局会被下一行纵向互压——
   单行时组件只占自己的 x 区间，天然安全。

自检方法（json2eez 生成后跑一次）：

```python
# rect = (left, top, left+width, top + max(声明高, 40+n*30))；两两判交，期望 0 对
```

## 14. 手册页码对照（详见本目录 01–06 号文档）

| 主题 | 手册章节 |
|---|---|
| User Actions / 事件 | P7.3、A34.2.16 |
| LVGL 动作清单（含 Anim\* 参数） | A43（P.215–221） |
| Animate（页面 timeline，Dashboard 机制） | A2（P.126–127）、P3.2 工具栏（P.38–39） |
| 变量/表达式 | P8（P.70–76）、P8.4 函数 |
| LVGL 字体/字形 | P11.2 |
| Tabview / 滑动行为 | W78（含 Active tab 属性） |

## §14 滑杆 / 开关真状态绑定（P-0047，2026-10-01 审计修复实测）

- **LVGLSliderWidget**（DSL `type:"slider"`）：字段与 bar 同名（min/max/mode/value/enableAnimation，
  **无 valueStart**）。`value` 用 `valueType:"expression"` 绑 native 变量即**双向**：
  tick `evalIntegerProperty → lv_slider_set_value`（外部→UI）+ VALUE_CHANGED handler
  `lv_slider_get_value → assignIntegerProperty`（拖动→`set_var_*`）（asar Slider.js 实证）。
- **KNOB 尺寸（★ 2026-10-02 修正，此前本段写错过）**：knob **直径 = 控件高度**
  （lv_slider.c draw_knob: `knob_size = lv_obj_get_height(obj)`；position_knob 里
  KNOB 的 pad 只把圆**向外扩**：`x1 -= pad_left`、`x2 += pad_right`，正 pad 不会
  缩小它）。所以想要「细轨道 + 大圆点」必须：**控件高度 = 圆点直径**，再用
  **MAIN 的 `transform_height` 负值收缩轨道**（lv_bar.c draw_indic：
  `lv_area_increase(&bar_coords, transf_w, transf_h)` 按 MAIN transform 收缩绘制区，
  INDICATOR 由收缩后的 bar_coords 推导，自动跟着变细）。DSL 侧 track() 已封装：
  参数 h = 轨道厚度，内部把控件撑成 knob 直径并把 y 上移 extra/2 保持轨道中线不变。
  （踩坑实证：h=5 的 slider 圆点只有 5px ≈ 看不见；rad 100 取圆、pad=0 即可。）
- **v9 slider defaultFlags 无 SCROLL_CHAIN_HOR**（asar 原文）——横拖不会把滚动链给外层
  tabview pager，拖进度条不换页；不要手动补回。
- **CHECKED 真状态**：`checkedStateType:"expression"` + `checkedState:"<bool变量>"`
  挂在 **Base.js**（任意 LVGL 控件都支持，不限 switch）。生成两段：
  tick `evalBooleanProperty → lv_obj_add/remove_state(CHECKED)`；
  VALUE_CHANGED `lv_obj_has_state → assignBooleanProperty`（回写 `set_var_*`）。
  普通容器按钮要可点选 → flags 追加 `CHECKABLE`（LVGL 原生翻转 + 发 VALUE_CHANGED）。
- **事件时序坑（P-0046）**：LVGL 9.4 CHECKABLE 翻转在 **LV_EVENT_RELEASED**
  （lv_obj.c:829-835），CLICKED 不翻。命令通道从 CLICKED(onAction) 迁到
  checkedState 回写后，冒烟脚本模拟点击要发 RELEASED（param=NULL 安全，
  lv_indev_get_scroll_obj 判 NULL）。
- **命令语义**：绑定回写带给定值（布尔/0..100 绝对值），toggle 类 APP_OUT_*
  的 v 一律改为「目标态」；User Action 直调入口需要翻转语义时在 native 层
  读 model 取反再入队（native_actions send_toggle）。
- **纯 UI 内部状态**（如通知筛选 notif_filter）：onClick SetVariable →
  set_var_notif_filter 直接 app_set_input_* 存 model，不经命令队列、不经 io。


### §14.1 Switch 的 KNOB pad 方向（P-0049，2026-10-02 实测）

- lv_switch.c 里 knob 区域同样是**向外扩**：`x1 -= pad_left; x2 += pad_right;
  y1 -= pad_top; y2 += pad_bottom`，且 knob 基准大小 = 控件高度。
  → **正 pad 会把圆点撑出轨道**（实测 pad 3：23px 轨道配 29px 大白球，圆点溢出）；
  **负 pad 才是内嵌**（pad -3 → 直径 23-6 = 17px，四周留 3px，与设计稿一致）。
- 设计稿「开关 = 蓝药丸 + 内嵌白圆」的正确写法：KNOB pad 全 -3、radius 100。
