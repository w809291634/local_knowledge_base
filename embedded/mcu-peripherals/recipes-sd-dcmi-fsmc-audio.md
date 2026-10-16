# 代码配方：SD 卡 / OV2640+DCMI / FSMC SRAM / I2S 音频（照抄原文）

> 配套 `sd-card-dcmi-fsmc-sram.md` 与 `audio-i2s-wav.md`，行号指原文导出文本位置。
> **本篇特别重要**：多处流程在原文里**只有文字或截图、没有代码**，已逐条标 `原文无代码`，
> 以免以后误以为"库里有现成实现"。

## 1. SD 卡：SDIO 方式

### 1.1 时钟与上电 + CMD0 + CMD8（17d:1290/1302 | F4）
```c
SDIO_InitStructure.SDIO_ClockDiv   = SDIO_INIT_CLK_DIV;  /* SDIOCLK=48M ⇒ 48/(118+2)=400kHz，初始化必须 ≤400k */
SDIO_InitStructure.SDIO_ClockEdge  = SDIO_ClockEdge_Rising;
SDIO_InitStructure.SDIO_BusWide    = SDIO_BusWide_1b;    // 初始化阶段先 1 位
SDIO_Init(&SDIO_InitStructure);
SDIO_SetPowerState(SDIO_PowerState_ON);  SDIO->CLKCR |= 1<<8;      // ← 使能 SDIO_CK
for(i=0;i<74;i++){                                              // CMD0 重试 74 次（>74 个时钟）
  SDIO_CmdInitStructure.SDIO_Argument  = 0x0;
  SDIO_CmdInitStructure.SDIO_CmdIndex  = SD_CMD_GO_IDLE_STATE;  // CMD0
  SDIO_CmdInitStructure.SDIO_Response  = SDIO_Response_No;
  SDIO_CmdInitStructure.SDIO_CPSM      = SDIO_CPSM_Enable;
  SDIO_SendCommand(&SDIO_CmdInitStructure);
  errorstatus = CmdError();                                     // while(timeout--) 查 SDIO_FLAG_CMDSENT，0x00010000 次
  if(errorstatus == SD_OK) break; }
SDIO_CmdInitStructure.SDIO_Argument = SD_CHECK_PATTERN;         // CMD8 参数 0x1AA
SDIO_CmdInitStructure.SDIO_CmdIndex = SDIO_SEND_IF_COND;
SDIO_CmdInitStructure.SDIO_Response = SDIO_Response_Short;      // R7
SDIO_SendCommand(&SDIO_CmdInitStructure);
errorstatus = CmdResp7Error();                                  // 无 R7 ⇒ V1.x 卡或 MMC
```
### 1.2 ACMD41 电压协商循环（17d:1302）
```c
while((!validvoltage) && (count < SD_MAX_VOLT_TRIAL)){
  /* CMD55 */ ... SDIO_CmdIndex = SD_CMD_APP_CMD; SDIO_Response = SDIO_Response_Short; SDIO_SendCommand(...);
  errorstatus = CmdResp1Error(SD_CMD_APP_CMD);
  /* ACMD41 */ SDIO_CmdInitStructure.SDIO_Argument = SD_VOLTAGE_WINDOW_SD | SD_HIGH_CAPACITY;
             /* 0x80100000 | 0x40000000 */          SDIO_CmdIndex = SD_CMD_SD_APP_OP_COND;
  SDIO_SendCommand(&SDIO_CmdInitStructure);
  errorstatus = CmdResp3Error();
  response = SDIO->RESP1;
  validvoltage = (((response >> 31) == 1) ? 1 : 0);   // ← OCR bit31=1 才表示卡就绪
}
```
MMC 分支：不发 CMD55，改发 **CMD1**（参数 `0x80FF8000`），同样查 bit31。
`⚠校核`：**CMD2→CMD3→CMD9→CMD10→CMD7 的初始化后续在原文只有文字步骤（1169-1179 行）、代码在空表格里 ⇒ 无实现可抄**；
`SD_GetStatus`、`SDIO_ReadIdleBit`、`SD_ReadMultiBlocks` 的代码同样**原文无**（CMD18+CMD12 只有文字，1206-1216 行）。

### 1.3 单块读（CMD16+CMD17）与轮询收数（17d:1189 | F4）
```c
SDIO->DCTRL = 0x0;
if(CardType == SDIO_HIGH_CAPACITY_SD_CARD){ blksize = 512; addr >>= 9; }   // ← 高容量用块地址
/* CMD16 设块长 */ SDIO_CmdInitStructure.SDIO_Argument = blksize;
   SDIO_CmdIndex = SD_CMD_SET_BLOCKLEN; SDIO_SendCommand(...);
errorstatus = CmdResp1Error(SD_CMD_SET_BLOCKLEN);
/* 数据通路参数（DPSM） */
SDIO_DataInitStructure.SDIO_DataBlockSize = power << 4;      // ← 2^n 放到 [7:4]
SDIO_DataInitStructure.SDIO_DataLength    = blksize;
SDIO_DataInitStructure.SDIO_TransferDir   = SDIO_TransferDir_ToSDIO;
SDIO_DataConfig(&SDIO_DataInitStructure);
/* CMD17 */ SDIO_Argument = addr; SDIO_CmdIndex = SD_CMD_READ_SINGLE_BLOCK; SDIO_SendCommand(...);
INTX_DISABLE();                                    // ← 轮询模式严禁被中断打断，否则 FIFO 错
while(!(SDIO->STA & ((1<<5)|(1<<1)|(1<<3)|(1<<10)|(1<<9)))){   // 上溢/CRC/超时/传输完成/起始位错误
  if(SDIO_GetFlagStatus(SDIO_FLAG_RXFIFOHF) != RESET){
    for(count=0;count<8;count++) *(tempbuff+count) = SDIO->FIFO;
    tempbuff += 8; timeout = 0X7FFFFF;
  } else { if(timeout == 0) return SD_DATA_TIMEOUT; timeout--; } }
while(SDIO_GetFlagStatus(SDIO_FLAG_RXDAVL) != RESET){ *tempbuff = SDIO->FIFO; tempbuff++; }
```
### 1.4 DMA 版（17d:1347）
```c
SDIO->MASK |= (1<<1)|(1<<3)|(1<<8)|(1<<5)|(1<<9);   // 使能相应中断
SDIO->DCTRL |= 1<<3;                                 // ← DMA 请求使能
/* DMA 配置：DMA2_Stream3 + Channel_4、外设 &SDIO->FIFO、Word 宽、
   DMA_FIFOThreshold_Full、MemoryBurst_INC4、外设作流控制器 */
```
`⚠校核`：17d:1254 的 CMD13 标 **R1**（协议应为 **R2**）；RT-Thread 头文件 17d:1539 也写 `SEND_STATUS 13 /* R2 */`——
**同一文档两处冲突，用前先抓一次总线确认响应长度**。

## 2. SD 卡：SPI 模式（结构最简单，可移植到任何 SPI）

来源 17d:1527
```c
static int sd_send_cmd(u8 cmd, u32 arg, u8 crc){
  SD_CS_DISABLE(); sd_read_write_byte(0XFF); SD_CS_ENABLE();
  do{ retry = sd_read_write_byte(0XFF); }while(retry != 0xFF);      // ← 等卡退出 busy
  sd_read_write_byte(cmd | 0x40);                                   // 0x40 = 起始位 + 传输位
  sd_read_write_byte(arg>>24); sd_read_write_byte(arg>>16);
  sd_read_write_byte(arg>>8);  sd_read_write_byte(arg);
  sd_read_write_byte(crc);                                          // ← SPI 模式必须带 CRC
  if(cmd == CMD12) sd_read_write_byte(0XFF);                        // STOP_TRAN 后要再读一字节
  do r1 = sd_read_write_byte(0xFF); while(r1 & 0X80);                // 等 idle(bit7) 清零
  return r1; }
```
固定 CRC 值（`rt_msd_init`，17d:1559）：`CMD0 = 0x95`、`CMD8 = (0x01AA, 0x87)`（并校验回读 `response[4] == 0xAA`）、
`CMD59 CRC_ON_OFF`：开 = `0x83`、关 = `0x91`；`CMD16` 与 `CMD9` 的 crc 写 `0x00`（注释里旧值 `0xAF`）；
上电先发 **100 字节 0xFF**（>74 个时钟）。**"每条命令发送 6 次"的写法原文无代码。**
验证：能读到 CID/CSD（MID 非 0）即 SPI 模式打通；TF 卡 frequently 不支持 SPI ⇒ 先用已知支持的卡试。

## 3. OV2640 + DCMI

```c
/* 复位与识别（17d:2000/2065） */
OV2640_PWDN_H; delay_ms(50); OV2640_PWDN_L; delay_ms(10);
OV2640_RST_L;  delay_ms(50); OV2640_RST_H;  delay_ms(10);
SCCB_Init();
SCCB_WR_Reg(OV2640_DSP_RA_DLMT, 0x01);     // ← 切换到 sensor 寄存器
SCCB_WR_Reg(OV2640_SENSOR_COM7, 0x80);     // 软复位
delay_ms(50);
/* 之后读 MIDH/MIDL、PIDH/PIDL 与预期比对 */
```
`SCCB_WR_Reg` 的**时序实现代码原文无**（只有调用与手册 Figure13 图注）。
初始化 = 循环下发寄存器表：`for(i...) SCCB_WR_Reg(ov2640_sxga_init_reg_tbl[i][0], tbl[i][1]);`
系统时钟段开头（17d:2005 表）：`0xff,0x00, 0x2c,0xff, 0x2e,0xdf, 0xff,0x01, 0x3c,0x32, 0x11,0x00, 0x09,0x02, 0x04,0xD8, ...`；
XVCLK 典型 24MHz（17d:1646）。

**窗口/缩放设置（这段就是"宽高必须 4 的倍数"的出处）**，17d:1743/1749
```c
u8 OV2640_ImageWin_Set(u16 offx, u16 offy, u16 width, u16 height){
  if(width  % 4) return 1;                      // ← 不整除直接返回错误
  if(height % 4) return 2;
  hsize = width/4;  vsize = height/4;           // 单位是 4 像素/4 行
  SCCB_WR_Reg(0XFF, 0X00); SCCB_WR_Reg(0XE0, 0X04);
  SCCB_WR_Reg(0X51, hsize & 0XFF);  SCCB_WR_Reg(0X52, vsize & 0XFF);
  SCCB_WR_Reg(0X53, offx & 0XFF);  SCCB_WR_Reg(0X54, offy & 0XFF);
  temp  = (vsize >> 1) & 0X80;  temp |= (offy >> 4) & 0X70;
  temp |= (hsize >> 5) & 0X08;  temp |= (offx >> 8) & 0X07;
  SCCB_WR_Reg(0X55, temp);  SCCB_WR_Reg(0X57, (hsize >> 2) & 0X80);
  SCCB_WR_Reg(0XE0, 0X00); }
/* OutSize_Set 同构，用 0X5A / 0X5B / 0X5C；854 不合法，要 852（17d:1930） */
```
**DCMI 初始化与启动顺序**（17d:1989）
```c
DCMI_InitStructure.DCMI_CaptureMode    = DCMI_CaptureMode_Continuous;
DCMI_InitStructure.DCMI_CaptureRate    = DCMI_CaptureRate_All_Frame;
DCMI_InitStructure.DCMI_ExtendedDataMode = DCMI_ExtendedDataMode_8b;   // 8 位并行
DCMI_InitStructure.DCMI_HSPolarity     = DCMI_HSPolarity_Low;    // ← 极性照摄像头手册
DCMI_InitStructure.DCMI_PCKPolarity    = DCMI_PCKPolarity_Rising;
DCMI_InitStructure.DCMI_SynchroMode    = DCMI_SynchroMode_Hardware;
DCMI_InitStructure.DCMI_VSPolarity     = DCMI_VSPolarity_Low;
DCMI_Init(); DCMI_ITConfig(DCMI_IT_FRAME, ENABLE); DCMI_Cmd(ENABLE);
/* DMA：DMA2_Stream1 + Channel_1、外设 &DCMI->DR、PeripheralDataSize_Word、循环、FIFO Full、
        MemoryBurst_INC8 */
/* 启动：先配屏窗口，再开 DMA，最后使能采集 */
LCD_Set_Window(...); LCD_WriteRAM_Prepare(); DMA_Cmd(ENABLE); DCMI_CaptureCmd(ENABLE);  // ← CAPTURE 必须最后
/* DCMI 本身无双缓冲；帧中断里： DCMI_Stop(); ov_frame++; DCMI_Start(); */
```
`原文无代码`：**JPEG `FFD8/FFD9` 边界查找、`ov2640_fifo_init` + 帧缓冲池**都只是文字（17d:1678）；
灰度转换有代码但**权重用错**：`Gray = (r*299 + g*587 + b*114 + 500)/1000`，r/g/b 是 5/6/5 位裸值未扩到 8 位 ⇒ 偏暗
（`⚠校核`，见 ERRATA C）。

## 4. FSMC 外扩 SRAM（17d:3461/3491 | F407，RAM 挂 NE3 = `0x68000000`）

```c
SRAM_Handler.Init.NSBank          = FSMC_NORSRAM_BANK3;
SRAM_Handler.Init.DataAddressMux  = FSMC_DATA_ADDRESS_MUX_DISABLE;
SRAM_Handler.Init.MemoryType      = FSMC_MEMORY_TYPE_SRAM;
SRAM_Handler.Init.MemoryDataWidth = FSMC_NORSRAM_MEM_BUS_WIDTH_16;
SRAM_Handler.Init.BurstAccessMode = FSMC_BURST_ACCESS_MODE_DISABLE;
SRAM_Handler.Init.WriteOperation  = FSMC_WRITE_OPERATION_ENABLE;
SRAM_Handler.Init.ExtendedMode    = FSMC_EXTENDED_MODE_DISABLE;      // 读写同时序
FSMC_ReadWriteTim.AddressSetupTime      = 0x00;   // ADDSET
FSMC_ReadWriteTim.AddressHoldTime       = 0x00;   // 模式 A 未用到
FSMC_ReadWriteTim.DataSetupTime         = 0x06;   // ← 6 个 HCLK 建立（原文注"6ns*7=42ns"，混用单位 ⚠校核）
FSMC_ReadWriteTim.BusTurnAroundDuration = 0X00;
FSMC_ReadWriteTim.AccessMode            = FSMC_ACCESS_MODE_A;
HAL_SRAM_Init(&SRAM_Handler, &FSMC_ReadWriteTim, &FSMC_ReadWriteTim);
/* CubeMX 生成的另一版：AddressHoldTime=15、CLKDivision=16、DataLatency=17（模式 A 下无效，17d:3541） */
```
`原文无代码`：**标准库 `FSMC_NORSRAMInitStructure` 的填法原文没有**（只有 HAL 版）。
验证（17d:3531 `fsmc_sram_test`）：**每 4096 字节写自增 temp、遍历 1MB 后回读比对**（后读值 > 首值）。
`0x55/0xAA` 只出现在文字里（17d:2838：`*(uint8_t*)0x60000000 = 0xAA` ⇒ 只写低字节），**无回读代码**。
接法：19 根地址 × 16bit = 1MB；`HADDR[1] → FSMC_A[0] → 外部 A0`，`HADDR[0]` 控制 NBL0/NBL1。
`⚠校核`：作者判断"正点原子 A 线对应关系可能画错，建议参考野火图纸"（17d:2584）；
17d:3332 写 `FSMC_CLK = HCLK/CLKDivision`，与手册的 `HCLK/(2×CLKDIV+2)` 不一致。

## 5. I2S + WM8978 + WAV 播放（17d，F4，SPI2 = I2S2）

```c
/* I2S 初始化（4263）：无 I2S_PIDMACmd，用的是 SPI_I2S_DMACmd */
I2S_InitStructure.I2S_Mode = I2S_Mode_MasterTx;  I2S_InitStructure.I2S_Standard = I2S_Standard_Phillips;
I2S_InitStructure.I2S_DataFormat = I2S_DataFormat_16bextended;  I2S_InitStructure.I2S_CPOL = I2S_CPOL_Low;
I2S_InitStructure.I2S_MCLKOutput = I2S_MCLKOutput_Disable;                 // MCLK 不输出（WM8978 用 R6=0 外部给）
I2S_InitStructure.I2S_AudioFreq  = I2S_AudioFreq_Default;                   // 由 SampleRate_Set 单独设
I2S_Init(SPI2, &I2S_InitStructure);
SPI_I2S_DMACmd(SPI2, SPI_I2S_DMAReq_Tx, ENABLE);  I2S_Cmd(SPI2, ENABLE);
/* 调用 */ WM8978_I2S_Cfg(2, 0);
          I2S2_Init(I2S_Standard_Phillips, I2S_Mode_MasterTx, I2S_CPOL_Low, I2S_DataFormat_16bextended);

/* 采样率：fs = I2SxCLK / [256*(2*I2SDIV + ODD)]，I2SxCLK = (HSE/M)*N/R （4269/4216） */
const u8 ratio_tbl[] = { {4410,271,2,6,0}, {4800,258,3,3,1}, {1600,213,2,13,0}, ... };
void I2S2_SampleRate_Set(u8 rate){
  RCC_PLLI2SCmd(DISABLE); RCC_PLLI2SConfig(N, R); RCC->CR |= 1<<26;
  while((RCC->CR & 1<<27) == 0){}                       // 等 PLLI2S 锁定
  tempreg = I2SDIV | (ODD << 8) | (1 << 9);  SPI2->I2SPR = tempreg;   // bit9=MCKOE
}
/* 双缓冲 DMA 播放（4275/4332/4286）见 recipes-timer-adc-dma.md §4 */
```
`⚠校核`：17d:4185"196Khz"应为 **192kHz**；表中 17640/19200 对应 N=361/393 的取值范围说法待核。

**WM8978：`原文无完整初始化序列代码`**（"WM8978 相关初始化库函数"那张表是空的）。原文只散见：
```c
WM8978_Write_Reg(0, 任意值);          // R0 软复位
WM8978_Write_Reg(1, 0X1B);            // R1: MICEN | BIASEN | VMIDSEL=11(5K)   ← 最先要开
WM8978_Write_Reg(2, 0X1B0);           // R2: ROUT1EN | LOUT1EN | BOOSTENR/L
/* 输入通路 WM8978_Input_Cfg（3908）：R2 |= 3<<2 (INPPGA)；R44 = 3<<4 | 3<<0 */
```
文字要求但无代码：R3 使能 LOUT2/ROUT2/MIXER/DACEN；R4 设 `WL[6:5]` + `FMT[4:3]=10`(I2S)；R6=0（外部时钟）；
R10 关静音 + DACOSR128；R49 SPKBOOST/TSDEN；R50/R51 置 1；R52~R55 音量（**最高位 HPVU 必须置 1 才更新**）。
**录音通路 `i2s_rec_dma` 原文无代码**（只给了 ADCDAT/MISO=PC2 引脚与 R2 的 ADCEN 说明）。

## 6. 复用本篇时的顺序建议

| 做什么 | 依据 |
|---|---|
| 先做 SPI 模式 SD（引脚最少、失败信息最多） | §2，固定 CRC 值直接用 |
| 再上 SDIO：先 400kHz + 1 位宽跑通 CMD0/CMD8/ACMD41 | §1.1-1.2；**后续 CMD2~7 得自己补**（原文无） |
| 摄像头：先只出 VGA/QVGA 不缩放，验证通了再动窗口 | §3 的 4 倍数规则 |
| 音频：先用固定 44.1k 的表值，示波器量 BCLK=1.4112M、WS=44.1k 再谈音质 | §5 |
| 任何"配了没效果"的 FSMC | 先算周期数（别信原文 ns），再用自增回读验接线 | §4 |
