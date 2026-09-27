# CH571（CH57x）BLE 设备 ID：滚码 NV 格式、控制台/BLE 写法与校验

> 适用：沁恒 CH573/CH57x + WCH BLE 协议栈（SimpleProfile 0xFFF0 / 0xFFF6）
> 来源工程：01KJN2601001（跨境手持白癜风治疗仪 BD1，`OnlyUpdateApp_Peripheral - V1.0.5`）
> 目标：把「设备 ID/滚码写 NV + 控制台查写 + BLE 查写 + 帧校验」这套做法固化下来，方便在后续项目照搬。

## 结论先行

设备标识只占 DataFlash 偏移 `0x100` 那一页的前 6 字节，用「序列号(小端2B) + 版本(1B) + 日期(年月日3B)」编码。三条写入通道（脱机烧录器滚码 / 控制台 `id` / BLE `0xF4`）写的是同一份数据。量产主通道是脱机烧录器滚码；BLE 走整帧 XOR 校验，**尾字节必须随 ID 逐帧重算**，照抄固定帧会失败。

## 1. NV（DataFlash）地址布局

| 偏移（DataFlash 相对） | 绝对地址 | 用途 | 粒度 |
|---|---|---|---|
| `0x0100` | `0x70100` | 设备标识（本方案，只用前 6 字节） | 256 B 页 |
| `0x0200` | `0x70200` | 电池旧数据 | 256 B 页 |
| `0x0300` | `0x70300` | 时长记忆（UVB 记录 8 字节） | 256 B 页 |
| `0x7000` | `0x77000` | OTA 标志 | — |
| `0x7E00` | `0x77E00` | BLE SNV（绑定信息） | — |

- `EEPROM_*` 宏（见 `SRC/StdPeriphDriver/inc/ISP573.h`）以 **DataFlash 相对地址**为准；绝对地址 = `0x70000 + 偏移`（`FLASH_ROM_MAX_SIZE = 0x70000`）。
- 擦除粒度 `EEPROM_PAGE_SIZE = 256`。`0x100 / 0x200 / 0x300` 各占一整页，天然互不覆盖——选地址时按页对齐即可。
- 脱机烧录器配置滚码时，目标写 DataFlash 偏移 `0x100` 这 6 个字节。

## 2. 6 字节设备标识格式

| 字节 | 含义 | 说明 |
|---|---|---|
| `[0..1]` | 序列号 uint16 | **小端**：低字节在前 |
| `[2]` | 版本 | 1 位十六进制参与命名 |
| `[3..5]` | 日期 | 年 / 月 / 日，各 1 字节 |

滚码字符串按字节顺序直写：
`01000A260704` → `01 00`（序号 1）`0A`（版本）`26 07 04`（2026-07-04）。

## 3. 设备名生成规则

模板：`20YYMMDD_<型号>%01X<序号%05d>`

```c
sprintf(out, "20%02x%02x%02x_%s%01X%05d",
        raw[3], raw[4], raw[5], UVB_DEVICE_NAME_TYPE,
        raw[2], *(uint16_t *)(&raw[0]));
```

- `01000A260704` + 型号 `BD1` → `20260704_BD1A00001`
- 有效性判定：`raw[0] == 0xff || raw[0] == 0` → 回退 `NODEV`

## 4. 三种写入方式

### 4.1 脱机烧录器滚码（量产主通道）

- 在烧录器的「滚码/序列号」里，对 DataFlash 偏移 `0x100` 写 6 字节，每片序列号 +1。
- 布局见第 2 节；**建议序列号从 1 开始**（原因见第 6 节注意点 1）。

### 4.2 控制台 `id` 命令

前提：`BOARD_CFG_SHELL_ENABLE == 1`（调试/中试构建默认开；release 强制关），走 USB CDC 虚拟串口。

```
id                  // 查询 → id: 20260704_BD1A00001  或  id: NODEV
id 01000A260704     // 设置（12 位 hex，顺序同滚码）
                    // 回显 id set: 20260704_BD1A00001 (hex: 01000A260704)
```

- 其他命令：`help` / `info` / `reboot` / `free`。
- 实现：`SHELL_EXPORT_CMD(... id, cmd_id, get/set device id (flash 0x100))`；内部调 `Uvb_DeviceIdWrite()`：擦整页 → 写 6 字节 → 读回 `memcmp` 核验。

### 4.3 BLE `0xF4` 命令

- 服务 `0xFFF0`，写特征 **`0xFFF6`**（不是 `0xFFF1`，FFF1 只支持 1 字节）。
- 设备必须**开机（非 OFF）且已连接**；建议用 **Write Request** 才能读到 ATT 错误码。
- 帧（12 字节）：`00 seq 0C 00 F4 <6B 标识> XOR`
- 示例：`00 01 0C 00 F4 01 00 0A 26 07 04 D7` → 写入 `01 00 0A 26 07 04`
- 返回 `SUCCESS` 表示写入并读回核验成功；失败：`0x0D`（长度/校验错）/ `0x0E`（状态或存储失败）。

## 5. BLE 帧校验（XOR）——本方案重点

`Uvb_ValidFrame` 的规则：

- 长度 `6 ~ 20`；`data[0] == 0`（PCB 固定 0）；`declared == len`；**`Uvb_Xor(整帧) == 0`**。
- 即：**尾字节 = 前面 (len-1) 字节逐字节异或**。

量产写 ID 时 ID 会变，尾字节也跟着变，必须**逐帧重算**：

| 滚码 | 完整帧（可直接写入 FFF6） |
|---|---|
| `00000A260704` | `00 01 0C 00 F4 00 00 0A 26 07 04 D6` |
| `01000A260704` | `00 01 0C 00 F4 01 00 0A 26 07 04 D7` |
| `02000A260704` | `00 01 0C 00 F4 02 00 0A 26 07 04 D4` |

计算方式：

```c
uint8_t x = 0;
for (i = 0; i < len - 1; i++) x ^= frame[i];
frame[len - 1] = x;   /* 使整帧异或为 0 */
```

> 只要改动 6 字节标识里的任意一字节，末字节 XOR 一定会变；复用固定帧会直接返回 `0x0D`。

## 6. 踩坑与校验注意点

1. **有效性只看 `raw[0]`**：`raw[0] == 0x00` 会被当成未烧录 → 名字显示 `NODEV`。因此序列号低字节为 0（第 0 片、第 256 片……）会被误判。建议序列号从 1 开始；更稳的做法是「只有全 `0xFF` 才算空」。注意 `board_config.h` 里 `seq = 0` 的示例实际会得到 `NODEV`，文档与实现不一致。
2. **广播名只在开机时生成**：`Peripheral_Init` 里调一次 `Uvb_DeviceNameGet` 填 GAP 名和扫描响应。用 `id`/`0xF4` 写完，flash 变了但广播名不变，**必须复位才生效**；控制台 `id` 打印的是「即时读回值」，不代表广播名已更新。
3. **写错特征**：FFF1 长度 1 字节，写 12 字节帧会被拒；一律写 FFF6。
4. **必须 Write Request**：Write Without Response 拿不到 `0x0D/0x0E`，容易误判写成功。
5. **版本字节 > `0x0F` 会加长名字**：`%01X` 只是最少 1 位，版本 ≥ `0x10` 时名字位数变化，扫描响应长度跟着变，注意 `memcpy(&scanRspData[2], attDeviceName, 18)` 与 `scanRspData[0]` 的同步。
6. **序列号溢出**：`%05d` 只保证 5 位，序号 > 99999 名字会变长。
7. **release 没有 `id` 命令**：`BOARD_CFG_RELEASE=1` 时 `BOARD_CFG_SHELL_ENABLE=0`，重写只能靠滚码或 BLE `0xF4`。

## 7. 迁移到新项目的清单

1. 选一个独立 DataFlash 页放 ID（避开 SNV/OTA/其他 NV），定义 `XXX_DEVICE_ID_ADDR` / `XXX_DEVICE_ID_BYTES`。
2. 写一份统一的 `DeviceIdWrite()`：擦整页 → 写 → 读回 `memcmp` 核验；三条通道共用，避免各写一份。
3. 名字模板集中到 `DeviceNameGet()` 一处，在 `Peripheral_Init` 填 GAP 名 + 扫描响应。
4. 控制台用 `SHELL_EXPORT_CMD` 导出 `id` 命令（查询/设置共用）。
5. BLE 在命令分发里加 `0xF4` 分支（12 字节，取 `data+5` 起 6 字节）；顺序是「先过帧校验 → 再判开关机态 → 再写」。
6. 烧录器滚码配置对齐 6 字节布局，序列号从 1 开始。
7. 主机单测补一条：构造合法帧（自带正确 XOR）→ 写 → 读回比对 → 再改一次验证可重复改写。

## 8. 参考代码位置（01KJN2601001）

- `BLE - newNack/OnlyUpdateApp_Peripheral - V1.0.5/APP/userNVDataHandle.c`：地址宏、`Uvb_DeviceIdWrite`、`Uvb_DeviceNameGet`、`cmd_id`
- `.../APP/user_communication.c`：`Uvb_Command` 中的 `0xF4` 分支
- `.../APP/include/board_config.h`：型号宏、滚码与完整帧示例
- `.../APP/peripheral.c`：`Peripheral_Init` 填 GAP 名与扫描响应
- `.../Profile/gattprofile.c`：FFF6 写回调 → `Uvb_Command` 入口
- `.../APP/knead_user.c`：`Uvb_Xor` / `Uvb_ValidFrame`
- `.../SRC/StdPeriphDriver/inc/ISP573.h`：`EEPROM_READ/WRITE/ERASE`、`EEPROM_PAGE_SIZE`