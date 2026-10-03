# P-0094 · 「始终连上次指定的WiFi」= 把 SsidManager 剪成唯一一项（推翻 P-0086 的 set_config 方案）

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：WiFi,SsidManager,HandleScanResult,RSSI,剪枝,StartStation,managed_components
- **关联提示词**：PR-0118 / PR-0122 / PR-0125

## 现象（看到什么）

用户在 WiFi 设置里点 HUAWEI-TC7102 并确认，开机/断线重连却连上信号更强的小米共享热点，MQTT/OTA 全连不上；两份真机日志实证（点 -53 的目标，连上 -43 的共享热点）。

## 复现（怎么稳定重现）

开机 TryWifiConnect 到 StartStation 到 STA_START 里 esp_wifi_scan_start，扫完 HandleScanResult 按 RSSI 降序取第一个在保存列表里命中的 AP。

## 根因（真正的原因）

wifi_station.cc:181-193 与 222-263 —— StartConnect 自己再 esp_wifi_set_config 一遍并 esp_wifi_connect，把调用方刚设的 STA 配置覆盖掉。P-0086 的修法只在 station 已 active 时成立（那时 StartStation 因 station_active_ 早退、不走扫描选择）。managed_components 被 gitignore 且带 .component_hash，原地改有被组件管理器重下抹掉的风险，故不动组件。

## 修复（做了什么）

io_esp 新增 wifi_keep_only：先拷列表快照（GetSsidList 返回内部 vector 的 const 引用，边遍历边 RemoveSsid 必失效），删掉所有非目标项，目标缺失则 AddSsid；在 WCMD_PICK_SSID 与 WCMD_JOIN_PWD 的 set_config+StartStation 之前调用。剪枝同一轮把 s_scan_result 里其它加密行的 sub 标记重拼并置 s_scan_done，避免界面还写已保存而点它却要密码。io_pc 用 wifi_keep_only_saved 同语义镜像（同样立即 publish）。

## 证据（数字 / 命令输出）

走路器双判据：audit net_net_list 读 label 真值（slot0 由 已保存 变 未保存，slot3 反向，label 宽度 111px 变 55px）；再点 slot0 改弹密码面板且 state 显示面板与键盘可见。真机日志：Found AP 只剩 1 条、断线后 Reconnecting 只认目标。设备侧真编译 4 文件 0 错 0 警。

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md 铁律新增一条（StartStation 语义 + 剪枝解法 + GetSsidList 引用陷阱 + Add/RemoveSsid 每次写 NVS）；补 P-0086/P-0087 正文
