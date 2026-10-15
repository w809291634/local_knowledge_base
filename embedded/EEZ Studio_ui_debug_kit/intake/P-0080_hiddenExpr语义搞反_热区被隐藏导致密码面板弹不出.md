# P-0080 hiddenExpr 语义搞反 → 整行热区被隐藏，密码面板/键盘永远弹不出

日期：2026-10-02　状态：fixed　涉及：EEZ hiddenExpr 语义、build_ui.py 行热区

## 现象
用户报「WiFi 输入密码弹不出来 / 键盘出不来」。`design/build_ui.py` 里 `git diff` 干净，
上一轮还特意"还原"过一行 `net_slotN_hit` 的 `hiddenExpr`。

## 根因（关键取证）
**EEZ 的 `hiddenExpr` 是「隐藏条件」，表达式为真 = 隐藏。**

自证（别靠注释，看生成代码）：`src/ui/screens.c` 的 hidden 求值模板 ——

```c
bool new_val = evalBooleanProperty(flowState, 549, 3, "Failed to evaluate Hidden flag");
bool cur_val = lv_obj_has_flag(objects.m_net_net_slot0_hit, LV_OBJ_FLAG_HIDDEN);
if (new_val != cur_val) {
    if (new_val) lv_obj_add_flag(objects.m_net_net_slot0_hit, LV_OBJ_FLAG_HIDDEN);
    else         lv_obj_remove_flag(objects.m_net_net_slot0_hit, LV_OBJ_FLAG_HIDDEN);
}
```

`new_val` 真 → `add_flag(LV_OBJ_FLAG_HIDDEN)` → **真 = 隐藏**。

而代码写的是：

```python
hit["hiddenExpr"] = "wifi_slot%d_ssid == '' || !(%s)" % (i, cur4)
```

`cur4` = 失败态（`wifi_state == 4 && wifi_conn_slot == i`）。常态下 `!(cur4)` 为 **true**
→ 热区被**隐藏** → 点 AP 命中的是没绑动作的 visible row → `wifi_pick_N` 从没被调用
→ 密码面板（→ 键盘）永远弹不出。**恰好反了**：失败态反而露出来、压在最上层盖住「重试」pill。

正确写法（与 pill 的 `hiddenExpr = !(cur4)` 严格互补：失败态显示 pill、隐藏热区，
一次点击只命中一个控件）：

```python
hit["hiddenExpr"] = "wifi_slot%d_ssid == '' || (%s)" % (i, cur4)   # 失败态隐藏热区
```

## 为什么上一轮没发现
P-0079 我把 `!(cur4)` 当成"用户刻意定的不要一点就弹 WiFi" 而拒绝改 —— **只看了代码字面，
没真点一遍去证伪**。「`git diff` 干净」不等于「语义正确」。用户一旦说"某功能没反应"，
必须真点一遍取证，而不是拿 diff 干净当免检牌。

## 复现/验证手法（PC 仿真，未上真机）
1. `python design/sim.py --walk=pwd` —— `pwd` 脚本加了 `state` 硬自证：
   点前 → `密码面板=隐藏/未开 键盘=隐藏`；点 `net_net_slot1_hit` 后 →
   `密码面板=可见 键盘=可见`。
2. 截图目检：`build/sim_shots/walk_pwd/11_pwd.png` —— 面板 + 全键盘完整无裁剪
   （2026-10-02 "面板按整屏算被内容区裁掉键盘" 那次修复有效）。
3. 回归：`wifi`（弹面板→join→连接）、`wifi_retry`（重试链）、
   `wifi_ok`（已保存直连）、`click_speed`（快慢手速都命中 `_hit` 并弹面板）。
4. `python design/all.py --sim` 门禁 9.29% < 25%；`_device_syntax_check.py` 4 文件 0 错 0 警。

## 「这个能不能在 EEZ 里实现」—— 能，是 EEZ 原生属性
- 知识库 `reference/05_widgets_part1.md:797-798` 与 `06_widgets_part2.md:56-57` 是官方属性表：
  `Hidden` — **EXPRESSION (boolean)**「隐藏对象」、`Hidden flag type` — Enum
  （Literal / Expression 二选一）。这就是 EEZ Studio 图形界面里
  「选中 Widget → Flags → Hidden 勾上 → flag type 选 Expression → 填表达式」那同一个属性。
- 映射链路（改这一行到底落在 EEZ 哪里）：
  `build_ui.py` DSL → `ui.json` 的 `hiddenExpr` → `json2eez.py:355-358` 写成
  `hiddenFlagType="expression"` + `hiddenFlag=<expr>` → project.json（Studio 打开的工程文件）
  → EEZ CLI build → `screens.c` 的 `evalBooleanProperty(...)` → 每帧 add/remove `LV_OBJ_FLAG_HIDDEN`。
  也就是说 **`build_ui.py` 只是批量填 EEZ 那个 Hidden 表达式框的内容**，改法是 EEZ 原生的，
  在 Studio 里手工改 box `m_net_net_slot0_hit` 的 Hidden 表达式得到的是同一套东西。
- 表达式引擎支持 `== != < > <= >= && ||`（`eez-flow.cpp` 的 `do_OPERATION_TYPE_*`），
  本工程已大量使用 `!()` / `&&` / `||`（见 ui.json 里十几个既有 hiddenExpr），改法无兼容性风险。

## 通用教训
- 写"条件 C 时隐藏 X" → `hiddenExpr = C`；写"条件 C 时**不**隐藏 X" → `hiddenExpr = !C`。
  `!` 加错就整体反转，而且**静态看代码完全看不出来**（两个分支都"讲得通"）。
- 涉及 `hiddenExpr` 的逻辑，改完必须有一条走路脚本用 `state`/`lv_obj_is_visible()` 做
  **可见性硬自证**，只看截图容易漏（面板没弹但 tree 照样能跑 = P-0079 的假绿）。
- 与用户"刻意设定"冲突时，先按用户说的跑一遍取证，再决定是"还原"还是"违反"。

## 关键词
hiddenExpr语义, 真=隐藏, add_flag LV_OBJ_FLAG_HIDDEN, 热区被隐藏, 点击无响应,
WiFi密码面板弹不出, 键盘不可见, 走路器state自证, 假绿, 别只看git diff