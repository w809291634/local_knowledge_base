# ESP32-P4 + ESP32-C6 远程 WiFi（esp_hosted / SDIO）调试经验

板卡：Waveshare ESP32-P4-WIFI6-Touch-LCD-4.3（板载 ESP32-C6 提供 WiFi6）
架构：P4 = host，C6 = slave，传输层 = SDIO 4-bit 40MHz，软件 = esp_wifi_remote + esp_hosted
环境：ESP-IDF v5.5.5，工程 `base_template_p4_c61_wifi`

> P4 没有原生 WiFi 外设，应用层仍用标准 `esp_wifi` API，实际由 esp_wifi_remote 通过 esp_hosted + SDIO 转发到 C6 执行。

---

## 1. `wifi scan` 触发整板重启 —— 根因是供电不足（已实锤）

**症状**：执行 `wifi scan` 后开发板立即重启，串口监控断开。

```
I (66579) hci_stub_drv: Host BT Support: Disabled
I (66579) H_SDIO_DRV: Received INIT event
[I/app_wifi] (66579) scanning ...
I (66579) rpc_req: Scan start Req

--- Error: GetOverlappedResult failed (PermissionError(13, '拒绝访问。', None, 5))
--- Waiting for the device to reconnect
```

重连后的新启动日志：

```
I (2259) example: Running on CPU 0
esp32p4> [I/main] (2259) reset reason: POWERON (1)
```

**根因**：供电不足。P4 以 400MHz 运行 + 32MB PSRAM XIP 本就处于高功耗状态，而 `wifi scan` 是**唯一真正开射频**的命令 —— C6 从"射频关闭（mA 级）"跳到"全信道扫频"，电流台阶陡增，把 5V/3V3 拉过 POR（上电复位）阈值，导致：

1. P4 复位（复位原因 = POWERON）
2. 板载 USB-UART 桥（CH343）也一起从 USB 总线掉线 → COM 口消失

**修复**：改善供电即解决（换主板后置 USB 口 + 短粗 USB 线；或使用带独立供电的 USB Hub / 给板子接独立 5V，USB 只做通信）。经确认改善供电后不再复现。

---

## 2. 判定方法论：如何区分"芯片复位"与"供电事件"（可复用）

### 2.1 第一步：启动最早处打印复位原因

`esp_reset_reason()` 在 `app_init()` 里最先打印（放在最前，避免被后续复位冲掉）：

```c
/* Indexed by esp_reset_reason_t */
static const char *const RESET_REASON_NAME[] = {
    "UNKNOWN", "POWERON", "EXT_PIN", "SW(esp_restart)", "PANIC",
    "INT_WDT", "TASK_WDT", "OTHER_WDT", "DEEPSLEEP", "BROWNOUT",
    "SDIO", "USB", "JTAG", "EFUSE", "POWER_GLITCH", "CPU_LOCKUP",
};

int reason = (int)esp_reset_reason();
log_i("reset reason: %s (%d)", RESET_REASON_NAME[reason], reason);
```

| 值 | 名称 | 含义 |
| --- | --- | --- |
| 1 | POWERON | 电源上电复位（掉电/电压塌到 POR 阈值以下，或 EN 脚被拉低） |
| 3 | SW | 有代码主动调 `esp_restart()` |
| 4 | PANIC | 崩溃（abort / 异常） |
| 5 / 6 / 7 | INT_WDT / TASK_WDT / OTHER_WDT | 看门狗 |
| 9 | BROWNOUT | 欠压检测器（BOD）触发 |
| 10 | SDIO | 由 SDIO 通路触发 |
| 11 | USB | 由 USB 外设触发 |
| 14 | POWER_GLITCH | 电源毛刺 |

### 2.2 第二步（关键）：看串口桥是否也掉线

**判据：外置 USB-UART 桥芯片的 COM 口掉线 + 复位原因 POWERON ⇒ 供电/总线事件，而非芯片自身问题。**

- 外置桥芯片（CH343 / CH340 / CP2102 / FTDI）有独立的 USB 控制器和供电，**芯片单纯复位动不了它**。若只是 P4 复位，会在同一端口上看到从 `rst:0x..` 开始的完整重启日志，不该出现 `PermissionError`。
- 所以出现 `GetOverlappedResult failed (PermissionError(13))` + `Waiting for the device to reconnect`，说明**掉的不只是芯片，而是整条 USB 供电/总线**（VBUS 跌落、USB 口过流保护动作），芯片复位只是伴生结果。
- 反之，如果 COM 口是**芯片自带的 USB**（USB-Serial-JTAG / CDC），芯片复位会让它重枚举、端口照常消失 —— 此时"复位导致掉线"才成立。**先确认端口归属再下结论**：设备管理器看硬件 ID 是否含 `CP210x` / `CH340` / `CH343` / `FTDI`。
  - 本板卡：控制台走 UART0 物理引脚 GPIO37(TX)/38(RX)，COM20 = 板载 CH343 桥，**不是**芯片自带 USB。

### 2.3 为什么是 POWERON 而不是 BROWNOUT

电源塌得又快又深时，欠压检测器（BOD，触发阈值较高）来不及动作，芯片直接走 POR —— 所以看到的是 `POWERON`。**POWERON 不等于"正常开机"，它同样可以表示掉电**。

### 2.4 排除项（本例已逐一排除）

| 怀疑方向 | 排除依据 |
| --- | --- |
| 软件崩溃 panic | 无 Guru Meditation / backtrace，复位原因非 PANIC/WDT |
| 代码主动重启 | 复位原因非 SW(3) |
| esp_hosted 判 SDIO 链路不可恢复后 `_h_restart_host()` | 同上，非 SW(3) |
| 内存不足 | 33MB 堆空闲，`wifi status` 等命令正常 |
| SDIO 链路/从机枚举失败 | `Received INIT event` / `Base transport is set-up` / `Slave chip Id[12]` 全部正常 |
| WiFi 协议栈初始化失败 | `app_wifi_stack_init()` 返回 true，`scanning ...` 已打印，无 `ESP_ERROR_CHECK` 失败 |

### 2.5 为什么只有 `wifi scan` 复现

- `wifi status` / `wifi slave` / `wifi stats` → 只走 SDIO 控制通路，射频基本不工作，功耗平稳
- `wifi scan` → 唯一真正开射频的命令，功耗台阶最陡 → 供电吃紧时刚好越界

### 2.6 若改善供电后仍复位，再查这两个方向

1. **EN 脚被自动复位电路干扰**：串口掉线时 DTR/RTS 抖动可能误拉低 EN，同样报 POWERON。可临时断开自动复位电路验证。
2. **降低 SDIO 时钟**：`CONFIG_ESP_HOSTED_SDIO_CLOCK_FREQ_KHZ` 从 40000 降到 20000，减小高速总线翻转电流。

---

## 3. `wifi scan` 的 RPC 调用链（日志断层的迷惑性）

`esp_wifi_scan_start(NULL, true)` 会连续走三个 RPC，但**只有一个会打日志**：

| 顺序 | RPC | 日志 | 说明 |
| --- | --- | --- | --- |
| 1 | `scan_start` | `rpc_req: Scan start Req` | **唯一有日志的** |
| 2 | `scan_get_ap_num` | 无 | |
| 3 | `scan_get_ap_records` | 无 | 响应携带最多 20 条 `wifi_ap_record_t`，整条链路上**最大的一次 SDIO 传输** |

**踩坑**：日志停在 `Scan start Req` 之后，不代表崩溃点就在 `scan_start`。后面两个 RPC 完全没有打印，且扫描本身要耗时数秒（期间也没有任何输出），所以"日志断层处"≠"崩溃发生处"。排查时要把整条调用链都纳入怀疑范围。

---

## 4. 本板卡 / 本工程的固定事实（换板卡需核对）

| 项 | 值 |
| --- | --- |
| 控制台 UART | UART0，TX=GPIO37 / RX=GPIO38，CUSTOM 模式，961200 波特率 |
| 调试串口 | COM20 = 板载 CH343（外置桥，非芯片自带 USB） |
| WiFi 架构 | P4(host) + C6(slave)，esp_wifi_remote + esp_hosted，SDIO 4-bit 40MHz |
| 从机复位引脚 | GPIO54（esp_hosted 自动执行 `Reset slave using GPIO[54]`） |
| 日志特征 | `cpu_start: GPIO 38 and 37 are used as console UART I/O pins` |

### 4.1 sdkconfig.defaults 硬约束

- `ESP_WIFI_REMOTE_ENABLED` 与 `ESP_HOST_WIFI_ENABLED` **互斥**，不可同时开启
- 写 `CONFIG_ESP_CONSOLE_UART_DEFAULT=n`，**不要**写 `# CONFIG_ESP_CONSOLE_UART_DEFAULT is not set`（后者在配置阶段会报 malformed line 警告）
- `BOARD_CONFIG_ENABLE_WIFI_CMD` 置 0，避免与共享组件的 `join` 命令重复注册

### 4.2 WiFi 协议栈懒初始化

`esp_wifi_init()` 延迟到第一条 wifi 命令才执行。因此**第一条 wifi 子命令**（无论哪个）都会触发完整的传输层拉起：

```
transport: Attempt connection with slave: retry[0]
transport: Reset slave using GPIO[54]
sdio_wrapper: SDIO master: Data-Lines: 4-bit Freq(KHz)[40000 KHz]
transport: Received INIT event from ESP32 peripheral
transport: Base transport is set-up
transport: Slave chip Id[12]
```

实测 `Received INIT event` → `Scan start Req` 稳定间隔约 1.18s。**该过程本身不引发复位**（`wifi status` 同样会走完，正常）。

---

## 5. 通用经验提炼

1. **"复位原因 + 串口桥是否同时掉线"是区分芯片问题与供电问题的第一判据**，成本极低（一行 `esp_reset_reason()` 打印 + 看一眼 COM 口归属），优先做。
2. 串口 I/O 报 `PermissionError(13)` / `Waiting for the device to reconnect` 时，先确认端口是外置桥还是芯片自带 USB —— 这决定了"谁先掉"。
3. `POWERON` 不是"正常开机"的同义词，掉电同样是 POWERON。
4. **射频类操作（scan / connect / TX 大功率）是嵌入式项目最典型的供电临界点**：其他命令全正常、唯独一开射频就复位，优先怀疑供电，而不是先怀疑驱动/协议栈。
5. 换 USB 口、换短粗线、外供电，这三步成本远低于读代码，应排在排查序列最前面。
