# 协议接入：RCSP / 杰理 OTA / 第三方 AI 协议 / 涂鸦 / 天猫精灵

> 四份协议文档 + 代码核对的合并结论。共同特征：**发布版 SDK 里这些协议默认全部关闭**，
> 且彼此之间存在硬性互斥，选一条路就要关掉另一条。

## 0. 一句话选型

| 需求 | 走哪条 | 是否需要联网 |
|---|---|---|
| 自家 APP 只做控制+OTA | **RCSP（杰理蓝牙控制协议）** | 否，纯本地 BLE/SPP |
| 接第三方语音平台（天猫精灵/小爱/小度/酷狗/亚马逊） | **第三方 APP 通信协议（统一中间层）** | 平台侧需要，设备侧不需模组 |
| 接涂鸦生态 | **涂鸦 BLE 自研模组 SDK** | 通过涂鸦云 |
| 阿里 IoT 直连 Mesh | 天猫精灵 BLE **Mesh**（⚠ **不在本 SDK**，见 §4） | 需天猫精灵联网 |

## 1. 杰理蓝牙控制 / OTA 协议（RCSP）

- 载体：SPP + BLE 双模。**iOS 走 BLE OTA、Android 走 SPP OTA**；AC692x 默认 SPP、AC693x 默认 BLE（协议 p3）。
- **帧格式**（`include_lib/btstack/third_party/rcsp/JL_rcsp_packet.h:22-45`）：
  `tag[3] = {0xFE, 0xDC, 0xBA}` + HEAD 位域（Bit15 Type、Bit14 Response、Bit13-8 unused、Bit7-0 OpCode）
  + `u16 length` + data + 尾 `0xEF`。**大端**（`READ_BIG_U16/U32` 同文件 `:6-13`）。
  MTU：收 540 / 发 128。Command 包 Byte4=OpCode_SN、Byte5=Param2；Response 包 Byte5=Status（p7）。
- 常用 opcode（协议 p7-p15）：
  `0x03` GetTargetFeature（返回 BIT0 协议版本…BIT8 双备份+loader flag、BIT9 升级状态、BIT10 pid/vid）；
  `0x0B` 切 BLE/SPP；`0xE1` 取升级文件标识偏移；`0xE2` 是否可升级（00 可 / 01 电压低 / 02 信息错）；
  `0xE3` 进升级模式；`0xE4` 退出；`0xE5` 发数据块；`0xE6` 取升级状态（00 完成/01 校验错/02 失败/
  03 key 不匹配/04 文件错/05 uboot 不匹配/0x80 loader 下载成功）；`0xE7` 强制重启或关机；`0xE8` 通知升级总长。
  全量 opcode 表：`include_lib/btstack/third_party/rcsp/JL_rcsp_protocol.h:69-109`（含 0x07/0x08 系统信息读写、
  0x0E 功能命令、0x1B-0x20 文件传输/删除/改名、0xC0-0xC4 广播设置）。
- **升级文件标识头固定 10 字节**：+0/+1 VID、+2/+3 PID、+4/+5 版本号、+6~+9 文件长度；0x20a-0x20d 保留；
  末尾厂商自定义，原文建议"最好包含 CRC"（p11）。
- 开关位置：`apps/soundbox/board/br23/board_ac695x_smartbox.h:691-700`，`SMART_BOX_EN=1` 会带出
  `RCSP_UPDATE_EN=1`、`UPDATE_MD5_ENABLE=1`、`CONFIG_DOUBLE_BANK_ENABLE=0`、`OTA_TWS_SAME_TIME_ENABLE=0`。
  opcode 宏：`apps/common/third_party_profile/jieli/JL_rcsp/rcsp_updata/rcsp_adv_user_update.h:8-15`；
  实现：`apps/soundbox/smartbox/smartbox_update/smartbox_update.c`、`rcsp_ch_loader_download.c`。
- **⚠ 属性位限制**：BIT1/BIT3/BIT4/BIT6 明确"正常模式支持，**OTA 模式不支持**"（p8-9）。
- **⚠ 692x 与 693x 流程不同**：693x 多一步"请求 ota_loader 数据 + 校验 crc"（p6 红框），由 BIT8 loader flag 决定收不收 loader。
- **⚠ 文档页脚标的是 AC692X doc，正文只区分 AC692x/AC693x；AC695N 适用性文档未提及。**

### 杰理之家（smartbox）APP 侧的功能注册（手册 Ch5）
目录职责：`browser`=目录浏览、`bt_manage`=透传、`cmd_data_deal`=rcsp 交互、`func_cmd`=各模式功能、
`smartbox_setting`=功能设置、`smartbox_setting_opt`=公共功能设置操作、`smartbox_update`=OTA。
总开关 `CONFIG_APP_BT_ENABLE` + `SMART_BOX_EN 1`。
**自定义 opcode 只能用 `JL_OPCODE_CUSTOMER_USER = 0xFF`**，加在 `cmd_data_deal/cmd_user.c:smartbox_user_cmd_recieve`（p40）。
`JL_OPCODE_GET_TARGET_FEATURE` → `feature.c:target_feature_mask_get_tab`；
`SYS_INFO_GET/SET` → `function.c:target_common_function_get_tab / common_function_set_tab`。
公共设置项结构 `SMARTBOX_SETTING_OPT`（p42）必填 `data_len / setting_type(最大 31) / syscfg_id /
deal_opt_setting / set_setting / get_setting`，可选 `custom_setting_ini / release / vm_info_update / update /
sibling_setting_deal`；注册宏 `RESGISTER_APP_SETTING_OPT`；对外三接口
`set_smarbox_opt_setting`（**原文少一个 t，就是这个拼写**）/ `get_smartbox_opt_setting` / `smartbox_opt_release`。

## 2. 第三方 AI 协议统一中间层（屏蔽各家差异）

- 各家代号（p6/p16）：**GMA=阿里天猫、MMA=小米、DMA=百度、TME=腾讯酷狗、AMA=亚马逊**。
- 载体：BLE 固定 UUID 透传，可开 SPP（p8 `USER_SUPPORT_PROFILE_SPP=1`）；不需联网模组，语音助手依赖手机 APP。
- 开关：`apps/soundbox/include/app_protocol_api.h:17-32` 打开 `APP_PROTOCOL_xxx_CODE` +
  `APP_PROTOCOL_SPEECH_EN` / `READ_CFG_EN`，`HANDLER_ID` 范围 **0x300~0x800**；
  板级 `CONFIG_APP_BT_ENABLE` + `AI_APP_PROTOCOL=1`（p7）；`BT_MIC_EN` + `TCFG_ENC_OPUS/SPEEX_ENABLE`（p8）；
  `tone_cfg` 要加 `TDM2500`、准备 `tone_TM.cfg`（p9）。适配文件 `apps/soundbox/third_party_profile/app_protocol_deal.c`。
- 初始化顺序（p25）：`btstack_init` → `BT_STATUS_INIT_OK` → `app_protocol_init(GMA_HANDLER_ID)` →
  设参数/操作/回调 → 三元组 `gma_prev_init` → `app_protocol_tone_register` → `app_protocol_common_init` →
  `app_protocol_ota_init` → `loop_process`。
- **必须实现的 3 个结构体**（p16-18）：`app_protocol_info_t`、`app_ctrl_operation_t`、`callback_register_t`
  （成员 `message_handler_regedit` / `check_tws_role_is_master_register` / `tx_resume` / `rx_resume` / `get_battery`）。
- 公共消息（p11）：`CONNECTED_BLE/SPP`、`DISCONNECT`、`AUTH_PASS`、`SPEECH_START/STOP`、`SET/GET_VOLUME`、
  `LIB_TWS_DATA_SYNC`；OTA 消息（p12）：`OTA_CHECK / GET_APP_VERSION / CHECK_CRC / BEGIN / TRANS_DATA /
  PERCENT / END / SUCCESS / FAIL / CANCLE / REBOOT`。
- 坑：`APP_PROTOCOL_xxx_CODE` 宏注释写明"**不要在板级头文件重复定义**"（p9）；
  语音助手超时由 `APP_PROTOCOL_MIC_TIMEOUT` 决定，收到停止命令或 **8s** 超时停 mic/编码（p26）；
  三元组烧在 flash 最后 256 byte，OTA 不擦除（p27）。

## 3. 涂鸦（Tuya）BLE

- 设备以"**自研模组 SDK**"方式接涂鸦云，走 BLE。文档**未提及额外 WiFi 模组**。
- 开关：板级 `CONFIG_APP_BT_ENABLE` + `TUYA_DEMO_EN=1`（p9）。
- **必须填的三处**：`tuya_ble_app_demo.c:28-30` 的 `device_id_test / auth_key_test / mac_test`（对应授权码清单）
  与 `tuya_ble_app_demo.h:11` 的 `APP_PRODUCT_ID`（对应 pid）。**授权码与 pid 必须配对使用**（p7/p8）。
- 入口：`apps/soundbox/smartbox/tuya/tuya_demo.c:1184-1185 tuya_ble_app_init()`；
  回调 `tuya_cb_handler`（`TUYA_BLE_CB_EVT_DP_WRITE` → `tuya_data_parse`，p10）。
- **DP 帧**：`buf[0]=id、buf[1]=type、buf[2..3]=len(大端)、buf[4]=data`（p11）；
  按 `TUYA_BLE_PROTOCOL_VERSION_HIGN` 取 0x03 / 0x04 分别走 `tuya_ble_dp_data_report` / `tuya_ble_dp_data_send`。
  帧头/CRC 细节**文档未给**，指向外部《TUYA BLE SDK User Guide.pdf》5.10 节。
- **⚠ 互斥**：开 `TUYA_DEMO_EN` 时 `apps/common/config/include/bt_profile_cfg.h:20-24` 会**强制把
  `USER_SUPPORT_PROFILE_SPP` 置 0**，即涂鸦与 RCSP/SPP 互斥。
- **⚠ 型号相关**：涂鸦 port 目录里有 `tuya_ble_port_AD697x.c`（**AC697X** 命名），SDK 内涂鸦库是预编译
  `tuya_protocol/sdk/lib/libtuya_lib.a` —— 换芯片系列要确认这层 port 是否匹配。
- 若所选产品类型没有"自研模组 SDK"这种对接方式，**无法申请调试用授权码**（p5）——先确认平台侧产品类型再开工。

## 4. 天猫精灵：本 SDK 里只有 GMA，没有 Mesh

《soundbox天猫精灵使用说明》讲的是 **BLE Mesh**（按阿里 IoT"天猫精灵蓝牙 mesh 软件基础规范"把设备描述为**插座**），
需要天猫精灵连互联网 + 手机 APP 配网（p2）：`api/model_api.h` 设 `CONFIG_MESH_MODEL=SIG_MESH_ALIGENIE_SOCKET`；
板级 `apps/mesh/board/br23/board_ac635n_demo_cfg.h`；回调表 `gen_onoff_srv_op[]`
（`BT_MESH_MODEL_OP_GEN_ONOFF_GET/SET/SET_UNACK`）与 `vendor_srv_op[]`（`VENDOR_MSG_ATTR_GET/SET/CONFIRM`）。

**⚠ 该文档不属于本 soundbox SDK**：`api/model_api.h`、`apps/mesh/`、`board_ac635n_demo_cfg.h`、
`examples/AliGenie_socket.c` 在本工程内**全部不存在**，它对应的是杰理 BLE Mesh（AC635N/BR23）SDK。
本 soundbox SDK 里接"天猫精灵"只有 **GMA 协议**（§2）。

## 5. BLE 自定义 profile 的通用接法（不接任何平台，自己做 APP 时用）

- 协议栈接口：`include_lib/btstack/le/`（`att.h` / `ble_api.h` / `gatt.h` / `le_user.h` / `sm.h`），
  发送用 `ble_op_att_send_init` / `_send_data` / `_set_send_mtu` / `set_data_length`。
- 现成 demo：`apps/common/third_party_profile/jieli/trans_data_demo/le_trans_data.c`
  （按 `ATT_CHARACTERISTIC_ae01/02/03/04/05/10/3b/3c` handle 分支读写）、
  SPP 侧 `spp_trans_data.c` + `spp_data_deal_handle_register()`（`trans_data_demo.c:77,186`）。
- profile 选择在 `apps/common/config/include/bt_profile_cfg.h:46-77` 的 `TCFG_BLE_DEMO_SELECT`。
  **`AI_APP_PROTOCOL=1` 时会被强制改成 `DEF_BLE_DEMO_NULL`**（同文件 `:47-48`）。

## 6. 发布版默认状态与"只能一个连接"

`apps/soundbox/board/br23/board_ac695x_smartbox.h:662-675` 当前
`TRANS_DATA_EN / SMART_BOX_EN / TUYA_DEMO_EN / TRANS_MULTI_BLE_EN / TUYA_MULTI_BLE_EN / AI_APP_PROTOCOL`
**全部为 0**；`app_protocol_api.h:17-22` 各家 CODE 也全为 0。
**协议链表可以共存，但"协议只能支持一个连接"** —— 同一时刻发送只会有一个协议成功（p16-17）。
所有协议文档的配置截图都指向 `board_ac695x_smartbox.h`（br23 / smartbox 工程），
**换板级时这些开关要自己补**，demo 板级没有。
