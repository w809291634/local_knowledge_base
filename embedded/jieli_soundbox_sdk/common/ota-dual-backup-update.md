# 升级与 OTA：单/双备份、通道、参数与自定义协议

> 出处：`doc/功能模块说明文档/双备份配置说明.pdf`（**正文只有两个小标题，其余全是截图**）、
> `AC695N_app升级说明文档.pdf`（Rev1.0 2020-10-28，9 页；**1.1 原文写的是"AC696N 系列"，与文件名不符，疑笔误**）、
> `杰理蓝牙OTA协议.pdf`，以及 `include_lib/update/` 代码补证。

## 1. 升级通道有哪几种（文档只讲蓝牙 OTA，代码里有全表）

`UPDATA_TYPE` 枚举（`include_lib/update/update.h:22-38`）：**USB_UPDATA / SD0_UPDATA / SD1_UPDATA /
PC_UPDATA / UART_UPDATA / NORFLASH_UPDATA**，实现文件 `apps/common/update/uart_update.c`、`norflash_update.c`、
`testbox_update.c` 等。
**手册能力表写"升级 U盘 / SD"**。**USB/SD/串口升级的详细流程：文档未提及**，只有蓝牙 OTA 有完整章节。

通道是否可用由位掩码决定，**不要硬编码判断**：`config_update_mode`
（`include_lib/update/update_loader_download.h:115-118`：`UPDATE_BT_LMP_EN / STORAGE_DEV_EN / UART_EN / APP_EN`），
判定宏 `UPDATE_MODULE_IS_SUPPORT(x)`（`:8`）；双备份判定 `UPDATE_DUAL_BANK_IS_SUPPORT()`（`:10`）。

## 2. 单备份 vs 双备份

| | 单备份 | 双备份 |
|---|---|---|
| 原理 | 覆盖运行区，中途掉电有变砖风险，靠 uboot 重试 | 新固件烧到另一 bank，校验通过才切 boot info |
| 官方建议 | — | **Flash 空间够就建议双备份**（支持对耳同步升级，原文 p3） |
| 退出升级模式 | 单分区设备"最好返回失败" | 双分区可以支持（OTA 协议 p12） |
| 3.1.0 默认 | **`CONFIG_DOUBLE_BANK_ENABLE = 0`（单备份）**（`board_ac695x_smartbox.h:692`；`app升级 p3` 也写 0） | 需自己打开 |

### 双备份要改的两处（截图补全，文档正文没写）
1. **下载目录**：ini 里打开三项 `BR22_TWS_DB=YES;`、`FLASH_SIZE=1M;`、`BR22_TWS_VERSION=0;`，
   并**注释掉** `#NEW_FLASH_FS=YES;`（文件 `isd_config_app_ota.ini`）。同段可见 `CHIP_NAME=AC695X`、
   `ENTRY=0x1E00100`、`PID=AC695x_TWS`、`NEED_RESERVED_4K=YES;//关闭4K保留`，且 `[SYS_CFG_PARAM]` 标注
   **"UBOOT配置项，请勿随意调整顺序"**。
   单备份还要**额外加 `[EXIF]` 区**：`BITIF_ADDR=AUTO / BITIF_LEN=0x1000 / BITIF_OPT=1 /
   EXIF_ADDR=AUTO / EXIF_LEN=0x1000 / EXIF_OPT=1`（升级说明 p4）。
2. **SDK 侧**：`const int support_dual_bank_update_en = 1;`（注释"0-单备份;1-双备份"）。
   当前代码已改成条件式：`apps/soundbox/log_config/lib_update_config.c:24-29` 依 `CONFIG_DOUBLE_BANK_ENABLE` 取值。

### 回滚是怎么发生的（代码补证 `include_lib/update/dual_bank_updata_api.h`）
```
dual_bank_update_allow_check(fw_size)   // :25  先查空间够不够
   → 传输 → dual_bank_update_verify()   // :41  CRC16-CCITT 全量校验
   → dual_bank_update_burn_boot_info()  // :48  通过才给新 bank 烧 boot info
flash_update_clr_boot_info(u8 type)     // :60  type: CLEAR_APP_RUNNING_BANK=0 / CLEAR_APP_UPDATE_BANK
```
注释明确：**清掉运行 bank 的 boot info 后 `system_reset`，系统就会跑另一个 bank** —— 这就是回滚/切换路径。
地址一律用链接符号 `UPDATA_BEG / BOOT_STATUS_ADDR / UPDATA_FLAG_ADDR`（`update.h:6-9`），**不要写字面量**。

## 3. 蓝牙 OTA 的开启前提（升级说明 p3 §1.2.1）

板级 `board_ac695x_demo_cfg.h`（或所用板级）打开：`CONFIG_APP_BT_ENABLE`（注释"AI功能，流程总开关"）→
其下 `CONFIG_DOUBLE_BANK_ENABLE`、`RCSP_UPDATE_EN`、`OTA_TWS_SAME_TIME_ENABLE`、`UPDATE_MD5_ENABLE`、
`RCSP_FILE_OPT`、`JL_EARPHONE_APP_EN`、`TCFG_LFN_EN`、`TCFG_BS_DEV_PATH_EN`；
`SMART_BOX_EN`（rcsp 需要打开 ble）分支里这些为 1，else 分支**全为 0**。
另有 `support_norflash_update_en` 需先在 Board.h 开 `TCFG_NOR_FS_ENABLE`。

## 4. 服务器匹配参数：`json.txt`（p4 §1.2.2）

需要"弹窗升级/服务器查找"时改下载路径 `cpu/br23/tools/` 下的 `json.txt`：
- `ver_info` = **VID(2B) + PID(2B) + VER(2B)**，示例 `0x00,0x02,0x00,0x33,0x00,0x01`；
- `ver_info_ext` = **`AuthKey,ProCode`** 字符串，示例 `hE9yfFseX6UdK7rFh,jl_sdk_ac697_publish`；
  **AuthKey = 公司申请的标识 Key，ProCode = 产品代码**，VID/PID 按产品与版本号改；
- 还要在 `download.bat` 里用 `json_to_res.exe` 把它转成 `.dat`。

## 5. MD5 校验与 ufw 命名（p4-p5 §1.2.4）

开 `UPDATE_MD5_ENABLE` 后，服务器查找升级文件时会比对当前固件 MD5 与服务器 MD5 列表。
`download.bat` 需要：
```
if exist update_*.ufw del update_*.ufw
md5sum.exe app.bin md5.bin
set /p "themd5=" < "md5.bin"
copy jl_isd.ufw update_%themd5%.ufw
```
即 **ufw 文件名后缀带上固件 MD5**。原文红字警告：**"该步骤输出的文件名 res.bin 不能改变，否则升级或下载时找不到对应文件"**。

## 6. 让 OTA 打印出来（p5 §1.2.5）

tool 目录下有 `ota.bin` 与 `ota_debug.bin`：把 **`ota_debug.bin` 改名为 `ota.bin`**，
并在 `isd_config.ini` 里把 **`UTTX` 与 `UTBD`** 配成对应 IO 与波特率。

## 7. 客户自带协议做升级（p6-p7 §1.3）

开 `APP_UPDATE_EN`，并**实现三个接口注册给升级模块**：
`File_open`（初始化 `file_offset=0`、`seek_type=BT_SEEK_SET`）、
`File_read`（用 `data_send_hdl` 按偏移请求数据，pend 等结果或超时返错）、
`File_seek`（`SEEK_SET` / `SEEK_CUR`）。
参考实现：`apps/common/update/rcsp_ch_loader_download.c`，注册入口
`app_update_loader_downloader_init(update_type, result_cbk, NULL, &rcsp_tws_update_op)`，
协议流程参考 `apps/common/third_party_profile/JL_rcsp`。
**`update_tws.c` 实现 TWS 同步升级，客户不需要修改。**

## 8. 流程图差异（p8-p9 §1.4）

- **单备份**：APP 连接 → 发升级文件信息 → 升级校验（失败返错）→ **请求 ota_loader 数据 + 校验 ota_loader crc** →
  断开经典蓝牙和 ble → UBOOT/SPP/BLE 升级模式 → 等待重连（超时 → 判"固件可运行？"→ 是则重启，否则跳另一个升级模式；
  连接成功 → 开始升级 → 成功 → 退出 uboot）。
- **双备份**：APP 连接(BLE/SPP) → 发升级信息 → 信息校验 → 小机请求升级数据 → 等待接收（否则请求下一包）→
  接收完成 → **flash 新固件校验** → 失败返校验错 / 成功 → 进入 uboot 更新固件 →
  **"意外中断？"是 → 重启进入 uboot 重新更新固件**；否 → 更新成功、重启运行 APP。

## 9. 相关坑与限制

- 手册 p12：**升级后设备会重启，需要重新打开设备才能再次下发**；`UART 通讯不支持 ufw 更新`。
- 配置工具里的"升级"按钮**只用于验证，不会编译生成新 fw/ufw**（p14）；量产必须把改动整合成 fw 再用烧写器烧。
- 在线配置功能**本身增加约 3K RAM**。
- 三元组（AI 协议）烧在 **flash 最后 256 byte，OTA 不会擦除**（第三方 APP 协议 p27）。
- `DEV_UPDATE_SUPPORT_JUMP`（升级 IO 保持）**目前只有 br23/br25 支持**（`app_config.h:376`）。
- Android/iOS 官方 SDK：`github.com/Jieli-Tech/Android-JL_OTA`、`github.com/Jieli-Tech/iOS-JL_OTA`（p5）。
- 版本兼容的细粒度规则（向前/向后）：**文档未提及**，只给 VID/PID/VER + MD5 列表作为服务器匹配依据。
