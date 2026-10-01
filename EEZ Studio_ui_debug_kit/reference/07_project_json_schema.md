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
