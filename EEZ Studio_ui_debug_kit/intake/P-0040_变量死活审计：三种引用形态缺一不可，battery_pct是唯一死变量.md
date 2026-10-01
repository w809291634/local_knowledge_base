# P-0040 变量死活审计：三种引用形态缺一不可，battery_pct 是唯一死变量

- **状态**：fixed
- **发现日期**：2026-10-01
- **提示词**：PR-0066
- **标签**：变量审计, hiddenExpr, Label绑定, native读写, 死变量, battery_pct

---

## 一、现象（用户原话：「有些本地变量是不是没有作用，没有作用可以删除掉」）

用户在 EEZ GUI 里看到变量列表怀疑有无用变量。

## 二、审计方法的三次迭代（教训所在）

1. **第一版（错）**：JSON 里 `"变量名"` 带引号计数 + vars.h/eez-flow.cpp 代码计数
   → 报 18 个「无引用」。**两个盲区**：
   - hiddenFlag/表达式里变量是**裸写**（`wifi_state == 2`），不带引号；
   - **Label 的 text 绑定**（Assignable）也是裸名（`wifi_conn_ssid` 出现在
     widget 的 text 字段）。
2. **第二版（仍不全）**：加 hiddenFlag/表达式池 + native 层读写 → 报 9 个。
   仍漏 **Label text 结构化绑定**（`wifi_conn_ssid` 等出现在 widget 的 text
   字段值里，JSON 计数 >1 但不在表达式池）。
3. **最终判据（三态合并）**：
   `活 = JSON带引号计数>1（结构化绑定） ∨ 表达式裸引用 ∨ native层读写`
   → **唯一死变量 = `battery_pct`**（33 个全局变量中）。

## 三、结论与修复

- **删除**：`battery_pct`（build_ui.py 变量声明表）——UI 无绑定、native 无读写
  （io 层只写 `battery_charging`，状态栏电池无百分比文本）。全局变量 33→32。
- **保留（看似无用实则有用了）**：
  - `main_page_idx` / `set_page_idx`（页面局部变量）：换页同步链的
    getActiveTab 结果 + Compare 判据，删了链就断；
  - `wifi_slot{i}_rssi/lock`：hiddenExpr 裸引用（锁图标显隐/信号文案）；
  - `wifi_conn_ssid/ip`、`wifi_err`、`wifi_slot{i}_sub`：Label text 绑定
    （连接卡/错误行/行副标题的运行时文本）；
  - `wifi_rssi/wifi_icon/wifi_bars_visible/battery_charging/brightness/
    wifi_conn_slot`：native 层读写（io_pc/io_esp 状态栏/网络状态写入）。
- 页面局部变量 2 个全部有引用，未删。

## 四、证据

- 删除后 `all.py --shots` EXIT=0：11 屏对照 8.62%、6 条 swipe 断言全过、
  native 编译链接正常（vars 表 32 个）。

## 五、沉淀

- **变量死活审计必须三态合并**：①JSON 结构化绑定（text/entries.variable，带引号）
  ②表达式裸引用（hiddenFlag/Compare/表达式，正则 \b 词边界）③native 读写
  （src/native 全文）。任何单一形态都会误报——本次第一版误报 18 个、第二版误报 8 个。
- 删除变量前先想 **native 链接**（P-0020）：variables[] 里的变量会被 EEZ 生成
  get_var_/set_var_，native 用宏引用它们——从 EEZ 侧删了变量，native 侧不同步就断链。
