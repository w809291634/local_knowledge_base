# P-0086 · 真机「点的不是连的」：StartStation 前写 STA 配置只在 station 已 active 时有效

> 本条是**回填**（2026-10-03 由 Qoder 按 INTAKE 方式 B 补建）。素材 = 工程日志
> `.workbuddy/memory/2026-10-02.md` 第 102 轮（20:48）原文 + 当日 index 无行、
> intake 无正文的缺账事实。**当时结论已被 P-0094 推翻**，见文末「追加」。

- **工程**：eez-test（真机 io_esp + xiaozhi esp_wifi 组件链）
- **日期**：2026-10-02（回填 2026-10-03）
- **工具**：WorkBuddy（原轮次）/ Qoder（回填）
- **状态**：fixed（当时）→ **已被 P-0094 推翻并替代**
- **标签**：WiFi,StartStation,esp_wifi_set_config,STA配置,点的不是连的,回填
- **关联提示词**：无（第 102/103 轮的提示词当时未逐字补录，PR-0112 之后直接跳到 PR-0113；用户原话见工程日志：「明明连的是指定 wifi，显示的是另一个」）

## 现象（看到什么）

用户在 WiFi 浮层点第 N 行的某个 SSID（或输入密码后点「连接」），真机连上的却是**另一个网络**，
UI 显示的就是那个别的网络。同轮还有一个 UI 现象：「重新扫描」pill 太小（26 高 / 11px 字 / 无边框）。

## 复现（怎么稳定重现）

真机侧：保存过多网络、且 esp_wifi 自己 NVS 里上一次成功连接留下的 STA 配置指向 A，
在 UI 上点 B ⇒ 连上 A。PC 仿真**复现不出来** —— io_pc 的假状态机按槽位写 `CONN_SSID`，
天然一致，这是真机专属问题。

## 根因（真正的原因）

`WCMD_PICK_SSID` / `WCMD_JOIN_PWD` 两条路径都是**裸调 `wifi.StartStation()`**。
esp_wifi 的语义是「按**已保存的 STA 配置**连」而不是「按**参数**连」：StartStation 会
用 esp_wifi 自己 NVS 里上次那份 `wifi_config_t`，那份可能指着别的 SSID ⇒ 点的 A、连上 B。

显示侧另有半个根因：`publish_state_locked()` 的 `snap.ssid` 取自组件 `GetSsid()`，
那是**配置值**，与实际关联的 AP 不是一回事，两者不一致时就把「已连接」显示成另一个网络。

为什么以前没发现：PC 仿真永远编译不到 esp_wifi 这层真实语义，G1~G5 门禁全绿也照不到；
只有真机能暴露。

## 修复（做了什么）

`eez-test/src/native/platform/io_esp.cpp` 工作任务里，pick 与 join 两条路径各加：
1. `esp_wifi_get_config` 取回当前 STA 配置 → 把 `ssid` 改成**用户点的那个** →
   密码从 `SsidManager` 取（开放网络置 `threshold.authmode = OPEN`）→ `esp_wifi_set_config`
   → `esp_wifi_disconnect`（避免旧连接抢）→ 再 `StartStation()`；join 同款，密码用刚输入的；
2. **显示权威源**改为 `esp_wifi_sta_get_ap_info()`（STA 实际关联的 AP）优先，
   `GetSsid()` 只作兜底；
3. 「重新扫描」pill 26→34 高、11→13px 字、加 LINE 边框、pad 16，「可用网络」小标题 11→12px。

## 证据（数字 / 命令输出）

设备侧 4 文件真编译 0 错 0 警；`all.py` PASS；`walk wifi` / `net_states` 回归绿。
本条**没有**留下「修复前连错、修复后连对」的真机日志对比 —— 这正是它被推翻的伏笔。

## 沉淀（新增断言 / 案例 / 文档）

当时的教训（措辞）：esp_wifi 系任何「连接」都必须**先 `set_config` 明确 SSID** 再启动，
`StartStation` 是「按配置连」而不是「按参数连」。→ 这条**结论方向对、机制描述不全**，
由 P-0094 修正。

## 追加（2026-10-03 · P-0094 推翻本条的方案，按纪律只追加不改上文）

1. **本条的修法不成立**：`esp_wifi_set_config` 只在 **station 已经 active**（`esp_wifi_start()`
   之后）时才影响随后的连接目标。`WifiManager::StartStation()` 内部先 `Scan()` →
   `HandleScanResult()` 在 `SsidManager` 列表里按 **RSSI 降序**挑一个 → 才 `StartConnect()`
   重新 `set_config`。所以「先写配置」在冷启动路径上会被 `HandleScanResult()` 的选择**覆盖掉**
   —— 用户点 B、扫描发现 A 信号更强，照样连 A。真实案例是「有时连上共享热点」。
2. **生效的修法**（P-0094）：`io_esp::wifi_keep_only()` 把 `SsidManager` 列表剪成
   **唯一一项 = 用户指定的目标**，`HandleScanResult()` 没得挑 ⇒ 点谁连谁 / 开机始终回连指定 AP。
   零改 `managed_components`（该目录 gitignore + 带 `.component_hash`，改了会被重新拉取覆盖）。
3. **仍然有效、别丢**：`snap.ssid` 取 `esp_wifi_sta_get_ap_info()`（实际关联）优先、
   `GetSsid()`（配置值）兜底 —— 这条与剪枝正交，P-0094 没有回退它，现仍在 io_esp.cpp:418-426。
4. **口径教训**：本条当初写「已修复」但只有编译/仿真证据，没有「点的=连的」的真机对照日志。
   真机专属问题必须留真机证据，否则推翻时没人知道它什么时候真的好过。
