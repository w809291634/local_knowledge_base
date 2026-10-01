# P-0041 native 变量死活审计：io 写/UI 不读的 4 个白写变量删除（六文件同步）

- **状态**：fixed
- **发现日期**：2026-10-01
- **提示词**：PR-0068
- **标签**：native变量, APP_IN, io写入, 死变量, 三向审计, 变量删除, 双向绑定

---

## 一、背景（用户原话：「有些变量我看到没有什么实质作用，这些变量本来是用于
给外部使用的，有些变量没有实质使用意义」）

P-0040 从 EEZ 侧审计了变量消费；本轮从 **native 侧反向审计生产/消费闭环**：
每个 APP_IN_* 变量必须有「io 层写入 → UI 层消费」的完整链，断一环即死。

## 二、审计判据的最终形态（编译器级，零猜测）

对每个变量统计四个调用点：
1. **UI 表达式引用**（hiddenFlag/text/Compare 等裸引用，P-0040 方法）
2. **EEZ 生成代码消费**：`get_var_<名>` 在 eez-flow.cpp/screens.c 的调用数
3. **io 层写入**：`APP_IN_<大写>` 枚举在 io_pc/io_esp 的出现数
4. **io 层读回**：`get_var_<名>` 在 io 层的调用数（反向变量，如滑块双向绑定）

⚠ 本轮曾有两个判据误区：①只查 get_var_ 方向漏掉 set_var_（brightness 误判）；
②枚举名映射想当然（brightness 实际走 APP_OUT_BRIGHTNESS 命令通道，无 APP_IN_
枚举）。**四点全查后按「写读闭环」判定**。

## 三、定论（32 个全局变量）

- **✓ 健康 27 个**：UI 表达式/native 读写闭环完整。
- **✓ 保留 1 个**：`brightness` —— 虽然当前全向无调用，但它是亮度滑块的
  **现成接口**（`get/set_var_brightness` 转发 `APP_OUT_BRIGHTNESS` 命令，注释
  明确「暂留：四个 slider_row 目前纯绘制无事件」），滑块事件化时直接绑定。
- **✗ 删除 4 个**：`wifi_rssi`（io 写 5 处、UI 0 读）、`battery_charging`
  （io 写 3 处、UI 0 读）、`wifi_icon`（全向零引用）、`wifi_bars_visible`
  （全向零引用）——**状态栏信号格/电池图标一族的功能预留，UI 从未绑定**
  （状态栏图标是静态字形）。

## 四、修复（六文件同步，P-0020 链路纪律）

| 文件 | 改动 |
|---|---|
| design/build_ui.py | 变量声明表删 4 行（EEZ variables[] 自动同步 32→28） |
| src/native/native_vars.cpp | 删 4 变量的 get/set 实现 + **battery_pct 残留实现**（P-0040 只删了 EEZ 侧）+ wifi_icon/wifi_bars 派生块 |
| src/native/native_vars.h | 对应声明删除 |
| src/native/platform/io_pc.cpp | 删 APP_IN_WIFI_RSSI/BATTERY_PCT/BATTERY_CHARGING 写入 + fake battery 模拟块 |
| src/native/platform/io_esp.cpp | 删注释中的示例行 |
| src/native/app_model.h | 删 APP_IN_WIFI_RSSI/BATTERY_PCT/BATTERY_CHARGING 枚举（APP_IN_COUNT 自动缩减；APP_WIFI_SLOT_ID 具名引用不受影响） |

## 五、证据

- 全局变量 32→**28**；vars.h get 声明 28（28 对）；死变量残留 **0**；
- `all.py --shots` EXIT=0：11 屏对照 8.62%、6 条 swipe 断言全过、
  native 编译链接正常。

## 六、沉淀

- **native 变量审计判据 = 四点闭环**（UI 表达式 / EEZ 生成代码 get_var_ 调用 /
  io 写入枚举 / io 读 get_var_），「写读闭环」断一环即死；双向绑定变量
  （滑块）必须查 set_var_ 方向。
- **删除变量是六文件同步操作**（声明表/native_vars.cpp/native_vars.h/io 层
  写入/枚举/EEZ variables[]），漏一处就是断链或死代码——P-0020 链路纪律的
  变量版。
- 功能预留变量（如 brightness）删除前先看注释与命令通道关联。
