# P-0193 · qsort 之后仍拿指向数组槽位的指针读字段，状态文案写成另一个网络

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：悬垂指针,排序,qsort,状态文案,断言口径
- **关联提示词**：PR-0363、PR-0364

## 现象（看到什么）

无头导航日志里，点「开放网络 Office-2G」直连之后打的是 `[IO] connected: 1号楼6层WiFi (saved=0)`，
标题文案也会写成「已连接 1号楼6层WiFi」——连的是 A，报的是 B。
状态位本身是对的（`wifi_ap_at()` 全表遍历只有一个 connected），所以只看状态断言发现不了。

## 复现（怎么稳定重现）

`io_wifi_connect()` 里把重排后的 `ap->ssid` 用回文案与日志（`snprintf(buf, ..., "已连接 %s", ap->ssid)`），
重编重跑 `WIFI_NAVTEST=1`：`[NAV] FAIL 状态文案点名「已连接 <这条 SSID>」`、rc=1，
且 `[IO] connected:` 行的 SSID 与被点的行不一致。

## 根因（真正的原因）

`ap = find_ap(ssid)` 返回的是 `&s_aps[i]`；紧接着 `resort_and_publish()` 里 `qsort` 把整个数组搬家，
同一个槽位换住别的网络。函数尾部（文案 + printf）在重排**之后**读 `ap->ssid`，读到的就是搬过来占这个
槽位的另一个 AP。为什么容易踩：指针在改动前有效、改动后仍然"能读"，不会崩，只是值串台；
断言若只查"是否含『已连接』"就完全放过。

## 修复（做了什么）

`platform/pc/wifi_platform_pc.cpp`：`io_wifi_connect()` / `io_wifi_forget()` 在调用
`resort_and_publish()` **之前**把 `ap->ssid` 抄进局部 `char target[sizeof(ap->ssid)]`、
把 `ap->saved` 抄进 `int now_saved`，之后的文案与日志只用局部变量；并在代码里写明这条约束。

## 证据（数字 / 命令输出）

修复后 `[IO] connected: Office-2G (saved=0)`、`[IO] forgotten: yjt_dev_2.4G`，
`[NAV] RESULT: PASS 30 / FAIL 0`（连跑 3 次一致）；反向测试（改回 `ap->ssid`）rc=1 且点名一条 FAIL。

## 沉淀（新增断言 / 案例 / 文档）

断言口径收紧：状态文案必须**点名到目标 SSID**（`strstr(文案, "已连接 " + s_target)`），不再只查关键字；
用例目标一律按 SSID 认行（`row_of_ssid`），因为连接/忘记都会重排，缓存行号必错。
工程侧落档：`EEZ_WORKFLOW.md` §5.7。
