# 在线配置工具与量产流程（杰理 soundbox SDK）

> 出处：`doc/音箱配置工具使用说明.pdf`（24 页）、两份 `.jlxproj` 入口文件、手册 p10 §1.4，代码核对。
> 一句话定位：**配置工具改"数据"，宏改"有没有这个模块 + 这项数据走不走配置文件"**。

## 1. 两个入口文件的本质：Lua 脚本，不是 URL

| 入口 | 路径 | 标题 | 差异 |
|---|---|---|---|
| 开发端 | `cpu/br23/tools/ac695x配置入口.jlxproj` | "AC695X-SDK" | 多传 `sdk.jcf -p cfg.dir -r rootDir -b cfg_tool.bin -t tone.cfg`，另有"路径"按钮 |
| 终端（给客户） | `客户终端使用工具 入口/给终端的入口文件.jlxproj` | "调音以及配置" | **不传上面那些参数** ⇒ 看不到开发端屏蔽的项 |

两者共同结构：`req_pkgs = {"efftool","sdktool","luaconfig","3rd","sdkaudiocvt"}`（`:18`），
用 `rootDir/pkgman.exe` 检查/更新依赖包，失败弹"软件包不是最新"；两个按钮：
- **配置工具** → 无参启动 `luaconfig`（产出 `cfg_tool.bin`）
- **调音工具** → `efftool --type atk`（产出 `eq_cfg_hw.bin`）

→ 遇到"工具打开看不到某个选项"先分清用的是哪个入口，而不是怀疑固件。

## 2. 工具能改哪些字段（说明 p7-p9、p11-p12）

工具版本样例：`LuaConfig - 20210105.7 (1.0.29) - Version: soundbox-1.0.0`。六大页：

- **蓝牙**：经典蓝牙名、新增/删除蓝牙、MAC(6B)、发射功率 0~10；BLE 名/MAC/功率；
  自动关机时间（分钟，0=不开）；TWS 配对码（2 字节）；
  晶振微调 `lrc_ws_inc 480`、`lrc_ws_init 400`、`bt_osc_ws_inc 480`、`bt_osc_ws_init 140`（us，范围 140~480）、
  `osc_change_mode`；"蓝牙配置恢复默认值"。
- **通话参数** / **MIC 参数** / **提示音** / **音量** / **设备信息**（在线读校验码与 SDK 版本）。

## 3. 生效路径（三处宏要对齐）

1. **固件侧允许工具连**：板级 `TCFG_SOUNDBOX_TOOL_ENABLE = ENABLE`、
   `TCFG_USB_COMM = 1` / `TCFG_UART_COMM = 2`（通信方式）、`TCFG_COMM_TYPE`、
   TX/RX = `IO_PORT_DP` / `IO_PORT_DM`（p23）。
   **UART 通讯方式不支持 ufw 更新**。
2. **固件侧允许配置覆盖编译值**：`user_cfg_new.c` 里
   `USE_CONFIG_AUDIO_SETTING / MIC_TYPE_SETTING / AUTO_OFF_SETTING = 0`、`USE_CONFIG_COMBINE_VOL_SETTING = 1`（p24）；
   手册 p10 §1.4：默认从配置文件读灯状态与提示音，不想读就把 `USE_CONFIG_STATUS_SETTING` 改 0；
   各 `USE_CONFIG_*_SETTING` 都等于 `USE_CONFIG_BIN_FILE`，全开就是 `#define USE_CONFIG_BIN_FILE 1`。
   兜底表在板级 `.c` 的 `STATUS_CONFIG status_config = {...}`（见 `config-three-layers-and-macro-mutex.md` §5）。
3. **成本**：p10 明确 **该功能增加约 3K RAM**。

## 4. 三种使用形态

| 形态 | 流程 | 用途 |
|---|---|---|
| 开发端 | 入口 → 改配置 → 保存 → **编译生成 fw/ufw** → 一起下载 | 定产品默认值 |
| 终端 + ufw | 打开 `.ufw` → 在线读 → 改 → 保存（可覆盖或另存新 ufw） | 小批量改参数 |
| 终端 无 ufw | 直连在线读/写 | 现场验证 |

**量产必须把改后的配置重新整合进 fw 再用烧写器烧录**；小批量可用工具自行升级。
**p14 红字：直接点"升级"只用于验证，不会编译生成新 fw/ufw。**
升级成功后设备重启，**必须重新"打开设备"才能再次下发**。

## 5. 权限屏蔽（给客户用的关键）

开发端"配置 → 选择可配置的选项"可屏蔽项，终端只显示/编辑被开放的项。
**该功能只在"下载目录的工具入口"有效，给终端的入口没有此功能**；
改动开放项后要**重新编译生成 ufw** 才生效。

## 6. 产物与文件

- 保存生成 **`cfg_tool.bin`** + **`tone.cfg`**（若用 ufw 打开则另生成新 ufw）。
- 这两个文件都是烧录命令里 `-res` 的入参：
  `isd_download.exe ... -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all`
  （见 `sdk-layout-build-and-flash.md` §4）。
- **文件名不能改**（改完烧录找不到对应文件），`res.bin` 那类中间文件名官方有明确红字警告。

## 7. 排查表

| 症状 | 先查 |
|---|---|
| 工具连不上设备 | `TCFG_SOUNDBOX_TOOL_ENABLE`、`TCFG_COMM_TYPE`、TX/RX 脚、115200；**不要勾"蓝牙串口"**（除非走 BT 透传） |
| 改了蓝牙名没生效 | `USE_CONFIG_*_SETTING` / `USE_CONFIG_BIN_FILE` 是否让它走配置文件；有没有重新烧 `cfg_tool.bin` |
| 终端看不到某项 | 用的是终端入口还是开发端入口；开发端有没有屏蔽 |
| 升级后参数丢 | 直接"升级"不生成新 fw；需要重新整合 fw/ufw 后烧录 |
| RAM 不够 | 在线配置本身约 3K RAM，先关掉不用的通道 |
