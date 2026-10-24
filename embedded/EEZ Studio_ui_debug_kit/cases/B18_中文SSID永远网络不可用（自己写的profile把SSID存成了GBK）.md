# B18 中文 SSID 永远「网络不可用」——自己写的 WiFi profile 把 SSID 存成了 GBK

## 现象

- 真接口（wlanapi）下点某个中文 SSID 的「已保存」网络，**每次都失败**：标题栏
  「连接失败 X（特定的网络不可用）」，Windows 事件 `8002` 在 **2 秒**内给出
  `失败原因:特定的网络不可用，RSSI: 255`；伴随 `无可见连接接入点`。
- 空口明明扫得到这个 SSID 的 4 个 BSS（-70～-85 dBm 抖动）。
- 同一份代码、同一网卡连别的网络（`yjt_dev_2.4G`）**能成功**（事件 `8001`）。
- 关掉应用用 `netsh wlan connect name="<SSID>"` 单连：**同样失败**。用原密钥重建 profile：**还是失败**。

## 证据

导出 profile 的 XML（`netsh wlan export profile name="<SSID>" folder=<dir> key=clear`）：

```
旧 profile 的 <SSID><hex>：594A542D31 BAC5C2A5B0ECB9AB 2032
空口广播的原始字节      ：594a542d31 e58fb7 e6a5bc e58a9e e585ac
```

「号楼办公」四个字：profile 里是 **GBK**（BAC5 C2A5 B0EC B9AB），空口是 **UTF-8**；
profile 的 SSID 末尾还多了 `20 32`（空格 + "2"）。另外 `netsh wlan show profiles` 里
这条叫「YJT-1号楼办公 **2**」——**profile 名 ≠ SSID**。

修复后同一路径：

```
[WIN] WlanConnect 已下发：YJT-1号楼办公
[REACH] connect 目标=YJT-1号楼办公 文案=已连接 YJT-1号楼办公   （4.2 秒）
事件 8001 成功；netsh 回读 状态: 已连接 / SSID: YJT-1号楼办公 / 通道 36
```

## 曾经的误判

误判成**信号/AP/驱动问题**，理由看着很充分：

1. 信号确实在 -70～-85 dBm 抖动，且同机房另一条网络能连；
2. 事件日志只说"网络不可用"，不说密码错；
3. **`netsh` 单连（应用全关）也失败**——这条最误导：本以为是"脱离我们的代码也失败 ⇒ 环境问题"，
   实际上 `netsh` 用的也是**同一个坏 profile**。

推翻它的关键证据是导出 XML 看 `<hex>`：profile 存的 SSID 字节与空口字节不同。
顺着这条线还发现：WLAN 通知回调里的 `dot11Ssid` 也是 ANSI 字节（13 字节 vs 空口 17 字节），
我们拿字节比对认领通知，同样永远不相等。

## 真因

`WlanSetProfile` 的 profile XML 只给 `<SSID><name>` 时，**Windows 按系统 ANSI 码页
（本机 GBK）把名字转成 profile 的 SSID 字节**。中文 SSID 于是与空口广播的 UTF-8 字节不一致，
驱动再也匹配不到 BSS ⇒ 2 秒内"无可见接入点"。

第二条独立成因：**profile 名不一定等于 SSID**（同名冲突时存成「SSID 2」）。我们原来一律
拿 SSID 文本当 profile 名去 `WlanConnect`/`WlanDeleteProfile`，名字对不上同样报"网络不可用"，
并且"已保存"判断也会飘。

## 修法

1. profile XML 里**同时写 `<hex>`**，内容直接取 `WLAN_BSS_ENTRY.dot11Ssid` 的原始字节：

```xml
<SSIDConfig><SSID><hex>594a542d31e58fb7e6a5bc…</hex><name>YJT-1号楼办公</name></SSID></SSIDConfig>
```

2. 用 `WlanGetProfileList()` + 逐个 `WlanGetProfile()` 读 XML 里的 SSID，建
   「profile 名 ↔ SSID」对照表；`saved`、连接、忘记都用表里的**真实 profile 名**。
3. 认领通知按 `strProfileName`（宽字符）比，不按 `dot11Ssid` 字节比。
4. 没有 profile 的开放网络也要先建 profile（`authentication=open` / `encryption=none`，同样带 `<hex>`）。

## 验证

- `netsh wlan export profile … key=clear` → XML 的 `<hex>` 与空口字节逐字节相同；
- 连接后 `Get-WinEvent … WLAN-AutoConfig` 出现 `8001`（成功），`netsh wlan show interfaces`
  回读 SSID/通道正确；
- app 点击路径打 `[REACH] connect … 文案=已连接 X`，4～5 秒完成；
- 无头门禁 `[NAV] PASS 47 / FAIL 0`、`preflight --skip-cli --with-sim` 全绿。

## 通用化

- **跨 API 传同一个标识必须确认字节形态**：SSID 在信标里是原始字节（本次 UTF-8），
  在 profile XML 里可能被按 ANSI 转码，在通知里又是另一种编码。凡是"名字 ↔ 标识"的转换，
  能用字节就用字节（`<hex>`），实在不行用双方都规范化过的字段（profile 名）。
- 排障次序：**先看系统自己存的数据**（`export profile` 的 `<hex>`），再看事件原因码，
  最后才怀疑硬件/信号。能被三个独立工具（应用、netsh、重建 profile）同时复现的失败，
  最容易误判成"环境"，因为它们可能共用同一份坏数据。
