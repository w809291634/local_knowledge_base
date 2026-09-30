# P-0031 状态机 UI 用 hiddenExpr 声明式显隐（互斥控件叠字 / pill 宽度顺序两个坑）

- **状态**：fixed
- **发现日期**：2026-09-30
- **提示词**：PR-0058
- **标签**：hiddenExpr, hiddenFlag, 声明式显隐, 状态机, 互斥显隐, pill宽度, 事件冒泡, 双命令, 表达式嵌套括号

---

## 一、现象

网络页从「全静态画面（写死 3 个网络名 + 假"连接中…"）」重做为
**5 态状态机**（0 列表 / 1 扫描中 / 2 连接中 / 3 已连接 / 4 失败）。

做法：`design/json2eez.py` 支持 `hiddenExpr` → 写工程 JSON 的
`hiddenFlagType:"expression"` + `hiddenFlag:"<表达式>"`，EEZ build 生成
`evalBooleanProperty` 每帧求值 + 自动 add/remove `LV_OBJ_FLAG_HIDDEN`。
**UI 逻辑零用户代码**，完全符合「UI 控制与控件联动一律 EEZ 优先」铁律。

链路跑通（build 零错误、54 处 `evalBooleanProperty`），但**四态出图核对**发现两处视觉/交互缺陷：

1. **锁图标骑在「正在连接…」文字上**（本该互斥的两个控件同时显示）；
2. **「连接超时」红字压在「重试」pill 上**。

另外核验工程 JSON 时发现第 3 个问题：

3. 一次点击「重试」会发出**两条** `wifi_pick_1` 命令。

## 二、根因

### 坑 1：hiddenExpr 里嵌套括号 → 判定恒真/恒假

DSL 里图省事写成「扁平条件 + 括号子条件」：

```python
hiddenExpr = "wifi_slot%d_lock == 0 || !(%s)" % (i, show_idle)
# 其中 show_idle = "!(%s)" % state_of_row
```

落盘到 `ui.json` 里被再包一层，变成：

```
wifi_slot0_lock == 0 || !(!((wifi_state == 2 || wifi_state == 3 || wifi_state == 4) && wifi_conn_slot == 0))
```

**嵌套 `!(...)` 的语义在 EEZ 表达式引擎里不是按 Python 直觉走的**（外层 `!` 作用于
内层带括号的复合表达式时优先级/解析与预期不符），结果该隐藏的不隐藏 →
互斥的两组控件（锁图标 / 「正在连接…」）同时出现、横向叠在一起。

**规则**：`hiddenExpr` **只用扁平的 `&&` / `||` 串**，`!` 直接贴比较式写；
需要分组时**预先展开**成 `!X && !Y && !Z`，不要写 `!(A && B)` 再往外套括号。

修法：

```python
cur2 = "wifi_state == 2 && wifi_conn_slot == %d" % i
cur3 = "wifi_state == 3 && wifi_conn_slot == %d" % i
cur4 = "wifi_state == 4 && wifi_conn_slot == %d" % i
idle = "!(%s) && !(%s) && !(%s)" % (cur2, cur3, cur4)   # 三条独立否定，不嵌套
```

### 坑 2：`pill()` 返回的宽度只能在 `x=0` 锚点下用

`design/build_ui.py` 的 `pill(x, y, h, text, ...) -> (node, w)`，`w` 是**从 x=0 起算**
的内容宽 + 左右 padding。失败的排版写成：

```python
fb, fw = pill(0, 0, 24, "重试", 11, ERR, SURFACE2)
shift(fb, rx - fw, ry + (NET_ROW_H - 24) / 2.0)      # ← 先 shift 了
rk.append(label_right(rx - fw - 8, ...))             # ← 再用 fw 反推邻居位置
```

`shift` 之后 `fb` 已经在正确位置，但 `label_right(rx - fw - 8)` 里的 `fw` 是
**内容宽**，`rx - fw - 8` 算出来的锚点落在 **pill 内部**，于是「连接超时」文字正好
压在 pill 上（截图里就是两个字叠在一起，看着像乱码）。

**规则（顺序固定）**：

```python
fb, fw = pill(0, 0, 24, "重试", 11, ERR, SURFACE2)
pill_x = rx - fw                        # ① 先用 w 反推 pill 的 x
shift(fb, pill_x, ry + (NET_ROW_H - 24) / 2.0)   # ② 再 shift
err_x = pill_x - 10 - tw("连接超时", 11)  # ③ 邻居用 pill_x 定位，不用 fw
```

### 坑 3：行容器与行内按钮绑同一动作 → 一次点击两条命令

```python
row["onAction"] = "wifi_pick_%d" % i     # 行本体
fb["onAction"]  = "wifi_pick_%d" % i     # 失败态「重试」pill（在 row 内部）
```

点「重试」时 pill 命中，事件继续**冒泡到 row** 又触发一次 → `io_wifi_pick` 被调两次。

**修法**：行容器**改成纯展示、不绑动作**；另外加一层 `bgOpa=0` 的**透明热区按钮**
铺满整行负责点击，其 `hiddenExpr` 与行内按钮**互补**（失败态让位给 pill）：

```python
hit = box(ix, ry, iw, NET_ROW_H, id="net_slot%d_hit" % i, bgOpa=0, clickable=True)
hit["onAction"] = "wifi_pick_%d" % i
hit["hiddenExpr"] = "wifi_slot%d_ssid == '' || !(%s)" % (i, cur4)
```

这样**一次点击永远只命中一个控件、只发一条命令**，职责也清楚。

## 三、附带记录：`label_right` 右对齐会飘

`label_right(rx, ...)` 内部按 Pillow 量宽反推 x，与 LVGL 实渲差 1~2px
（含 `…` 省略号时更明显），表现为右边缘对不齐。要严格右对齐就自己算：
`label(rx - tw(text, px), ...)`。

## 四、验收（怎么证明修好了）

- **四态出图逐张看**（不是靠断言）：`platform/io_pc.cpp` 认 `EEZ_SIM_STATE=<n>[,slot]`
  把状态**钉住**（否则 `shoot()` 只拍一张、扫完就回列表态，中间态根本拍不到）。
  四态图拼版存 `build/sim_shots/09b_wifi_states.png`：
  列表+已连接 / 扫描中 / 连接中 / 失败+重试。
- 工程 JSON 核验：`已连接 x=717`、`重试 x=722`、`wifi_err x=656`（= pill 左边 - 66），
  三者不再重叠。
- `all.py --shots` 全绿：EEZ build **No error and no warning**、11 屏出图、
  6 条 swipe 断言全过。

## 五、环境/工具注意（手动跑仿真 exe）

- Windows 下 `getenv` **读不到 shell 设的环境变量**，需先 `_putenv("")` 刷新 CRT 环境；
- 手动跑 `main.exe` 要把 `SDL2.dll` + `libstdc++-6.dll` + `libgcc_s_seh-1.dll` +
  `libwinpthread-1.dll` 拷到 exe 同目录；
- 出图目录参数必须 Windows 风格路径（`C:/…`）；传 `/foo` 会被当根路径解析，
  `fopen` 静默失败（脚本里会看到 `cp` 找不到文件）。

## 六、沉淀

- `skills.md §11.18`：hiddenExpr 机制说明 + 四个坑对照表 + 状态机页配方（模板）。
- 项目 `MEMORY.md`：新增「EEZ 声明式显隐 = hiddenExpr」章节。
