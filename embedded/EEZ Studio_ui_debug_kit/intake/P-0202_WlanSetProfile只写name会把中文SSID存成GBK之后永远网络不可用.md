# P-0202 · WlanSetProfile 只写 <name> 会把中文 SSID 存成 GBK，之后永远"网络不可用"

- **工程**：app-wifi-scan-conn-no-flow（PC 真接口）
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：wlanapi,profile,SSID,编码,中文,连接失败
- **关联提示词**：PR-0372

## 现象（看到什么）

某个中文 SSID 的网络"总是连接失败"：Windows 2 秒内报
`8002 失败原因:特定的网络不可用，RSSI 255`，通知里是「连接失败，因为无可见连接接入点」。
同一份代码连别的网络正常；空口扫得到该 SSID 的 4 个 BSS；`netsh wlan connect`（app 全关）同样失败；
用原密钥重建 profile 也失败。查了很久都是"环境问题"的假象。

## 复现（怎么稳定重现）

对一个中文 SSID 用 `WlanSetProfile` 写只含 `<name>` 的 profile XML → 连接 → 必现。

## 根因（真正的原因）

`netsh wlan export profile ... key=clear` 后看 XML 的 `<hex>`：

```
<hex>594A542D31 BAC5C2A5B0ECB9AB 2032</hex>   ← 「号楼办公」是 GBK 字节，末尾还有个 " 2"
```

而空口广播的是 UTF-8：`…31 e58fb7 e6a5bc e58a9e e585ac`。
也就是说 **profile 的 SSID 字节与空口字节不是同一个东西**，驱动里自然"没有可见接入点"。
Windows 在只有 `<name>` 时会按 ANSI 码页把名字转成 SSID 字节——中文 SSID 必踩。
（同一个坑还解释了：WLAN 通知里的 `dot11Ssid` 也是 ANSI 字节，13 vs 17 字节。）

## 修复（做了什么）

profile XML 里同时写 `<hex>`，内容直接取 `WLAN_BSS_ENTRY` 里空口抓到的原始 SSID 字节：

```xml
<SSIDConfig><SSID><hex>594a542d31e58fb7…</hex><name>YJT-1号楼办公</name></SSID></SSIDConfig>
```

修完 `8001 已连接`、协商 AES-CCMP、`netsh` 回读 SSID/通道正确，app 点击路径 4.2 秒连上。

## 证据（数字 / 命令输出）

`Get-WinEvent … Id 8001`（成功）取代了连续多次 `8002`；
`[REACH] connect 目标=YJT-1号楼办公 文案=已连接 YJT-1号楼办公`，
`netsh wlan show interfaces` → `状态: 已连接 / SSID: YJT-1号楼办公 / 通道 36`。

## 沉淀（新增断言 / 案例 / 文档）

- 写 WLAN profile 时**凡是非 ASCII SSID 一律用 `<hex>`**，`<name>` 只当显示名；
  判断"配上了没有"就看导出 XML 的 `<hex>` 是否等于空口字节。
- profile 名 ≠ SSID（重名会存成「SSID 2」）→ 连接/删除要用 `WlanGetProfileList` + 各 profile XML
  里的 SSID 建立对照，别拿 SSID 当名字。
- 排障顺序也要记：先 `netsh wlan export profile` 看 `<hex>`，比盲猜信号/驱动快一百倍。
