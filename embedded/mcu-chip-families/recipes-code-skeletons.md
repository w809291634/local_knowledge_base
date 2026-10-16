# 代码配方：GD32 / AT32 / STC / 沁恒 CH / Z-Stack（照抄原文）

> 配套 `mcu-chip-families/` 各篇。行号指原文导出文本位置。
> 本篇同时收录**"移植时到底改哪几行"**的可执行差异，以及 `原文无代码` 的缺口清单。

## 1. GD32F4（适用 GD32F407 / MDK / GD 官方库 V3.0.4 或 STM32F4 StdPeriph）

### 1.1 改晶振与档位宏（照抄）
```c
// ① gd32f4xx.h（03:47-53）
#define HXTAL_VALUE    ((uint32_t)25000000)      // ← 默认 25M，用 8M 晶振必须在工程宏里覆盖
// ② 工程预处理宏（03:177-210）
USE_STDPERIPH_DRIVER, GD32F407, __FPU_USED, HXTAL_VALUE=8000000
// ③ system_gd32f4xx.c（03:60-76）
#define __SYSTEM_CLOCK_240M_PLL_8M_HXTAL  (uint32_t)(240000000)
uint32_t SystemCoreClock = __SYSTEM_CLOCK_240M_PLL_8M_HXTAL;
// system_clock_config() 里 #elif defined(__SYSTEM_CLOCK_240M_PLL_8M_HXTAL) → system_clock_240m_8m_hxtal()
```
**唯一能查到的改名示例**是中断分组：`nvic_priority_group_set(NVIC_PRIGROUP_PRE2_SUB2);`
（对应 STM32 的 `NVIC_PriorityGroupConfig`）。
`原文无代码`：`rcu_*/gpio_*/usart_*` 的成对改名示例在原文**只有文字步骤**（"STM32 工程移植到 GD32…第 3 步改工程宏"），
**没有改名前后代码对照** ⇒ 别以为库里有现成映射表。
验证：`SystemCoreClockUpdate(); printf("SystemCoreClock:%d", SystemCoreClock);` 应 ≈240000000。

### 1.2 HSE 起振超时（GD32 必改的一行，03:219-224）
```c
#define HSE_STARTUP_TIMEOUT    ((uint16_t)0x05000)   // 改前（GD 的 V3.x 库写在 stm32f10x.h；V3.0 前在 stm32f10x_rcc.c 的 HSEStartUp_TimeOut）
#define HSE_STARTUP_TIMEOUT    ((uint16_t)0xFFFF)    // 改后 ← GD 起振慢，不改则 PLL 锁不住、跑在 IRC 上
```
`⚠校核`：`0x05000` 超出 `uint16_t` 范围、且 F4 的该宏应在 `stm32f4xx.h`，**原文这一段是 F1/F4 库混排**。

### 1.3 `SPI1_SetSpeed` 为什么在 GD32 上要删（03:229-240）
```c
void SPI1_SetSpeed(u8 SPI_BaudRatePrescaler) {
  assert_param(IS_SPI_BAUDRATE_PRESCALER(SPI_BaudRatePrescaler));   // ← GD 删这行（宏没定义）
  SPI1->CR1 &= 0XFFC7;                     // ← 关键错误点：SPI 还在运行就直接改 CR1 分频位
  SPI1->CR1 |= SPI_BaudRatePrescaler;
  SPI_Cmd(SPI1, ENABLE); }
// 官方做法：先 SPI_Cmd(SPIx, DISABLE); 再重配；最后 SPI_Cmd(SPIx, ENABLE);
```
`⚠校核`：原文末行印成 `SPI Cmd(SPlx, DISABLE)` ⇒ 是 `SPI_Cmd(SPIx,` 的 OCR 错。

## 2. AT32F435/437（适用官方 peripheral 库 / AT32_Work_Bench 生成码）

### 2.1 SPI 完整配置（04:2000-3005 `wk_spi1_init`）
```c
crm_periph_clock_enable(CRM_SPI1_PERIPH_CLOCK, TRUE);        // ← 时钟前缀是 CRM，不是 RCC
gpio_pin_mux_config(GPIOA, GPIO_PINS_SOURCE5, GPIO_MUX_5);   // ← SCK；MUX_5 = SPI1
gpio_init_struct.gpio_mode = GPIO_MODE_MUX;  gpio_init(GPIOA, &gpio_init_struct);
spi_default_para_init(&spi_init_struct);
spi_init_struct.transmission_mode   = SPI_TRANSMIT_FULL_DUPLEX;
spi_init_struct.master_slave_mode   = SPI_MODE_MASTER;
spi_init_struct.mclk_freq_division  = SPI_MCLK_DIV_8;        // SCK = PCLK/8
spi_init_struct.clock_polarity      = SPI_CLOCK_POLARITY_LOW;   // ← CPOL=0
spi_init_struct.clock_phase         = SPI_CLOCK_PHASE_1EDGE;    // ← CPHA=0（Mode0）
spi_init(SPI1, &spi_init_struct);
spi_enable(SPI1, TRUE);                                      // 同 GD 教训：重配前先关
```
SPI3（PB3/4/5）要用 **`GPIO_MUX_6`**，SPI1/SPI2 是 MUX_5 ⇒ **同一个外设家族 AF 编号不同**，别照抄。

### 2.2 DMA 三件套（04:2936-2995）
```c
wk_dma_channel_config(DMA1_CHANNEL1,
    (uint32_t)&SPI1->dt,               // ← paddr
    (uint32_t)buf,                     // ← maddr
    len);                              // ← dtcnt（buffer_size 16 位 ⇒ 单次 ≤65535）
/* 展开就是： */ dmax_channely->dtcnt = buffer_size;  dmax_channely->paddr = ...;  dmax_channely->maddr = ...;
dmamux_enable(DMA1, TRUE);
dmamux_init(DMA1MUX_CHANNEL1, DMAMUX_DMAREQ_ID_SPI1_TX);    // ← 请求源映射（像 H7/GD 那样，不是 F4 的 CHSEL）
dma_channel_enable(DMA1_CHANNEL1, TRUE);
/* 发送过程中换缓冲：关通道 → 改 maddr 与 dtcnt_bit.cnt → 再开 */
DISP_DMA_CHANNEL->maddr = (uint32_t)buf;  DISP_DMA_CHANNEL->dtcnt_bit.cnt = size;
void DMA1_Channel3_IRQHandler(void){
  if(dma_flag_get(DMA1_FDT3_FLAG)){ dma_flag_clear(DMA1_FDT3_FLAG); /* … */ } }
```
`⚠校核`：原文变量名 `TragetPoint` 是拼写错误（保留原样）；`wk_dma_channel_config` 的 65535 保护分支
（先递归再更新游标）**作者自注"没有发送保护""会嵌套使用"⇒ 不可直接搬用**（见 `at32.md` §6）。

### 2.3 288MHz 的实际填法（04:1506-1517；`fPLL = (f_in × ns)/(ms × fr)`）
```c
/* 两组合，HEXT = 8M（HEXT_VALUE 在 at32f435_437_conf.h: #define HEXT_VALUE ((uint32_t)8000000)） */
pll_ns = 144;  pll_ms = 1;  pll_fr = 4;    // 8×144/(1×4) = 288M   ← WorkBench 默认
pll_ns = 72;   pll_ms = 1;  pll_fr = 2;    // 8×72/2 = 288M
```
`SystemInit()` **只把 CRM 复位到 HICK，不配 PLL** ⇒ 时钟没生效先找 `system_at32f435_437.c` 的档位函数，不是 `SystemInit`。
`原文无代码`：**ZW/NZW 的配置（`EOPB0`、系统数据高字节须为低字节反码）只有文字描述**，
原话是"使用者可通过设定扩充的系统选项 EOPB0 来使用此扩充模式…512K 扩充模式下零等待闪存容量限制为 128K"、
"每个系统数据实际占 2 字节，低字节为内容、高字节为其反码，不符则产生 `USDERR`"——**照这段去查手册，别自己编寄存器名**。

### 2.4 中断（04:2953-2957）
```c
void wk_nvic_config(void){
  nvic_priority_group_config(NVIC_PRIORITY_GROUP_4);        // 分组
  nvic_irq_enable(DMA1_Channel1_IRQn, 0, 0);                 // 使能 + 抢占/子优先级
}
```
`原文无代码`：ADC1/2/3 **共用向量 `ADC1_2_3_IRQHandler` 的分源判断**原文没有实现，只有"3 组 5.33Msps 独立引擎"的产品描述。

## 3. STC8H（适用 Keil C51）

### 3.1 XFR 访问（07:1305/1361）
```c
#define EAXSFR()  P_SW2 |= 0x80            // ← 打开扩展 SFR 访问，之后一直保持
void main(void){ EAXSFR(); GPIO_config(); Timer_config(); EA = 1; while(1); }
```
**顺序要紧**：`EAXSFR()` 必须在任何 `T2CON/AUXR/P_SW*` 之类扩展 SFR 操作之前。

### 3.2 串口 1 用 T1 做波特率（07:1541-1551、1612-1636）
```c
SCON = 0x50;                    // 模式 1（8 位 UART，波特率可变）+ REN
TMOD = 0x20;                    // T1 = 模式 2（8 位自动重装）
TL1 = TH1 = 0xFD;               // 11.0592M/12T/9600 的典型值
TR1  = 1;
AUXR = 0x40;                    // ← T1x12=1（1T 模式）且 S1ST2=0（串口 1 用 T1）
#define FOSC 11059200UL
#define BRT (65536 - (FOSC/115200 + 2)/4)     // 模式 0（16 位重装）：0xFFE8
#define BRT (256   - (FOSC/115200 + 16)/32)   // 模式 2（8 位，SMOD=0）：0xFD
```
公式（原文）：`波特率 = SYSclk / (4 × (65536 − 重载值))`（1T、T1 模式 0）。
`原文无代码`：**串口 1 改用 T2（`AUXR` 的 B0=S1ST2=1）只有位说明没有初始化代码**；
`S1_S[1:0]`（P_SW1 的 B7:B6）、`S2_S`（P_SW2 的 B0）切引脚**也只有文字没有代码**；
UART3/4 原文注明"STC8H1K28 没有串口 3/4"。

### 3.3 UART2 轮询 + 中断（07:1737-1748，中断号 8）
```c
/* 轮询发送 */ S2BUF = c; while(!(S2CON & 0x02));          // + IE2 = 0x01(ES2) 若开中断
void Uart2_Isr(void) interrupt 8 {
  if (S2CON & 0x02){ S2CON &= ~0x02; uart2_tx_busy = 0; }   // ← 开了 ES2 就必须在 ISR 清 TI
  if (S2CON & 0x01){ S2CON &= ~0x01; uart2_rx_byte = S2BUF; uart2_rx_flag = 1; }
}
```
**这条与轮询死锁的关系**（原文两条互证）：开了 `ES2` 而 ISR 不清 TI ⇒ 中断风暴；ISR 清了 TI ⇒ 主循环
`while(!(S2CON&0x02))` 永远等不到。**同一串口不要混用轮询发送与中断发送。**
中断号：`T0=1, T1=3, 串口1=4, 串口2=8`。`原文无代码`：`using` 寄存器组的用法原文没有示例。

### 3.4 定时器 1T 初始化（07:1273-1278、344）
```c
Timer1_Reload = MAIN_Fosc/1000;                 // 24MHz → 24000 计数 = 1ms
TMOD &= ~0x30;  TMOD &= ~0x40;                  // C/T=0（定时）、清 T1 模式位
AUXR |= 0x40;                                   // ← T1x12=1 → 1T 模式
TH1 = (65536-24000)/256;  TL1 = (65536-24000)   // ← 原文此行被截断 ⚠校核（应为 ;结尾的低字节赋值）
void timer0_isr(void) interrupt 1 { … }
```
公式（原文）：`1T 溢出周期 = (65536 − 重装值)/SYSclk`，`12T 模式再 ×12`。
验证：翻转一个 IO 用示波器量周期（原文即此法）。

### 3.5 ADC 内参电压法（原文只有文字，**无读取序列代码**）
> "第 15 通道内部固定连 1.19V BandGap…`Vx = BGV / res_bg × res_x`（`res_bg` = ADC15 读数）"
⇒ 这是**比例测量法**：用内部基准测自己的读数，可抗 VDD 漂移。写代码时按此式自行实现，别引用不存在的样例。

### 3.6 ISP 硬件选项（关键概念，非代码）
原文："这个选项不对应任何 SFR 寄存器，而是写入 MCU 内部 Flash 末尾的'用户配置字节'区…属 ISP 下载时一并烧录"
⇒ **改了要重新上电才生效**；`OPT_HELPOR_USE_LONG`（上电复位较长延时）也是这类配置字节。
`原文无代码`：**内部 EEPROM/Flash 读写擦、PWMA（含死区寄存器）、看门狗操作** 在 07 章**都没有代码**，
只有"512 字节单页擦除、擦写 10 万次""PWMA=4 对互补带死区"这类文字。

## 4. 沁恒 CH57x/CH58x（⚠校核：原文 main 例来自 CH58X 工程、时钟代码路径来自 CH57x SDK，**跨型号混排**，移植按实际芯片选函数前缀）

### 4.1 时钟（08:580-593）
```c
uint32_t GetSysClock(void){
  rev = R16_CLK_SYS_CFG & 0xff;                                   // 寄存器地址 0x40001008
  if((rev & 0x40) == (0<<6))      return 32000000/(rev & 0x1f);   // HSE 分频
  else if((rev & RB_CLK_SYS_MOD) == (1<<6)) return 480000000/(rev & 0x1f);  // PLL=32M×15=480M 再分频
  else return 32000; }
#define CLK_SOURCE_PLL_60MHz  0x48        // ← 0x40|8 ⇒ 480/8 = 60MHz
void main(void){ SetSysClock(CLK_SOURCE_PLL_60MHz); … }           // ← 必须是 main 第一句
```

### 4.2 BLE 工程 main 骨架（08:912）
```c
SetSysClock(CLK_SOURCE_PLL_60MHz);
GPIOA_ModeCfg(GPIO_Pin_All, GPIO_ModeIN_PU);        // ← 全脚先配上拉输入，防浮空漏电
GPIOA_SetBits(bTXD1); GPIOA_ModeCfg(bTXD1, GPIO_ModeOut_PP_5mA);
UART1_DefInit();
CH58X_BLEInit();  HAL_Init();  GAPRole_PeripheralInit();  Peripheral_Init();
while(1){ TMOS_SystemProcess( ); }                  // ← 主循环唯一一句，别在 main 里做别的事
```
参数设置（08:1040）：
```c
GAPRole_SetParameter(GAPROLE_ADVERT_ENABLED, sizeof(uint8_t), &initial_advertising_enable);
GAPRole_SetParameter(GAPROLE_SCAN_RSP_DATA,  sizeof(scanRspData), scanRspData);
GGS_SetParameter(GGS_DEVICE_NAME_ATT, GAP_DEVICE_NAME_LEN, attDeviceName);
GAP_SetParamValue(TGAP_DISC_ADV_INT_MIN, advInt);          // ⚠校核：原文此行前有断字残缺
/* 连接间隔单位 1.25ms（7.5ms~4s）；有效间隔 = 间隔 ×(1+从设备延迟) */
```

### 4.3 ISR 属性 + TMR0（**这条不写就必然跑飞**，08:1266）
```c
__attribute__((interrupt("WCH-Interrupt-fast")))     // ← 不可省，否则用 ret 而非 mret 返回 → 跑飞
__attribute__((section(".highcode")))                // ← 中断代码放 RAM（.highcode >RAM AT>FLASH）
void TMR0_IRQHandler(void){
  if(TMR0_GetITFlag(TMR0_3_IT_CYC_END)){ TMR0_ClearITFlag(TMR0_3_IT_CYC_END); /* … */ } }
/* 另一版中断还要判 EXC 异常，且 fast 版在 OS 下必须让出（return EXC_SUCCESS） */
TMR0_TimerInit(BUZZER_HALF_PERIOD);        // 26 位定时器 @60MHz ⇒ 周期 = 值/60M
TMR0_ITCfg(ENABLE, TMR0_3_IT_CYC_END);
PFIC_SetPriority(TMR0_IRQn, 0xF0);         // ← 压到最低，保证 USB/BLE 能抢
PFIC_EnableIRQ(TMR0_IRQn);
```
`⚠校核`：**RTOS 环境下禁用 `WCH-Interrupt-fast`**（另处 08 章节的 `WCH-Interrupt-slow-func` 才是 OS 版）；
"含主机角色必须用外部 32K 晶振"、"BLE 运行期间禁止关全局中断/长 ISR" 是硬约束。
`原文无代码`：GPIO 中断（`GPIO_As中断`/`R32_PIN_IC`）、SPI/I2C 初始化例、`const tTaskEvents_T` 任务事件表
—— 原文只有"开启事件后应用任务将处理 `Peripheral_ProcessEvent` 中的事件"这句文字。
OTA/IAP 地址（08:745-775）：DataFlash `0x00070000~0x00077FFF`(32K)、`BLE_SNV_ADDR 默认 0x77E00`、
OTA 示例偏移 `0x7000`、IAP 示例偏移 `0x0000`（合入须互相避让）、`BOOT_LOAD_CFG(0x7E000)`、`ROM_CFG_ADDR(0x7F000)` 在 DataFlash 之外。

## 5. Z-Stack 应用层模板（适用 ZStack-CC2530-2.4.0 / IAR）

### 5.1 描述符 + Init 注册骨架（02:964/1037）
```c
SimpleDescriptionFormat_t zclSampleSw_SimpleDesc = {
  SAMPLESW_ENDPOINT, ZCL_HA_PROFILE_ID, ZCL_HA_DEVICEID_ON_OFF_LIGHT_SWITCH,
  SAMPLESW_DEVICE_VERSION, SAMPLESW_FLAGS,
  ZCLSAMPLESW_MAX_INCLUSTERS, (cId_t *)zclSampleSw_InClusterList,
  ZCLSAMPLESW_MAX_OUTCLUSTERS, (cId_t *)zclSampleSw_OutClusterList };
/* endPointDesc_t { byte endPoint; byte *task_id; simpleDesc_t *simpleDesc; latency_t latencyReq; } */
void zclSampleSw_Init(byte task_id){
  zclSampleSw_TaskID = task_id;                                // ← task_id 由 osalInitTasks 传入
  bdb_RegisterSimpleDescriptor(&zclSampleSw_SimpleDesc);        // 方式 1（3.0.2 风格）
  afRegister(&sampleSw_TestEp);                                 // 方式 2：直接向 AF 注册端点
  zcl_registerAttrList(...);  zcl_registerForMsg(zclSampleSw_TaskID); }
```
任务表与初始化链（02:1852/1917）：`main → osal_init_system → osalInitTasks`；
```c
const pTaskEventHandlerFn tasksArr[] = { macEventLoop, nwk_event_loop, Hal_ProcessEvent,
#if defined( MT_TASK )  MT_ProcessEvent,  #endif
  APS_event_loop, ZDApp_event_loop, SAPI_ProcessEvent /* , 用户任务加在最后 */ };
const uint8 tasksCnt = sizeof(tasksArr)/sizeof(tasksArr[0]);  uint16 *tasksEvents;
```
`⚠校核`：任务入口叫 `osal_start_system`/`osal_run_system`，原文某处写的 `osal_start_host_app` 不存在。

### 5.2 事件处理函数骨架（02:2184，删到关键分支）
```c
UINT16 SAPI_ProcessEvent(byte task_id, UINT16 events){
  if (events & SYS_EVENT_MSG){
    pMsg = (osal_event_hdr_t *)osal_msg_receive(task_id);
    while (pMsg){
      switch (pMsg->event){
        case AF_INCOMING_MSG_CMD:                              // ← 收到数据
          pMSGpkt = (afIncomingMSGPacket_t*)pMsg;
          SAPI_ReceiveDataIndication(pMSGpkt->srcAddr.addr.shortAddr,
                                     pMSGpkt->clusterId,
                                     pMSGpkt->cmd.DataLength, pMSGpkt->cmd.Data); break;
        case ZDO_STATE_CHANGE:                                 // ← 入网状态机
          if (pMsg->status == DEV_END_DEVICE || pMsg->status == DEV_ROUTER || pMsg->status == DEV_ZB_COORD)
            SAPI_StartConfirm(ZB_SUCCESS);
          else if (pMsg->status == DEV_HOLD || pMsg->status == DEV_INIT) SAPI_StartConfirm(ZB_INIT);
          break;
        case AF_DATA_CONFIRM_CMD: … break; }                    // 发送回执（需 AF_ACK_REQUEST）
      osal_msg_deallocate((uint8*)pMsg);                       // ← 必须释放，否则堆耗尽
      pMsg = (osal_event_hdr_t *)osal_msg_receive(task_id); }
    return (events ^ SYS_EVENT_MSG); }
  if (events & ZB_ENTRY_EVENT){ … zb_StartRequest() … return (events ^ ZB_ENTRY_EVENT); }
  if (events & (ZB_USER_EVENTS)){ zb_HandleOsalEvent(events); }   // 用户事件位只有 0x00FF
  return 0; }
```
### 5.3 定时 / 发送 / NV / MT
```c
osal_start_timerEx(task_id, event_id, timeout_value);              // 单位 ms（软定时器，不打断当前执行）
osal_start_reload_timer(touch_Task_ID, touchScan_EVENT, 10);       // 周期 10ms 扫描示例
/* AF_DataRequest（02:1076） */
dstAddr.addrMode = afAddr16Bit;                 // 单播；广播用 Addr5Std
dstAddr.addr.shortAddr = destNwkAddr;  dstAddr.endPoint = SAMPLESW_ENDPOINT;
AF_DataRequest(&dstAddr, &sampleSw_TestEp, cid, len, data,
               &transferId, AF_DISCV_ROUTE, AF_DEFAULT_RADIUS);
/* NV（02:2780/2395） */
osal_nv_write(ZCD_NV_CHANLIST, 0, sizeof(uint32), &vScanChannels);
osal_nv_read(configId, 0, size, pValue);        // 封装层：zb_ReadConfiguration / zb_WriteConfiguration
/* MT 串口命令（02:2262/2502） */
UINT16 MT_ProcessEvent(uint8 task_id, uint16 events){
  if (events & SYS_EVENT_MSG){
    while ((msg_ptr = osal_msg_receive(MT_TaskID)))
      MT_ProcessIncomingCommand((mtOSALSerialData_t *)msg_ptr);
    return (events ^ SYS_EVENT_MSG); } }
void MT_ProcessIncomingCommand(mtOSALSerialData_t *msg){
  switch (msg->hdr.event){
    case CMD_SERIAL_MSG:      MT_ProcessIncoming(msg->msg); break;        // ← 收 PC 命令
    case MT_SYS_APP_RSP_MSG:  len = msg->hdr.status; MTProcessAppRspMsg(msg_ptr, len); break; }
  osal_msg_deallocate((uint8 *)msg); }
```
`⚠校核`：`osal_msg_send` 的原注释里多出一个 `@param uint8 len`（函数实际只有 2 参，TI 原注释缺陷）；
`MT_SYS_APP_RSP_MSG` 分支里被注释掉的 `SPI_0DATA_MSG_LEN` 是公司魔改痕迹（`<!-- 项目专有 -->`）。

### 5.4 Z-Stack 侧的验证方法（原文给的）
| 验什么 | 怎么验 |
|---|---|
| 端点注册成功 | PC 抓包看 ZDO Match Descriptor 是否命中你的端点 |
| 空口发送成功 | `AF_DATA_CONFIRM_CMD` 的状态 == `ZSuccess` |
| NV 是否真落盘 | 写 → 复位 → 读回比对 |
| 入网是否成功 | `ZDO_STATE_CHANGE` 到达 `DEV_ZB_COORD/DEV_ROUTER/DEV_END_DEVICE`；否则先查 `TC_LINKKEY_JOIN` 与 `zb_StartRequest()` |
