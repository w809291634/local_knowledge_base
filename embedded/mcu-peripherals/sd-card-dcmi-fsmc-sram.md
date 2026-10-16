# SD 卡 / 摄像头 DCMI / 外部 SRAM（FSMC-FMC）

## 1. SD 卡容量与卡型判别（通用）

| 项 | 内容 |
|---|---|
| 容量分代 | SDSC 0~2G、SDHC 2~32G、SDXC 32G~2T；**F4 只支持 SD2.0 ⇒ 最大 32GB** |
| 卡型判别 | 无 CMD1 有 CMD55 = SD；有 CMD1 无 CMD55 = MMC；CMD8 分 SD 1.1/2.0；ACMD41 分 SDSC/SDHC |
| 命令帧 | **48 位**：start(0) + trans(1) + idx(6) + arg(32) + **CRC7** + end(1) |
| 时钟 | `SDIO_CK = SDIOCLK / (2 + CLKDIV)`；**初始化阶段 ≤ 400kHz**；F4 的 SDIOCLK = 48MHz 固定 |
| 关键 CMD | CMD0 无响应；CMD8→R7；CMD2→R2；CMD9→R2；CMD16→R1；CMD17→R1；CMD18→R1；CMD12→R1b；CMD24→R1；CMD25→R1；ACMD41→R3。`⚠校核C`：**CMD13 SEND_STATUS 实为 R2，文档标成 R1** |
| 超时 | CMD 响应超时 = **64 个 SDIO_CK** |
| 响应寄存器 | 短响应 → `RESP1` = 卡状态[31:0]；长响应 → `RESP1..4` = [127:96]/[95:64]/[63:32]/[31:1]0b。`⚠校核`："RESP3 LSB 恒为 0b"疑应指 RESP4 |
| 寄存器位 | `CLKCR`：WIDBUS[12:11]、CLKDIV[7:0]；`CMD`：WAITRESP[7:6]、CMDINDEX[5:0]；`DCTRL`：DBLOCKSIZE[7:4] = 2^n；`DLEN[24:0]` 须为块长整数倍 |
| **SPI 模式下的 SD** | 6 字节命令**全部要带 CRC**；固定值：`CMD0 = 0x95`、`CMD8(arg=0x1AA) = 0x87`；`CRC_ON_OFF = CMD59`；**很多 TF 卡不支持 SPI 模式**（买卡要先验） |
| SDIO vs SPI | SDIO 走 1/4 位宽 + DMA（`SDIO = DMA2_Stream3_Ch4`）；SPI 模式简单但慢、且 CRC 逻辑不同 |

## 2. 摄像头 OV2640 + DCMI（F4）

| 项 | 内容 |
|---|---|
| OV2640 规格 | 1/4 寸 UXGA，阵列 1632×1232，**输出最大 1600×1200**；UXGA 15fps / SVGA 30fps / CIF 60fps；`XCLK` 典型 **24MHz**，`PCLK` 最高 **36MHz**；**SCCB 兼容 IIC** |
| 镜像/翻转 | 寄存器 `0x04`：bit7 镜像、bit6 垂直翻转。`⚠校核`："0x04=0x58 垂直翻转"含额外 `VREF[0]` 位，注释未说明 |
| **缩放坑（必记）** | `ImageWin` / `OutSize` 的**宽高必须是 4 的倍数**，否则花屏；相关寄存器 `0x51/0x52/0x53/0x54/0x55/0x57`(窗口)、`0x5A/0x5B/0x5C`(输出) |
| DCMI 接口 | 8/10/12/14 位并行，可达 **54MB/s**；**8 位模式下 4 个 PCLK 才存满一个 32 位字，低字节在前**；`CR` 里有 `PCKPOL/HSPOL/VSPOL` 极性位（接错极性=全黑或撕裂） |
| DMA | `DCMI = DMA2_Stream1_Ch1`。`⚠校核C`：文档另一处 H743 例子写成 `DMA1_Stream1 + DMA_FLAG_TCIF1_5` 且头文件是 `stm32f7xx_hal.h` ⇒ 代码是拼接的，照抄前要对齐代际 |
| JPEG 判界 | 码流以 `0xFF,0xD8` 开头、`0xFF,0xD9` 结尾（分包/丢帧判断就靠这两个标记） |
| 图像处理 | `RGB565` 是 5-6-5 位域；`⚠校核C`：文档的 `rgb565_to_y800` 直接把 5/6/5 位宽的 r,g,b 乘 299/587/114，**权重是按 8 位通道设计的，未先 <<3 归一 ⇒ 灰度比例失真** |

## 3. 外部 SRAM 与 FSMC/FMC 映射

| 项 | 内容 |
|---|---|
| Bank 映射 | Bank1 四个区各 64MB（共 256MB，对应 `HADDR[27:0]`）；`BANK1/2/3/4 = 0x6000_0000 / 6400_0000 / 6800_0000 / 6C00_0000` |
| 地址线接法 | 16 位设备：`HADDR[25:1] → FSMC_A[24:0]`；**FSMC_A[0] 恒接外部 A0**；`HADDR[0]` 用来控制 `NBL0/NBL1` 字节选通 |
| 时序参数范围 | `ADDSET 0~15`、`ADDHLD 1~15`、`DATAST 1~256`、`BUSTURN 0~15`、`CLKDIV 2~16`、`DATLAT 2~17`；SRAM 用 **Mode A** |
| IS62WV51216 | 512K×16 = 1MB；**19 根地址线 + 16 根数据线**；45/55ns；`BLL` 2.5~3.6V；**全静态、免刷新**；UB/LB 字节控制 |
| 换算坑 | `⚠校核C`：文档"1/168M = 6ns×16 = 96ns""DATAST=0x06 ⇒ 8 个 HCLK = 6ns"把**周期与周期数混用**（168MHz ≈ 5.95ns/周期；ADDSET=0 是 0 周期；DATAST=6 ≈ 36ns）。自己算时按 `周期数 × t_HCLK` |
| 与 GD32 的交叉坑 | GD32 上用 STM32 库驱动 FSMC LCD 时 `FSMC_DataSetupTime=0` 会**刷屏很慢**，要改成 ≥1（详见 `mcu-chip-families/gd32.md`） |

## 4. H7 的缓存与 DMA（这条不属于某个外设，但踩坑代价最大）

- **只有 Normal 内存可 cache，TCM 不可 cache**；D-Cache 16KB = 512 线 × 32B / 4-way。
- **DMA 缓冲区要么设为 NonCache，要么收发前后 `SCB_CleanInvalidateDCache()`**；
  实测 DCMI 画面撕裂：Write-Through 30FPS vs Non-Cache 15FPS。
- **DMA 不能访问 DTCM** ⇒ 双缓冲的 buf 别放 DTCM。
- 高主频下 WT 透写会出问题、降到 400MHz 就正常（作者注"原因不明"，**未验证**）。
- `⚠校核`：`SCB->CACR |= 1<<2` 被文字说成"开启强制透写"，但 CM7 透写位是 bit0(EWCT)。

## 5. 使用建议

| 需求 | 先看 |
|---|---|
| TF 卡读不出来 | 先确认卡是否支持 SPI 模式；再查 CMD8/ACMD41 判别序列与 400kHz 初始化时钟 |
| 摄像头花屏 | 先查 `ImageWin/OutSize` 是否 4 的倍数，再查 `PCKPOL/HSPOL/VSPOL` 极性 |
| 外扩 SRAM/LCD 慢 | 查 `DATAST/ADDSET` 的周期数换算，别抄文档的 ns 结论 |
| H7 上 DMA + 显示/图形异常 | 先怀疑 cache 策略，再怀疑时序 |
