# P-0200 · WLAN 通知两个坑：sizeof 通知结构体偏大、通知里的 SSID 是 ANSI 不是空口字节

- **工程**：app-wifi-scan-conn-no-flow（PC 真接口）
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：wlanapi,通知,失败原因,结构体,编码
- **关联提示词**：PR-0370

## 现象（看到什么）

接好 `WlanRegisterNotification` 之后，真机点连接失败，标题栏仍然只有
「连接失败 X」——一条 `notify` 日志都没有，像是通知根本没来。

## 复现（怎么稳定重现）

在回调里按 `d->dwDataSize < sizeof(WLAN_CONNECTION_NOTIFICATION_DATA)` 过滤，然后
`WIFI_WIN_DUMP=1` 跑一次真连接：日志里只有 `notify src=8 code=10 size=572`，
后面那条解析日志永远不出现。

## 根因（真正的原因）

1. `WLAN_CONNECTION_NOTIFICATION_DATA` 尾部是 `WCHAR strProfileXml[1]` 的变长尾巴，
   **sizeof 明显大于实际 payload**（本例 sizeof 比 572 大），所以"太短"判据把所有通知
   都丢了。正确下限是 `offsetof(WLAN_CONNECTION_NOTIFICATION_DATA, strProfileXml)`。
2. 认领"这条通知是我这次尝试的"时，我用空口抓到的 SSID 原始字节去比通知里的
   `dot11Ssid`：**同一条中文 SSID，空口 17 字节（UTF-8），通知里 13 字节（ANSI 码页）**，
   字节比对永远不相等。改用 `strProfileName`（宽字符）比对才稳。

## 修复（做了什么）

`platform/pc/wifi_platform_win.cpp:on_wlan_notify()`：改用 offsetof 判长度；按
profile 名认领；`WlanReasonCodeToString()` 失败时退化成「错误码 N」；去掉系统文案尾部句号。
另外把"服务已判失败"做成一个标志，`win_io_sample()` 下一拍立即收圈报错（原来要干等 10s 超时）。

## 证据（数字 / 命令输出）

`[WIN] notify code=10 reason=163851 "特定的网络不可用"` →
标题栏 `连接失败 YJT-1号楼办公（特定的网络不可用）`；整次尝试 4.6s 结束（含 2s 扫描），
出图 `build/sim_shots/real_fail_reason.png`。

## 沉淀（新增断言 / 案例 / 文档）

- **凡是"回调数据 + 变长尾巴"的 Win32 结构体，长度判据用 offsetof 固定字段，不要 sizeof**。
- **跨 API 比对同一个标识（SSID/UUID/路径）时，先确认两个 API 用的是同一编码/形态**；
  实在不确定就用双方都规范化过的字段（这里是 profile 名）。
- 失败原因这一类"只在真机出现"的文案，假世界没有对应分支 → 明确写进文档说明覆盖边界，
  别让门禁绿着却以为验过了。
