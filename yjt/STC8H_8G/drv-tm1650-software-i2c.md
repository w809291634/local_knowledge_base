# STC8 + TM1650 数码管：为什么必须软件 I2C，以及影子寄存器/逐位验证做法

> 适用：STC8G/8H + TM1650（及一切"准 I2C"两线接口、寄存器只写不可读的显示类芯片）
> 来源工程：STC8G_8H_SDK（common/drv/drv_tm1650，2026-08-05 加入，08-06 从 apl 挪到 drv 并由硬件 I2C 改软件 I2C）
> 目标：固化 TM1650 驱动的选型结论、帧协议、影子寄存器设计和上机验证方法。

## 结论先行

TM1650 **不能用硬件 I2C 外设**（实测固定时序对不上这种"准 I2C"芯片，不亮），也不能用库的 `I2C_WriteNbyte`（三段式协议对不上），必须用 `STC8G_H_Soft_I2C` 底层原语自拼 **2 字节定长帧**。寄存器只写不可读 → 本地影子寄存器记一份再读-改-写。段码表/走线未上机验证的假设，用 `TM1650_SegBitTest()` 逐位点亮核对。

## 1. 选型排除记录

| 方案 | 结论 | 原因 |
|---|---|---|
| 硬件 I2C 外设（drv_i2c） | ❌ 实测不亮 | 硬件 I2C 固定时序与 TM1650 的"准 I2C"时序对不上 |
| 库函数 `I2C_WriteNbyte/I2C_ReadNbyte` | ❌ 协议不匹配 | 库函数固定"设备地址+寄存器地址+数据"三段式，寄存器地址总会发出；TM1650 帧是"地址字节后直接接数据"，没有寄存器地址 |
| 软件 I2C 原语自拼帧 | ✅ 采用 | `I2C_Start/WriteAbyte/Check_ACK/Stop` 自由拼帧，时序自己可控 |

依赖关系：`drv_tm1650` 依赖 `BOARD_CFG_STC8G_H_LIB_ENABLE_SOFT_I2C`（不是 drv_i2c），已在 board_config.h 静态检查区块强制。TM1650 自带按键扫描不做（本工程按键走 GPIO + drv_inputex_lite）。

## 2. 帧协议

```
[Start] 地址字节 数据字节 [Stop]
```

- 控制命令地址 `0x48`，数据字节 = `(亮度<<4) | 开关位`
- 4 位数码管地址：`0x68 / 0x6A / 0x6C / 0x6E`（第 1~4 位）
- 段码 bit0~6 = a~g，bit7 = dp

```c
static void tm1650_write2(uint8_t addr, uint8_t dat)   /* 形参叫 dat 不叫 data（C51 关键字） */
{
    uint8_t nak = 0;
    I2C_Start();
    I2C_WriteAbyte(addr);
    I2C_Check_ACK();          /* 结果在 F0: 0=应答, 1=没应答 */
    if (F0) nak |= 0x01u;
    I2C_WriteAbyte(dat);
    I2C_Check_ACK();
    if (F0) nak |= 0x02u;
    I2C_Stop();
    s_last_nak = nak;         /* 记录 NAK 位, GetLastNak() 供诊断 */
}
```

## 3. 影子寄存器（只写不可读的通用解法）

控制字节和段码寄存器都**只写不可读**，凡"只改其中一部分"的操作必须本地记影子：

- `s_brightness` / `s_on`：`SetBrightness`/`DisplayOnOff` 改影子后统一重发控制字节；
- `s_digit_seg[4]`：`SetSegBit(pos, bit, on)` 基于影子做 `|=`/`&=~` 再整字节写回——不做影子就丢掉其余 7 段的状态；
- `SetDigit` 写段码时同步刷新影子，保证后续 `SetSegBit` 基于最新值。

**中断限制**：所有接口只允许应用层（主循环）调用。软件 I2C 时序和影子读-改-写都依赖连续执行，中断里调用可能被打断导致时序错乱或显示不一致；显示刷新统一走应用层汇总入口。

## 4. 上机验证工具（驱动自带）

- `TM1650_Test(step_ms)`：4 位同步 0~9 循环 + DP 按 1/4 周期闪烁。DP 做成闪烁而不是常亮，是为了同时验证"能点亮"和"能熄灭"（常亮只验得出前一半）。
- `TM1650_SegBitTest(pos, wait_ms)`：第 pos 位逐个 bit 单点点亮。用途：TM1650 可能驱动的不是标准 7 段管而是分组 LED，逐位跑一遍确认哪个 bit 对应哪颗灯。

**遗留未验证假设（接入新硬件时必做）**：控制字节格式、段码地址、共阴段码表来自第三方资料交叉印证；亮度"数值越大越亮"的方向可能因批次/克隆芯片而异——上机先用 `TM1650_SetBrightness()` 跑 0~7 确认单调性，再核对段码表与实际走线。

## 5. 配置归属

TM1650 开关和默认亮度没有引脚选择（软件 I2C 的 SDA/SCL 引脚宏在 board_config.h "Driver pin config" 区由 Soft_I2C 模块配置），所以整块放"库用户驱动配置"区，不拆 pin 区——分区判断标准见 `board-config-three-layer-switches.md`。
