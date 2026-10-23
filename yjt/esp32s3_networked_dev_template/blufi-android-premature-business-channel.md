# ★ Android BluFi 配网：BLE 刚连接就发送业务 JSON 会破坏配网时序

> 适用：`esp32s3_networked_dev_template`（ESP-IDF v5.3.1、Bluedroid BluFi、Android App 复用 BluFi 私有数据通道）。
>
> 来源：`esp32s3_networked_dev_template` 对照 `potential_therapy_dev_dw2`，2026-10-23；已完成完整 ESP-IDF 构建。

## 症状

Android 手机连接后，设备紧接着打印一条 `d2uRealData` 的 BLE 发送日志，随后出现：

```text
W (...) BT_GATT: attribute value too long, to be truncated to 20
```

Android 端无法继续 BluFi 配网；iOS 与成熟工程 `potential_therapy_dev_dw2` 正常。该轮日志中没有后续标准配网事件：`SET_WIFI_OPMODE`、`RECV_STA_SSID`、`RECV_STA_PASSWD`、`REQ_CONNECT_TO_AP`。

## 结论：先分清「BLE 已连」与「业务通道已就绪」

`ESP_BLUFI_EVENT_BLE_CONNECT` 仅代表 GATT/BluFi 的物理连接已建立，**不能**据此开始发送产品业务 JSON。

成熟工程的行为是：

```text
BLE_CONNECT
  -> ble_is_connected = true
  -> 等 Android 完成 BluFi 配网/安全协商并下发自定义业务命令 RDStart
  -> ifblufibleconnect = BLE_CONNECT_PRIORITY_H
  -> 发送 reg、d2uRealData 等业务报文
```

模板工程曾在 `ble_app_on_ble_connect()` 直接写入
`sys_parm.ifblufibleconnect = BLUFI_BLE_CONNECT`。`task_sysmain` 每 100 ms 检测到该状态变化后会置 `yjt_send_d2u_parm`，从而在 Android 尚未完成 BluFi 交互时，立刻发送约百字节的 `d2uRealData`。

这条主动数据会与 Android 的 BluFi 配网时序冲突；本轮还恰好触发 ATT 层将通知截断为 20 字节，使客户端无法正确解析/重组，最终不再下发 Wi-Fi 凭据。

## 最小修复

在 `main/app/blufi_app.c:ble_app_on_ble_connect()`：

- 不写 `sys_parm.ifblufibleconnect`；
- 仅记录 BLE 已连接；
- 保留 `ble_parse()` 内收到 `op == "RDStart"` 时设置
  `BLE_CONNECT_PRIORITY_H` 的逻辑，由它开启业务通道。

对应头文件注释也要同步为“业务通道由 RDStart 打开”。该改动与 `potential_therapy_dev_dw2` 的行为一致。

## 判据与复测

修复后，Android 配网开始阶段的日志顺序应是：

```text
BLUFI ble connect
BLE connected; wait RDStart before business channel
... Android 的 BluFi 安全协商 / Wi-Fi 配置事件 ...
set opmode / recv sta ssid / recv sta pwd / sta connect req
```

在 `RDStart` 前，**不得**出现 `BLE App` 的 `d2uRealData`、`reg` 或其他产品业务 JSON。若仍有 `attribute value too long, to be truncated to 20`，需同时记录该报文类型、长度与 RDStart/MTU 事件先后关系。

## 不要误判为工程配置差异

两工程的 BluFi 安全协商、`esp_blufi_send_custom_data()` 发送接口与 BT/BluFi sdkconfig 项均等价，且都未调用 `esp_ble_gatt_set_local_mtu()`。因此“本地 MTU 未显式扩大”是两工程共有的潜在可靠性风险，**不能单独解释**为何只有模板工程在 Android 配网阶段失败。

如果业务阶段仍发送大包并重现 20 字节截断，再单独验证本地/对端 MTU 协商，并评估设置本地 GATT MTU；不要把该增强与本条时序修复混为一项。
