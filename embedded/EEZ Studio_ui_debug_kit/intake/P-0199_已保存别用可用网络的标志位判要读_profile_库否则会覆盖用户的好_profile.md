# P-0199 · 「已保存」别用可用网络的标志位判，要读 profile 库——判错会把用户的好 profile 覆盖掉

- **工程**：app-wifi-scan-conn-no-flow（PC 真接口）
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：wlanapi,profile,状态判据,误覆盖,真接口
- **关联提示词**：PR-0369

## 现象（看到什么）

界面上每条网络都没有「已保存」胶囊，可 `netsh wlan show profiles` 明明列着这些 profile。
用户点一条**其实存过密码**的网络，弹的是"输入密码"半页；输完（哪怕输错）点连接，
失败；再点又失败，越试越糟。

## 复现（怎么稳定重现）

真接口模式扫一次，用 `WIFI_WIN_DUMP=1` 打印每行的 `saved` 与 profile 名：
`[WIN] #3 "YJT-1号楼办公" ... saved=0`（同时 `netsh wlan show profiles` 里存在同名 profile）。
无头用例里表现为 `[REACH] FAIL 没有「已保存且未连接」的行`。

## 根因（真正的原因）

`WLAN_AVAILABLE_NETWORK.dwFlags` 的 `WLAN_AVAILABLE_NETWORK_HAS_PROFILE` 位**不可靠**：
本机（Win11 + MediaTek MT7902）上 profile 存在、网络也在扫到的列表里，这一位却是 0，
`strProfileName` 也是空的。用它判"已保存"会连环出两个错：
① 显示错（没有「已保存」胶囊）；
② **行为错**——已保存的网络被当成"没存过密码"，于是弹半页收密码，
    而收密码的路径会 `WlanSetProfile(..., bOverwrite=TRUE)`，**把原本能用的 profile 覆盖成用户随手输的密码**。

## 修复（做了什么）

`platform/pc/wifi_platform_win.cpp:query()`：先 `WlanGetProfileList()` 取一次 profile 库，
按 profile 名与 SSID（UTF-8↔UTF-16 转换后）严格相等判 `saved`，条目标志位只作兜底；
新增 `WIFI_WIN_DUMP=1` 逐行打印（ssid/rssi/band/auth/lock/saved/conn/profile）作为排查入口。

## 证据（数字 / 命令输出）

修后 dump：`[WIN] #3 "YJT-1号楼办公" -74 dBm 2.4 GHz auth=WPA2 lock=1 saved=1 conn=0`；
点它直接下发 `WlanConnect`（不再弹半页）；`[NAV] PASS 44 / FAIL 0`、`preflight` 全绿。

## 沉淀（新增断言 / 案例 / 文档）

**凡是要根据"系统里是否已有 X"改行为（尤其是会覆盖系统数据的动作），判据必须读那份数据的权威来源**
（这里是 profile 库），不能读一个"顺带带出来"的标志位；标志位漏报的后果不只是显示错，
而是会触发一条破坏性的写路径。落档：工程 `EEZ_WORKFLOW.md` §5.10 问题 4。
