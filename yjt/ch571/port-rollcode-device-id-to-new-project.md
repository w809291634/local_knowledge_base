# 移植实战：把「滚码设备 ID」落到一个新 CH571 工程（ZY0_BLE_CH571）

> 适用：沁恒 CH573/CH57x + WCH BLE 协议栈（MounRiver Studio 2.5.0、letter-shell 控制台）
> 参考源：01KJN2601001（BD1，`OnlyUpdateApp_Peripheral - V1.0.5`）
> 目标工程：`ZY0_BLE_CH571`（型号前缀 `ZY0`）
> 配套文档：机制与格式见 [CH571（CH57x）BLE 设备 ID：滚码 NV 格式、控制台/BLE 写法与校验](./ble-device-id-rollcode-nv.md)；本篇只讲**怎么搬、搬哪里、搬完怎么验**。

## 结论先行

移植的实质是「**新增一个独立 DataFlash 页放 6 字节滚码 + 三条写入通道共用一套写/读函数**」。
真正容易翻车的不是业务逻辑，而是三件事：① 新页和已有 NV 区**不重叠**（擦除粒度 256 B，`NV_Write` 只会擦你传的那一页，但结构体一旦长胖就会越界）；② 排序上**先写 ID 再复位**才生效；③ 参考工程的有效性判据（`raw[0] == 0` 即无效）会让「序列号低字节为 0」的片被判成未烧录。

## 1. 移植前必须先查清的四件事

1. **目标工程的 DataFlash 分区**：把工程里所有落 DataFlash 的出口穷举出来（`Grep` 搜 `EEPROM_`、`NV_`、`DataFlash`、`FLASH_ROM_MAX_SIZE`）。ZY0 的结论是三处：应用 NV `@0x0000`、BLE SNV `@0x7E00+`、校准走寄存器不落 flash。
2. **擦除粒度**：`EEPROM_PAGE_SIZE = 256`。选地址按页对齐，就不会误擦邻居。
3. **目标工程有没有现成的「设备名」逻辑**：ZY0 原本把广播名存在 NV 结构体里（`adv_name[]`）。要先决定「复用」还是「废弃」。
4. **广播名在哪里被消费**：ZY0 是 `Peripheral_Init` 里填 `advName[]` → GAP 名 + 扫描响应，**只在开机时做一次**，所以写完 ID 必须复位。

## 2. 三个关键决策（本次实际取舍）

| 决策点 | 选择 | 理由 |
|---|---|---|
| 原 NV 里的 `adv_name` | **废弃，字段改 `reserved[18]` 占位** | 维持结构体布局不变 → 不用递增 `NV_APP_VERSION`、不触发老机器 NV 重置 |
| 名字格式 | 与参考工程完全一致，只把型号段换成 `ZY0` | 手机端/量产脚本无需改格式 |
| BLE 通道 | 沿用 `0xF4`，**无应答**，写成功后**打印新名 + 自动复位** | 与参考工程命令字一致；无应答即无需回包，复位不会被拖住 |

> 若选「递增 NV 版本」替代「占位」：优点是结构体可自由改；代价是现场老设备 NV 会被判无效并回默认值（门店模式、同步时间戳全丢）。量产后不要改。

## 3. 分区规划与"互不干涉"的强制手段

```
DataFlash 用户区 0x00070000 ~ 0x00077FFF（32 K）
├─ 应用 NV      偏移 0x0000 ~ 0x00FF   整页，统一结构体 app_nv_cfg_t
├─ 设备 ID      偏移 0x0100 ~ 0x0105   只用 6 B，占独立整页
└─ BLE SNV      偏移 0x7E00 起         协议栈占用，勿碰
```

`NV_Write(offset, buf, len)` 只检查 `offset + len <= 0x8000`，**它不认识分区**。所以「不越界」不能靠注释，要靠编译期断言封死：

```c
/* 应用 NV 区不得越入设备 ID 页：若结构体长胖到 >256 B，
 * NV_Write(0x0000, …) 的页擦除会连带擦掉设备 ID。 */
typedef char board_cfg_nv_region_no_overlap[
    ((BOARD_CFG_NV_DFLASH_OFFSET + BOARD_CFG_NV_AREA_SIZE) <= BOARD_CFG_DEV_ID_DFLASH_OFFSET) ? 1 : -1];

/* 统一 NV 结构体不得超出应用 NV 区（同一条约束的另一半）。 */
typedef char nv_app_cfg_size_within_area[(sizeof(app_nv_cfg_t) <= BOARD_CFG_NV_AREA_SIZE) ? 1 : -1];
```

违规时报错形如 `size of array 'nv_app_cfg_size_within_area' is negative`，一眼看出是哪个约束破了。C99 下用不了 `_Static_assert`，这个 `typedef char[cond?1:-1]` 惯用法最省事。

## 4. 改动清单（8 个源文件 + 文档）

| 文件 | 改法 |
|---|---|
| `APP/include/board_config.h` | 新增 `BOARD_CFG_DEV_ID_DFLASH_OFFSET/BYTES/DEV_NAME_TYPE`；加编译期断言；把滚码布局、三种设置方式、BLE 帧示例写成注释块 |
| `APP/nv/nv_app.h` | `adv_name[]` → `reserved[]` 占位；API 增 `NvApp_GetDeviceId/SetDeviceId/GetDeviceName/SetDeviceIdAndReboot`，删 `GetAdvName/SetAdvName` |
| `APP/nv/nv_app.c` | 实现 `nv_dev_id_valid` + 读/写（擦页→写→读回 `memcmp`）+ 名字派生（`snprintf`）+ 写后复位 |
| `APP/nv/nv_shell.c` | 导出 `id` 命令：查询恒可用；设置分支包在 `#if BOARD_CFG_NV_SET_CMD_ENABLE` |
| `APP/apl_shell/letter_shell_cmd.c` | 删掉旧的 `setname/getname` 命令；`sysinfo` 改用 `NvApp_GetDeviceName` |
| `APP/peripheral.c` | `Peripheral_Init` 用 `NvApp_GetDeviceName()` 覆盖默认广播名 |
| `APP/protocol/app_protocol.h` | 加 `APP_PROTO_CMD_DEV_ID_REQ 0xF4` |
| `APP/protocol/app_protocol_ble.c` | 加 `ble_handle_dev_id()` 与 `switch` 分支 |
| `docs/**` | 文档里的设备名来源同步（默认名 / 滚码派生） |

**共用性**：三条通道（烧录器/控制台/BLE）写的是同一份数据、同一个函数。把「写 ID → 打印新名 → 复位」封成一个接口，串口和 BLE 都调它，避免两处各写一份：

```c
/* 写设备标识并复位生效：成功则先打印派生广播名，再软复位。
 * 串口 id 命令与 BLE 0xF4 共用；失败返回 -1（不复位，提示由调用方给出）。 */
int NvApp_SetDeviceIdAndReboot(const uint8_t raw[BOARD_CFG_DEV_ID_BYTES])
{
    char name[BOARD_CFG_NV_NAME_MAX + 1];

    if(NvApp_SetDeviceId(raw) != 0)          /* 擦页 → 写 → 读回核验 */
        return -1;
    if(NvApp_GetDeviceName(name, sizeof(name)) != 0)
        name[0] = '\0';
    log_i("id:%s", name);                    /* 复位前先把新名打出来 */
    SYS_ResetExecute();
    return 0;
}
```

## 5. 验证方法（不能整体编译时怎么验）

本次 `obj/*.mk` 里残留旧绝对路径，整体 `make` 跑不通，改用**逐文件真参数语法检查**：从 `obj/APP/nv/subdir.mk` 里抄出真实的 `-I` 与编译选项，逐个文件 `-fsyntax-only`：

```powershell
$gcc = '...\MounRiver_Studio2\...\RISC-V Embedded GCC\bin\riscv-none-embed-gcc.exe'
& $gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore `
       -Os -fsigned-char -ffunction-sections -fdata-sections -fno-common -g `
       -I".../SRC/Startup" -I".../APP/include" -I".../Profile/include" `
       -I".../SRC/StdPeriphDriver/inc" -I".../BLE/HAL/include" -I".../SRC/Ld" `
       -I".../BLE/LIB" -I".../SRC/RVMSIS" -I".../APP" -std=gnu99 -Wall -fsyntax-only <file.c>
```

三个补充技巧：

- **被测分支被 release 裁掉怎么办**：`BOARD_CFG_RELEASE` 在头文件里硬编码，`-D` 覆盖不了。把文件复制一份，`#if BOARD_CFG_NV_SET_CMD_ENABLE` 临时改成 `#if 1` 再编，编完删掉。
- **断言真的生效吗**：故意把条件改假，确认报 `size of array '…' is negative`，再改回来。
- **`sizeof(结构体)` 实测**：`-S` 出汇编，看 `li a0,36` 之类的立即数即可（本次 `app_nv_cfg_t` = 36 B，远小于 256 B）。

最后仍需真机确认：BLE 发 `0xF4` 帧 → 串口打出 `id:2026xxxx_ZY0xxxxx` → 设备重启 → 新广播名出现。

## 6. 踩坑记录

1. **`SYS_ResetExecute()` 要连 `CONFIG.h` 一起包含**：只写 `#include "CH57x_sys.h"` 会报 `unknown type name 'SYS_CLKTypeDef'`（它依赖寄存器定义）。两个头都要。
2. **`CONFIG.h` 实际路径是 `BLE/HAL/include/config.h`**，靠 Windows 大小写不敏感才能命中；写 `-I` 时别写成 `Peripheral/HAL/include`。
3. **release 下未使用告警**：`id_hex()` 只在设置分支用，release 把它裁掉后会变成未使用函数。把 helper 也一起包进 `#if BOARD_CFG_NV_SET_CMD_ENABLE`。
4. **写完 ID 广播名不会立刻变**：名字在 `Peripheral_Init` 里才生成，必须复位。所以不要"写完就扫"，控制台查询到的新名≠当前广播名。
5. **序列号从 1 开始**：有效性判据只看 `raw[0]`，`…00` 结尾（第 0、256、512 片）会被判为未烧录。更稳的做法是「只有全 `0xFF` 才算空」。
6. **打印后立即复位不会截断**：stdout 无缓冲（`setvbuf(stdout, NULL, _IONBF, 0)`），USB CDC 是阻塞发送，字节发完才复位。
7. **BLE 写 ID 用 Write Request 时，复位会让 App 端看到一次无响应/断连**——ID 已保存生效，属"设置后立即重启"的固有表现，量产 App 需容忍。

## 7. 量产侧待确认项

- 烧录器填的是**相对偏移 `0x100`** 还是**绝对地址 `0x70100`**（参考文档写 `0x100`，本工程一致）。
- 4 KB 块擦除粒度对应用 NV 的影响：本次三区都按 256 B 页对齐，理论安全，但烧录器若按块整片擦，需要确认擦除范围是否覆盖到应用 NV。

## 8. 一次性核查清单（下次直接照抄）

1. 穷举 DataFlash 出口 → 画分区表 → 选一个**整页**放 ID。
2. 加两道编译期断言（区不重叠 + 结构体不超区）。
3. 写 `Get/SetDeviceId`（擦→写→读回 `memcmp`）+ `GetDeviceName`（模板集中一处）。
4. 把「写 ID → 打印新名 → 复位」封成一个接口，三条通道共用。
5. `id` 命令：查询恒可用，设置受 release 宏控制。
6. BLE 命令分发加 `0xF4`（先过帧校验 → 写 → 打印 → 复位）。
7. `Peripheral_Init` 里用派生名覆盖默认广播名。
8. 逐文件 `-fsyntax-only` 验（含被 release 裁掉的分支）→ 真机验一遍改 ID 后重启生效。