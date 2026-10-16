# 代码配方：I2C / SPI 与器件驱动（照抄原文 + 用法 + 验证）

> 配套 `i2c-spi-and-device-drivers.md`。代码照抄原 docx（17b=I2C 与器件、17c=SPI 与器件），
> 只删无关行、加 `// ← 关键`；未改数值/宏名。**`⚠校核` = 原文可疑处保留原样**；
> **`原文无代码` = 该处只有文字/图片，不要当已有依据**。

## 0. 先看这张表：三套软件 I2C 的"ACK 返回值"口径完全不同

| 口径 | 函数名 | ACK 返回 | NACK 返回 | 出处 |
|---|---|---|---|---|
| **A 等待应答型** | `IIC_Wait_Ack` / `I2C1_WaitAck` / `iic_waitack` | **0**（成功） | 1（失败且自动 stop） | 17b:115/211/690 |
| **B 写带应答（CC2530 OLED 版）** | `iic_write_byte` | **1** | 0 | 17b:55（另一份 583） |
| **C 写带应答（CC2530 传感器版 / F4 / F1 RTT 层）** | `iic_write_byte` / `iic_write_byte_ack` | **0** | 1 | 17b:809/821/682 |

`⚠校核`：17b:244 的 `IIC_Send_Byte` 是 `void`，**函数头注释却写了第三种口径**（"1 有应答 / 0 无应答"）；
17b:682 的 `iic_write_byte_ack` 代码是 `ACK→0`，注释仍是"1 有应答" —— **注释与实现相悖，务必读代码不读注释**。
读字节侧三套一致：`ack=1` 发 ACK、`ack=0` 发 NACK；但 F1 另有 `iic_read_byte_ack_Ex(ack)` 内部 `iic_send_ack(!ack)` **把语义取反**。

## 1. 软件 I2C 骨架（三平台）

### CC2530（`P0DIR` 切方向，宏不带括号）— 来源 17b:20/25/55
```c
void iic_start(void){ SDA_OUT; SDA=1; SCL=1; delay_us(1); SDA=0; delay_us(1); SCL=0; }
void iic_stop (void){ SDA_OUT; SDA=0; SCL=1; delay_us(1); SDA=1; delay_us(2); }
unsigned char iic_write_byte(unsigned char data){
  SDA_OUT; SCL=0;
  for(char i=0;i<8;i++){ if(data&0x80)SDA=1; else SDA=0;
    delay_us(1); SCL=1; delay_us(1); data<<=1; SCL=0; }
  SDA_IN; SDA=1; SCL=1;                       // ← 关键：先切输入再拉高 SCL
  if(SDA==1) return 0; else { SCL=0; return 1; }   // ← 本例口径 B
}
```
**延时不能按名义值算**（原文实测）：`delay_us(1)→1.25us`、`(2)→2.25us`、`(5)→5us`、`(100)→97us`；
旧版 `iic_delay_us(0)` 最小就有 4us ⇒ **必须用逻辑分析仪量实际周期**。

### STM32F4（MODER 直写 + BSRRL/BSRRH）— 来源 17b:115/119
```c
#define I2C1_SDA_IN  do{ I2C1_SDA_GPIO->MODER &= ~(3<<I2C1_SDA_NUM*2); I2C1_SDA_GPIO->MODER |= (0<<I2C1_SDA_NUM*2);}while(0)
#define I2C1_SDA_OUT do{ I2C1_SDA_GPIO->MODER &= ~(3<<I2C1_SDA_NUM*2); I2C1_SDA_GPIO->MODER |= (1<<I2C1_SDA_NUM*2);}while(0)
#define I2C1_SCL_H   (I2C1_SCL_GPIO->BSRRL = I2C1_SCL_PIN)
unsigned char I2C1_WaitAck(void){ unsigned char t=0;
  I2C1_SDA_IN; I2C1_SCL_H; I2C1_Delay(1);
  while(I2C1_SDA_R){ if(++t>250){ I2C1_Stop(); I2C1_SCL_L; return 1; } I2C1_Delay(1); }
  I2C1_SCL_L; return 0; }                     // ← 口径 A
```
`⚠校核`：F4 的 `I2C1_WriteByte` 是 **void**，应答必须由调用者单独取 `I2C1_WaitAck()`；
I2C4 版 `WaitAck` 多一句 `I2C4_SDA_H;`（I2C1 版没有）⇒ 两条总线时序不同，别互相抄。

### STM32F1（位带 `PBout/PBin`）— 来源 17b:211/226/237/244/249
```c
void IIC_Start(void){ SDA_OUT(); IIC_SDA=1; IIC_SCL=1; delay_us(4); IIC_SDA=0; delay_us(4); IIC_SCL=0; }
void IIC_Stop (void){ SDA_OUT(); IIC_SCL=0; IIC_SDA=0; delay_us(4); IIC_SCL=1; IIC_SDA=1; delay_us(4); }
u8 IIC_Wait_Ack(void){ ... if(ucErrTime>250){ IIC_Stop(); return 1; } ... return 0; }   // 口径 A
```
`⚠校核`：① 17b 另一份"通用层" `SDA_IN` 宏写的是 `CRH &= ~(0XF<<SDA_NUM*4)` —— **位移未减 8**，
引脚号 ≥8 时方向切换失效（CRH 应用 `(num-8)*4`）；② 正点原子版 `IIC_Stop` 的注释行位置与真实边沿错开一拍。

### 通用调用序与验证
```
init → start → write_byte(addr<<1) → waitack → write_byte(reg) → waitack
     → [写] data… stop
     → [读] start + write_byte(addr|1) + read_byte(1)… 最后一个 read_byte(0) → stop
```
验证：逻辑分析仪看 **SCL 第 9 个高电平期间 SDA 是否稳定为低**；总线上扫不到器件先查方向切换宏与上拉。

## 2. OLED（SSD1306/1316，I2C）

写函数与控制字节 — 来源 17b:321/590/615
```c
#define ADDR_W 0X78   /* 0111 10 SA0 R/W */   #define ADDR_R 0X79
static void OLED_Write_command(unsigned char cmd){ iic_start(); iic_write_byte(ADDR_W);
  iic_write_byte(0x00);            // ← 控制字节 Co=0,D/C#=0 = 命令
  iic_write_byte(cmd); iic_stop(); }
static void OLED_Write_GRAM(unsigned char g){ ... iic_write_byte(0x40); /* D/C#=1 单字节数据 */ ... }
static void OLED_Write_GRAM_BlitLine(char* d, unsigned int len){ iic_start(); iic_write_byte(ADDR_W);
  for(int i=0;i<len;i++,d++){ iic_write_byte(0xC0);   /* Co=1 连续写，列指针自增 */ iic_write_byte(*d); }
  iic_stop(); }
```
页与列定位 — 来源 17b:738/741
```c
static void OLED_Set_Pos(unsigned int x, unsigned int y){
  OLED_Write_command(0xb0 + y);                 // 页地址 B0H~B7H
  OLED_Write_command(((x & 0xf0) >> 4) | 0x10); // 列高 4 位 10H~1FH
  OLED_Write_command( x & 0x0f); }              // 列低 4 位 00H~0FH
```
`⚠校核`：17b:413/472 把 `0x00` 注释成"列起始地址**高位**"、`0x10` 成"低位" —— **与上面的实现和手册正好互换**；
17b:468 `OLED_WR_Byte(0xAE,OLED_CMD);//开启OLED屏显示` 错，0xAE 是关显示（0xAF 才开）；
17b:444 出现不存在的 `C1H`（COM 反向是 `C8H`）。

**96×32 正装初始化序列**（整段照抄，17b:590）
```
0xAE, 0x20 0x02, 0xB0, 0x00, 0x10, 0x40, 0x81 0x45, 0xA1, 0xC0, 0xA6,
0xA8 (Max_page*8-1)=0x1F, 0xD3 0x00, 0xD5 0x80, 0xD9 0x22, 0xDA 0x12,
0xDB 0x20, 0x8D 0x14, 0xAF
```
**128×64 倒装只改三处**（17b:615/666/671）：`Max_Column 96→128`、`Max_page 4→8`（于是 A8 参数自动变 0x3F）、
对比度 `0x45→0xAA`、COM 方向 `0xC0→0xC8`。

显存与刷新（含硬编码风险）— 17b:590/615
```c
static unsigned char OLED_GRAM[Max_Column][Max_page];
void OLED_DrawPoint(u8 x,u8 y,u8 t){ u8 pos,bx,temp=0;
  if(x>95||y>31) return;                     // ← 硬编码 96×32 边界
  pos = 7 - y/8; bx = y%8; temp = 1<<(7-bx); // ← pos 反序（页 7 对应 y=0..7）
  if(t) OLED_GRAM[x][pos] |= temp; else OLED_GRAM[x][pos] &= ~temp; }
void OLED_Refresh_Gram(void){
  for(i=0;i<8;i++){ OLED_Write_command(0xb0+i); OLED_Write_command(0x00); OLED_Write_command(0x10);
    for(n=0;n<128;n++) OLED_Write_GRAM(OLED_GRAM[n][i]); } }   // ← 8/128 硬编码，96×32 要改 4/96
```
调用序：`OLED_Init → OLED_Clear → ShowChar|ShowString|ShowBitmap → OLED_Refresh_Gram`；
取模用 PCToLCD2002：**阴码、列行式、逆向、8 位/列**。
验证：先跑 `OLED_Fill(0xFF)` 应整屏白；画面左右反 → `0xA1/0xA0`，上下反 → `0xC0/0xC8`，整屏偏移半屏 → `0xDA`。

## 3. 24C02 读时序（"读前 DUMMY WRITE + 重复起始"）

来源 17b:682/1032（24C02 专用函数原文无，这是通用等价实现） | `addr 写=0xA0 / 读=0xA1`
```c
iic_start(); iic_write_byte(addr);                       // 写地址
if(iic_waitack()!=0){ iic_stop(); return 1; }
iic_write_byte(reg);  iic_waitack();                     // ← DUMMY WRITE：先把目标地址写进去
iic_start();  iic_write_byte(addr+1);                    // ← 重复起始，不先 stop
while(len != 0){
  if(len==1) *buf = iic_read_byte_ack_Ex(0);             // ← 最后一个读要发 NACK
  else       *buf = iic_read_byte_ack_Ex(1);
  len--; buf++; }
iic_stop();
```
验证：写 `0x55` 到 0x10 再按上面读回；示波器看第一个 ACK 之后**有第二个 start 条件 + `0xA1`** 才叫时序正确。

## 4. PCA9685（12 位 PWM，"频率设置"这段是最常被抄错的）

来源 17b:899/923/978/1032
```c
void PCA9685_SetPWMFreq(uint8_t addr, float freq){ char lastMode,newMode,preVal; float p;
  freq = freq * 0.975;                                   // 粗校准（RT 版用 0.915）⚠校核 两处不同
  p = round(25000000/(4096*freq)) - 1;                   // 内部 25MHz
  PCA9685_ReadReg (addr, PCA9685_MODE1, &lastMode, 1);
  newMode = (lastMode & 0x7F) | 0x10;                    // ← 置 SLEEP：PRE_SCALE 只能在 SLEEP=1 时写
  PCA9685_WriteReg(addr, PCA9685_MODE1,  &newMode, 1);
  preVal = (char)p;
  PCA9685_WriteReg(addr, PCA9685_PRE_SCALE, &preVal, 1);  // PRE_SCALE=0xFE
  PCA9685_WriteReg(addr, PCA9685_MODE1, &lastMode, 1);    // ← 退出 SLEEP
  delay_ms(2);                                             // ← 手册要求 SLEEP=0 后 ≥500us 才能 RESTART
  lastMode |= 0xA1;                                        // RESTART|AI|ALLCALL
  PCA9685_WriteReg(addr, PCA9685_MODE1, &lastMode, 1); }
void PCA9685_SetPWM(uint8_t addr,uint8_t offset,uint16_t on_v,uint16_t off_v){ char d[4];
  d[0]=on_v&0xFF; d[1]=on_v>>8; d[2]=off_v&0xFF; d[3]=off_v>>8;
  offset *= 4;                                             // ← 通道寄存器 = LED0_ON_L + 4*通道
  PCA9685_WriteReg(addr, PCA9685_LED0_ON_L + offset, d, 4); }   // 4 字节连写 ON_L,ON_H,OFF_L,OFF_H
```
取值：`0x1000` = 恒高、`0,0x1000` = 恒低、`0,1024` = 25%；舵机 20ms / 0.5~2.5ms ⇒ 4.88us 步进、约 0.439° 分辨率。
`⚠校核`：作者标注本节"**IIC 代码具体没有修改，周期延时是错误的，后期可以调整**" ⇒ **整节属未验证代码**；
`PCA9685_portClear(addr)` 收了形参却内部写死 `ADDR1/ADDR2`。
验证：示波器量 SDOUT 周期；`ReadReg(0xFE)` 回读 PRE_SCALE 即证频率写进去。

## 5. PCF8563 RTC（BCD + 掩码 + 一个真实总线坑）

来源 17b:1108/1112，从地址 `0x51`，驱动传 `0x51<<1`
```c
static inline uint8_t decimal2bcd(uint8_t d){ return ((d/10)<<4) | (d%10); }
static inline uint8_t bcd2decimal(uint8_t b){ return ((b>>4)*10) + (b&0x0f); }
/* 从 0x02 起连读 7 字节，逐字段套掩码 */
tm_sec  = bcd2decimal(data[0] & 0x7f);   // data[0]&0x80 = VL 低压标志
tm_min  = bcd2decimal(data[1] & 0x7f);
tm_hour = bcd2decimal(data[2] & 0x3f);
tm_mday = bcd2decimal(data[3] & 0x3f);
tm_wday = bcd2decimal(data[4] & 0x07);   // 芯片自动算，写无效
tm_mon  = bcd2decimal(data[5] & 0x1F) - 1;
century = (data[5] & PCF8563_CENTURY_BIT) ? 100 : 0;      // 月寄存器 bit7 = 世纪位
tm_year = bcd2decimal(data[6]) + century;
pcf->write(handle, PCF8563_ADDRESS<<1, PCF8563_SECONDS, data, PCF8563_TIME_SIZE);
pcf->write(handle, PCF8563_ADDRESS<<1, PCF8563_CONTROL_STATUS1, &clear0x00, 1); // 清 STOP/TEST
```
**真实坑（原文 1346/1350/1096）**：连读只能读回第一个寄存器、其余为 0。根因是 `SDA_IN` 配了上/下拉**却没设 `ODR`**，
默认下拉把总线拉低；解法①外部加上拉电阻 ②`I2C4_WriteByte` 末尾补一句 `I2C4_Delay(1);`（原文："这里加入一个延时就可以解决"）。
`⚠校核`：读侧注释 `/* 0..11 */` 与写侧 `/* 1..12 */` 不一致；报警判据里判 wday 时复用了 `tm_mday`（原文即如此）。
验证：连续两次读秒应递增；`0x02` 的 bit7=0 表示供电正常。

## 6. TM1650 数码管（**类 I2C、无从机地址 ⇒ 只能软件模拟**）

来源 17b:1195/1236
```c
TM1650_Set(0x48, 0x51);        // 显示命令：亮度级 + 八段方式 + 开显示
TM1650_Set(0x68, CODE[0]);     // 显存地址 0x68 / 0x6A / 0x6C / 0x6E = 第 1..4 位（步进 2）
TM1650_Set(0x6A, CODE[5]); TM1650_Set(0x6C, CODE[1]); TM1650_Set(0x6E, CODE[4]);
```
硬件要求：**必须共阴**、SCL/SDA 4.7kΩ 上拉、VCC-GND 0.1µF、每段串 100Ω、DIG-Kx 串 2kΩ。
验证：写 `0x48,0x48`（关显示）应整屏灭；`0x51→0x58` 亮度阶梯肉眼可辨；改 `0x68` 只动第 1 位说明地址步进对。
`⚠校核`：`0x48,0x51` 被注释成"5 级亮度"，而常见命令表里 `0x51` 含义不同，原文未给位定义。

## 7. SPI 初始化 / 分频 / 读写一字节

来源 17c:124/129/134/143 | 适用 F4 标准库（PB3/4/5 = SCK/MISO/MOSI，**Mode3**）
```c
void SPI1_Init(void){
  RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE); RCC_APB2PeriphClockCmd(RCC_APB2Periph_SPI1, ENABLE);
  G.GPIO_Pin = GPIO_Pin_3|GPIO_Pin_4|GPIO_Pin_5; G.GPIO_Mode = GPIO_Mode_AF;
  G.GPIO_OType = GPIO_OType_PP; G.GPIO_Speed = GPIO_Speed_100MHz; G.GPIO_PuPd = GPIO_PuPd_UP;
  GPIO_Init(GPIOB, &G); GPIO_PinAFConfig(GPIOB, GPIO_PinSource3, GPIO_AF_SPI1);   /*4、5 同*/
  RCC_APB2PeriphResetCmd(RCC_APB2Periph_SPI1, ENABLE); RCC_APB2PeriphResetCmd(RCC_APB2Periph_SPI1, DISABLE);
  S.SPI_Direction = SPI_Direction_2Lines_FullDuplex; S.SPI_Mode = SPI_Mode_Master; S.SPI_DataSize = SPI_DataSize_8b;
  S.SPI_CPOL = SPI_CPOL_High; S.SPI_CPHA = SPI_CPHA_2Edge; S.SPI_NSS = SPI_NSS_Soft;   // Mode3（Flash）
  S.SPI_BaudRatePrescaler = SPI_BaudRatePrescaler_256;      // 84M/256 = 328.125kHz
  S.SPI_FirstBit = SPI_FirstBit_MSB; S.SPI_CRCPolynomial = 7; SPI_Init(SPI1, &S);
  SPI_Cmd(SPI1, ENABLE); SPI1_ReadWriteByte(0xff); }         // ← 空转一字节"启动传输"
void SPI1_SetSpeed(u8 prescaler){
  assert_param(IS_SPI_BAUDRATE_PRESCALER(prescaler));
  SPI1->CR1 &= 0XFFC7;                  // ← CR1 bit3-5 清零
  SPI1->CR1 |= prescaler; SPI_Cmd(SPI1, ENABLE); }          // ⚠GD32 上要先 DISABLE 再改（见 mcu-chip-families/gd32.md）
u8 SPI1_ReadWriteByte(u8 TxData){
  while(SPI_I2S_GetFlagStatus(SPI1, SPI_I2S_FLAG_TXE) == RESET){}
  SPI_I2S_SendData(SPI1, TxData);
  while(SPI_I2S_GetFlagStatus(SPI1, SPI_I2S_FLAG_RXNE) == RESET){}
  return SPI_I2S_ReceiveData(SPI1); }
```
HAL/RT-Thread 版：读写一字节用 `HAL_SPI_TransmitReceive(&SPI1_Handler, &TxData, &RxData, 1, 1000)`；
`SPI1_SetSpeed` 要 `__HAL_SPI_DISABLE → CR1&=0XFFC7 → |=prescaler → __HAL_SPI_ENABLE`；`MspInit` 里 `Alternate = GPIO_AF5_SPI1`。
`原文无代码`：**SPI 的 DMA 收发骨架在 17b/17c 里都没有**，只有映射表（`SPI1_RX = Stream0/2 + Ch3`）可参考。

## 8. W25Q128（读 ID / 页写 / 扇区擦 / **跨页与跨扇区处理**）

来源 17c:277（正点原子改版）
```c
/* 顺序：Init → ReadID 校验 → (Erase_Sector) → Write → Wait_Busy */
void W25QXX_Init(void){ /*CS 推挽输出并置 1*/ SPI1_Init(); SPI1_SetSpeed(SPI_BaudRatePrescaler_4); /*21M*/
  W25QXX_TYPE = W25QXX_ReadID(); if(W25QXX_TYPE == 0xEF16){ W25QXX_SIZE = 8*1024*1024; } }  // ⚠校核见下
u16 W25QXX_ReadID(void){ u16 T=0; W25QXX_CS=0; SPI1_ReadWriteByte(0x90);
  SPI1_ReadWriteByte(0x00); SPI1_ReadWriteByte(0x00); SPI1_ReadWriteByte(0x00);   // 24bit 地址 0
  T |= SPI1_ReadWriteByte(0xFF)<<8; T |= SPI1_ReadWriteByte(0xFF); W25QXX_CS=1; return T; }   // 期望 EF 17
u8  W25QXX_ReadSR(void){ u8 b; W25QXX_CS=0; SPI1_ReadWriteByte(0x05); b=SPI1_ReadWriteByte(0xFF); W25QXX_CS=1; return b; } // bit0 BUSY, bit1 WEL
void W25QXX_Write_Enable(void){ W25QXX_CS=0; SPI1_ReadWriteByte(0x06); W25QXX_CS=1; }
void W25QXX_Wait_Busy(void){ while((W25QXX_ReadSR() & 0x01) == 0x01); }
void W25QXX_Write_Page(u8* p, u32 addr, u16 num){ W25QXX_Write_Enable(); W25QXX_CS=0;
  SPI1_ReadWriteByte(0x02); SPI1_ReadWriteByte(addr>>16); SPI1_ReadWriteByte(addr>>8); SPI1_ReadWriteByte(addr);
  for(i=0;i<num;i++) SPI1_ReadWriteByte(p[i]);
  W25QXX_CS=1; W25QXX_Wait_Busy(); }                       // ← 单条命令不得跨页（≤256B）
void W25QXX_Erase_Sector(u32 sec){ sec *= 4096;            // ← 形参是扇区号；类型必须 u32
  W25QXX_Write_Enable(); W25QXX_Wait_Busy(); W25QXX_CS=0; SPI1_ReadWriteByte(0x20);
  SPI1_ReadWriteByte(sec>>16); SPI1_ReadWriteByte(sec>>8); SPI1_ReadWriteByte(sec);
  W25QXX_CS=1; W25QXX_Wait_Busy(); }                        // 原文注：扇区擦除最少 150ms
/* 跨页：自动切页 */
void W25QXX_Write_NoCheck(u8* p, u32 addr, u16 num){ u16 rest;
  rest = 256 - addr % 256;                                  // ← 本页剩余字节
  if(num <= rest) rest = num;
  while(1){ W25QXX_Write_Page(p, addr, rest);
    if(num == rest) break;
    p += rest; addr += rest; num -= rest;
    rest = (num > 256) ? 256 : num; } }
```
**跨扇区 = 读-改-写**：`secpos = addr/4096; secoff = addr%4096; secremain = 4096-secoff;` → 先整扇区读进
`W25QXX_BUFFER[4096]` → 若新数据不是全 0xFF 才 `Erase_Sector(secpos)` 并把新数据 memcpy 进缓冲、整扇区回写，
否则直接 `Write_NoCheck`；然后 `secpos++; secoff=0; 指针与长度按 secremain 前移`。
`⚠校核`：① `if(W25QXX_TYPE == 0xEF16)` 判的是 **W25Q64**，W25Q128 应是 `0xEF17` ⇒ 容量赋值对 128 不生效；
② `num`/`NumByteToWrite` 用 `u16` ⇒ 单次上限 65535，跨更多扇区要外层循环；③原文 272 行自述"这里有一描述错误"。
验证：逻辑分析仪看 CS 低期间首字节 = `0x90`、随后 4 字节为 `EF 17`；`ReadSR()&1` 归 0 才算擦完；页写后回读比首尾。

## 9. DM9051（SPI 以太网：寄存器 / burst / PHY 间接访问）

来源 17c:328/356/366/378/389/429 | **模式 0**（`CLKPolarity=LOW`、`CLKPhase=1EDGE`），与 Flash 的模式 3 不同
```c
static void dm9051_write_reg(u8 reg, u8 data){ DM9051_CS_LOW;
  SPIx_ReadWriteByte(reg | 0x80);      // ← 写：命令最高位置 1
  SPIx_ReadWriteByte(data); DM9051_CS_HIGH; }
static u8  dm9051_read_reg(u8 reg){ u8 d; DM9051_CS_LOW;
  SPIx_ReadWriteByte(reg);              // ← 读：最高位保持 0
  d = SPIx_ReadWriteByte(0); DM9051_CS_HIGH; return d; }
void dm9051_write_mem(u8* p, u32 len){ DM9051_CS_LOW;
  SPIx_ReadWriteByte(SPI_WR_BURST /*0x78*/ | 0x80);        // → 0xF8
  for(i=0;i<len;i++) SPIx_ReadWriteByte(p[i]); DM9051_CS_HIGH; }
int  dm9051_read_mem(u8* p, u32 len){
  int b = (dm9051_read_reg(DM9051_MRRH)<<8) + dm9051_read_reg(DM9051_MRRL);   // ← 先取读指针
  DM9051_CS_LOW; SPIx_ReadWriteByte(SPI_RD_BURST /*0x72*/);
  for(i=0;i<len;i++) p[i] = SPIx_ReadWriteByte(0x0);
  DM9051_CS_HIGH;
  int d = (dm9051_read_reg(DM9051_MRRH)<<8) + dm9051_read_reg(DM9051_MRRL);
  if (d > b) return d - b; else return (0x4000 - b) + (d - 0x0c00); }          // ← RX 环形回卷
/* PHY 间接访问：EPAR 0x0C(基址 0x40)、EPDRL/H 0x0D/0x0E、EPCR 0x0B */
static void phy_write(u16 reg, u16 val){
  dm9051_write_reg(DM9051_EPAR, DM9051_PHY | reg);
  dm9051_write_reg(DM9051_EPDRL, val & 0xff); dm9051_write_reg(DM9051_EPDRH, (val>>8) & 0xff);
  dm9051_write_reg(DM9051_EPCR, 0xa);                            // 0xA = READEN|EECMD = 写
  do{ delay_ms(1); }while(dm9051_read_reg(DM9051_EPCR) & 0x1);   // ← 轮询 EPHYBSY
  dm9051_write_reg(DM9051_EPCR, 0x0); }
static u16  phy_read (u32 reg){ u16 d;
  dm9051_write_reg(DM9051_EPAR, DM9051_PHY | reg);
  dm9051_write_reg(DM9051_EPCR, 0xc);                            // 0xC = TRDEN|EECMD = 读
  do{ delay_ms(1); }while(dm9051_read_reg(DM9051_EPCR) & 0x1);
  dm9051_write_reg(DM9051_EPCR, 0x0);
  return (dm9051_read_reg(DM9051_EPDRH)<<8) | dm9051_read_reg(DM9051_EPDRL); }
```
`⚠校核`：回卷分支把 `0x0C00` 当 RX 缓冲基址硬编码，且未处理 `d<b && d<0x0c00`；`phy_mode_set` 默认
`phy_reg4=0x01e1` 与注释的 auto 值不一致。验证：`read_reg(CHIPR)` 读到固定芯片 ID、`phy_read(2/3)` 非 0xFFFF
说明 EPAR/EPCR 通路正确；示波器看 SCK 空闲低、首字节 bit7=1 即写命令。

## 10. GC9A01 圆形彩屏（MADCTL 与大小端）

来源 17c:507~561
```c
LCD_WR_REG(0x36); LCD_WR_DATA8(0x68);   // 横屏状态1（MV=1,MX=1）
LCD_WR_REG(0x36); LCD_WR_DATA8(0xA8);   // 横屏状态2（MV=1,MY=1）
LCD_WR_REG(0x36); LCD_WR_DATA8(0xC8);   // 竖屏（MX=1,MY=1）
uint16_t to_big_endian(uint16_t v){
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  return ((v & 0xFF00) >> 8) | ((v & 0x00FF) << 8);   // ← 不交换则红显成绿
#else
  return v; #endif }
uint16_t c = to_big_endian(0x001F);      // 蓝色 RGB565；红色 = 0xF800
```
`⚠校核`：原文"试了很久无法显示红色，最后 `0x00f8` 才行"—— 那是**未做大小端交换的产物**，不是通用值；
且红蓝互换本质上是 `0x36` 的 bit3（BGR/RGB）问题，与大小端是**两个独立因素**，别混成一个技巧。
