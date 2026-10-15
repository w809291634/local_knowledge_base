# 调试器固件与驱动：J-Link V8 刷固件 / 序列号 / WCH-Link / ST-LINK

> 适用：J-Link（V8 实测）、WCH-Link、ST-LINK 的驱动安装与救砖
> 来源：《问题解决和汇总 v1.2》"jlink / 更新Jlink固件 / ST LINK 刷固件 / WCH-LINKE"章节
> 目标：调试器"连不上/变砖/提示 defective"时的完整处置流程。

## 结论先行

- J-Link V8（AT91SAM7S64）救砖三步：**短接 ERASE 擦除 → 短接 TST 进 SAM-BA Boot → SAM-BA 2.12 烧固件**；烧写提示锁定 flash 时**选 No**（选 Yes 以后无法再升级固件）。
- WCH-Link 两个接口两个驱动：接口 0 用 **WinUSB**（能刷出 DAP-Link），接口 1 用 USB 串口驱动（**zadig** 安装），装完用管理员运行驱动工具，GET 能显示 OK 才算正常。
- "the connected j-link is defective" 多半是**用非官方途径升级固件**（如在 RT-Thread Studio 里升级）造成的，用官方 exe 升级可避免。

## 1. J-Link V8 刷固件（救砖全流程）

### 1.1 工具

- **SAM-BA v2.12**：注意 v2.9 在 Win10 64 位上无法正确连接；
- J-Link V8 固件文件；
- 最新 J-Link 驱动（segger 官网）。

### 1.2 擦除（短接 ERASE）

1. 断开 J-Link 与电脑 USB；2. 短接板上 ERASE；3. 接 USB 供电；4. 等约 10 秒（有说 2 分钟）；5. 断开 USB；6. 断开短接。

### 1.3 进入 SAM-BA Boot（短接 TST）

同上流程，把 ERASE 换成 TST。板上有 A=擦除、B=TST 两个短接点。

### 1.4 烧录

- 装好 SAM-BA 2.12 后重连，Win10 自动装驱动（"Bossa program Port" 或 "USB Serial Device"；没有就回滚/更新驱动）；
- 打开 sam-ba_2.12，选 COM 口、芯片型号（默认 at91sam7s64）、Connect；
- 烧写提示"是否锁定 flash"：**点 Yes 会锁定固件、之后无法更新** → 一般选 **No**。

## 2. J-Link 序列号

- 序列号全改成 F 会显示为 -1，此时可用命令行重新赋值；
- J-Link Commander 里：`Exec SetSn = 01234567`（也可 `exec setsn=XXXXXXXX`）。

## 3. 常见报错

| 报错/现象 | 处理 |
|---|---|
| 指示灯快速闪烁、无法下载 | 换 USB 口（部分 USB 口不兼容） |
| `the connected j-link is defective` | 用 RT-Thread Studio 等非官方途径升级固件导致；临时解法是用 4.62/破解版（D 版）里的 `JLinkARM.dll` 替换安装目录同名文件；根治是用官方升级 exe 升固件 |
| `ERROR: Could not find CFI compliant flash device` | 驱动别用 6.30d 版；且选择目标设备时 flash/RAM 大小必须与真实 MCU 一致，不一致说明软件侧选型有误 |
| 升级成功的标志 | 官方 exe 升级过程中无报错提示即为正常，报错多为硬件问题 |
| F103 无法调试，`FAILED TO GET CPU status after 4 retries` | 注释代码中相应的调试配置语句后恢复（详见原文档截图） |

## 4. WCH-Link 驱动安装

- 一个调试接口 + 一个串口：**接口 0 用 WinUSB 驱动**（设备管理器左图模式，能枚举出 DAP-Link）；**接口 1 用 USB 串口驱动**（右图 RV 模式），用 `zadig-2.9.exe` 安装；
- ARM 调试器驱动用 `WCH-LinkUtility/Drv_Link` 安装；
- 更换驱动后**用管理员身份运行**驱动工具；验证标准：GET 能显示 OK、参数可设置。

## 5. ST-LINK

- 刷固件方法见《公司设备相关基础知识》手册（本文档不重复）。
