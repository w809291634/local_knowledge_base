# ZigBee / Z-Stack 的 OSAL 运行机制与工程实践

> 版本区分：文档同时覆盖 **Z-Stack 2.4.0-1.4.0x** 与 **Z-Stack 3.0.2**，两者差异已在条目里写明。
> `⚠校核` 见 `embedded/mcu-peripherals/ERRATA-*.md`。
> 这一篇的**运行机制部分**（§1）是跨项目可复用的；§4/§5 的帧协议与公司工程做法只作线索（属项目事实，不入库）。

## 1. OSAL 运行机制（核心，值得反复读）

| 机制 | 结论（原型照抄） |
|---|---|
| 任务表 | `const pTaskEventHandlerFn tasksArr[]`，顺序为 mac → nwk → Hal → MT → APS → ZDApp → SAPI/App；`tasksCnt = sizeof/sizeof` |
| 事件集 | `uint16 *tasksEvents`：**每个任务一个 16 位事件集**（按位） |
| 任务号与优先级 | `osalInitTasks()` 里 `taskID++` 的顺序 **就是优先级顺序（0 最高）** |
| **主循环** | `osal_run_system()`：先 `osalTimeUpdate(); Hal_ProcessPoll();`，再从 idx=0 找**第一个 `tasksEvents[idx] != 0`** 的任务；取走事件并清零 → `(tasksArr[idx])(idx, events)` → 返回值 `\|=` 写回（**没处理完的事件下一轮再来**） |
| **一轮只处理一个任务** | ⇒ 任何任务的处理函数里做长耗时操作，会让别的任务饿到 —— 这是 Z-Stack"卡死/丢包"类问题的第一嫌疑 |
| 空闲 | 无事件时进 `osal_pwrmgr_powerconserve()` 休眠（`POWER_SAVING` 宏控制） |
| 事件设置 | `osal_set_event(task_id, flag)` 按位或；**`SYS_EVENT_MSG = 0x8000` 被系统占用** ⇒ **自定义事件只剩 15 个位（0x0001~0x4000）** |
| SAPI 事件占用 | `ZB_ALLOW_BIND_TIMER 0x4000`、`ZB_BIND_TIMER 0x2000`、`ZB_ENTRY_EVENT 0x1000`、`ZB_USER_EVENTS 0x00FF` ⇒ **实际留给用户的只有 8 个位** |
| **消息队列** | 全局**单链表 `osal_qHead`**，长度不限（内存够即可）；`osal_msg_send(dest, msg)` 入队并**自动** `osal_set_event(dest, SYS_EVENT_MSG)`；`osal_msg_receive(task_id)` 一次最多取 **2 条**，剩余 >0 再置事件、=0 清事件 |
| 消息头 | `osal_msg_hdr_t{next, len, dest_id}` 由 `osal_msg_allocate` 附加；**接收方必须 `osal_msg_deallocate`**（否则堆耗尽） |
| 定时器 | `osal_start_timerEx(taskID, event_id, ms)` / `osal_start_reload_timer` 是**软定时器**：到期 = 置事件，**不会打断当前执行** ⇒ 精度取决于主循环忙闲 |
| 串口收发 | 中断/缓冲层只搬数据，**处理仍靠 `Hal_ProcessPoll → HalUARTPoll → uartCB` 轮询回调** ⇒ 关掉 POWER_SAVING 或阻塞主循环都会让串口"看起来丢数据" |
| 内存 | `osal_mem_alloc/free`；堆余量指标 `osal_heap_block_free()` 等需 `OSALMEM_METRICS = TRUE`；**协调器的 `osal_mem_set_heap` 不可设 0x200（会重启），建议 0x250** |

**迁移到其他"轮询 + 事件位"框架（如杰理 sys_event、AT32 的 tmr 方案）时的通用判据**：
事件位是**有限资源**（16 位）、一轮只跑一个任务、软定时器不是硬实时 —— 这三条决定架构上限。

## 2. ZigBee 概念与端点/地址（通用）

| 项 | 内容 |
|---|---|
| 端点 EP | **0 = ZDO**；**1~240 = 用户**；241~254 保留；**255 = 广播到所有端点** |
| 地址 | `0xFFFF` 广播全部；`0xFFFD` 只发给 rx-on-when-idle；`0xFFFC` 发给 ZC+ZR |
| 例值 | `SAMPLESW_ENDPOINT 8`、Profile `ZCL_HA_PROFILE_ID` |
| 节点类型 | `ZCD_NV_LOGICAL_TYPE = 0x0087`：0=ZC / 1=ZR / 2=ZED；**类型与固件不符会写入并重启**（首启 LED 闪 2 次的成因） |
| 启动选项 | `ZCD_NV_STARTUP_OPTION = 0x0003`：bit0 清配置、bit1 清状态、**bit2 = 0x04 为 AUTO_START** |
| 是否入网 | **不调 `zb_StartRequest()` 就不会入网** |

## 3. 应用框架 API（AF / SAPI）

```c
afStatus_t AF_DataRequest(afAddrType_t *dstAddr, endPointDesc_t *srcEP, uint16 cID, uint16 len,
                          uint8 *buf, uint8 *transID, uint8 options, uint8 radius);
```
- `endPointDesc_t{ endPoint, *task_id, *simpleDesc, latencyReq }`；注册用 `afRegister()`
  （3.0.2 里是 `bdb_RegisterSimpleDescriptor()`）。
- **SAPI 版**：`zb_SendDataRequest(dest, cmd, len, pData, handle, txOptions, radius)`，
  `dest` 可用 `ZB_BINDING_ADDR` 走绑定。
- 三类必处理的系统消息：
  | 消息 | 含义 | 条件 |
  |---|---|---|
  | `AF_INCOMING_MSG_CMD` | 收到数据 | — |
  | `AF_DATA_CONFIRM_CMD` | 发出去的 **ACK 确认** | **options 必须带 `AF_ACK_REQUEST`**，否则不会有确认 |
  | `ZDO_STATE_CHANGE` | 入网/网络状态变化 | 判断 `ZDC_STATE_JOINED` 等 |
  | `ZDO_CB_MSG` | ZDO 响应回调 | 需 `ZDO_RegisterForZDOMsg` 注册 `NWK_addr_rsp` / `Match_Desc_rsp` / `IEEE_addr_rsp` |
- 读 NV：`zb_ReadConfiguration/zb_WriteConfiguration` → 底层 `osal_nv_read(id, offset, len, buf)`。
- 查地址：`NWK_Cmd(NWK_GET_NWK_ADDR_REQ)` 类流程（"查询节点网络地址与 MAC 地址"在文档里走 IEEE_addr_rsp 回调）。

## 4. 协调器 ↔ 上位机（MT 层）的机制（通用部分）

| 项 | 内容 |
|---|---|
| 收帧状态机 | `MT_UartProcessZToolData`：`SOP → LEN → CMD1 → CMD2 → DATA → FCS`，校验通过后 `osal_msg_send(App_TaskID)` |
| 分发 | `mtProcessIncoming[]` 按 **CMD0 的子系统号** 分发，**APP 子系统 = 序号 9** |
| 端点转换 | `MT_AppMsg` 取数据首字节作为端点 → `afFindEndPointDesc` → 转投 SAPI 任务 |
| 无线转发 | `zb_HanderMsg` 中 `dAddr == 0 或 0xffff` 走 `processCommand`，否则 `zb_SendDataRequest` 转发 |
| 帧格式概念 | `SOP(1) + LEN(1，指 DATA 长度) + CMD(2) + DATA(N) + FCS(1，从 LEN 起异或)` |
| `⚠校核C` | 文档协议表的表头把 LEN 写成两字节宽，容易误读为 LEN 占 2B；**实际 LEN 是 1 字节**（示例帧逐字节验证） |
| 具体命令字（2900/6900/6980 等）与公司上位机协议 | **项目事实，不入库**；需要时看原 docx 的公司章节 |

## 5. 工程适配与版本差异（实战清单）

### 2.4.0-1.4.0x（老，SampleApp 系）
- 公司工程基于 **SimpleApp**；**高版本 SDK 可能没有 Samples 工程示例** ⇒ 别指望新版本里能找到同款模板。
- 端点描述符、`endPointDesc_t` 结构差异较大（相对 3.0.2）。

### 3.0.2（新，必须改的 6 处）
| # | 要做的事 | 不做的后果 |
|---|---|---|
| 1 | GenericApp 必须加 **`FEATURE_RESET_MACRO`** | **卡死** |
| 2 | 打开 `xNV_RESTORE`（**注意 `x` 前缀语义按工程约定**）+ `ZTOOL_P1 / MT_TASK / MT_APP_FUNC / MT_SYS_FUNC` | MT 串口命令不响应 |
| 3 | 关 `ZCL_SCENES`、`ZCL_GROUPS` | 省 **9KB RAM**（小 RAM 芯片必做） |
| 4 | 闭源库要成对换：`Router-Pro.lib` ↔ `EndDevice-Pro.lib` | **换错库 → `status: 0xcd`**（作者注"具体原因未知"，未验证） |
| 5 | 打开 **`TC_LINKKEY_JOIN`** | 不打开 ⇒ STEERING 永远 `IN_PROGRESS`（连不上） |
| 6 | 改频道/PANID 用 **`bdb_setFN()`**（置 `bdbNodeIsOnANetwork=false` + FN 标记），不要用 `bdb_setChannel` | 频道恒为 27（因为 `bdb_setChannel` 会强写 `zgDefaultChannelList`，即 27 号掩码 `0x04000000` 的来源）⇒ **formation 失败** |

### 与看门狗的时间冲突
`ZDApp_RestoreNetworkState()` 耗时约 **7s**，而看门狗 `WDTIMX` 设的是 2s ⇒ **会在恢复网络状态期间被踢复位**。
任何"上电后长时间初始化"的工程都要按这条重新核算喂狗。

## 6. 截图层补充 · 第 2 章 053–106（2026-10-16 逐张读）

> `（ch02/0NN）` = 导出截图序号；图与所属小标题的对应见 `Temp/mcu_doc/media/ch02/INDEX.tsv`。
> 只录文字层没有的唯一副本。截图分辨率有限，**看不清处一律标出、不补全**。

### 6.1 分层图与端点号（ch02/053、054）

- 分层自上而下：`ZCL` → `Application Framework (AF)`（红框，左跨 `Base Device Behavior (BDB)`）→ `APS` → `Network Layer`
  → `IEEE 802.15.4: MAC` → `IEEE 802.15.4: PHY`；AF 框内 `ZigBee Device Object (ZDO) EndPoint 0`、
  `Device Application Endpinoint 1`（**原文如此拼写**）、`Device Application EndPoint 240`。
- 端点号图：左"协调器 网络地址 0"、右"终端 网络地址 0x0EF1、端点号 8"，中间双向箭头
  ⇒ §2 的"1~240 用户端点"在图里以 `0x01~0xEF` 表述，**两处边界口径不同但都落在 240 以内**，用前按工程 `endPointDesc` 实际值。

### 6.2 `osal_init_system()` 的真实调用序列（ch02/055，唯一副本）

```c
uint8 osal_init_system( void )
{
  osal_mem_init();            // Initialize the Memory Allocation System
  osal_qHead = NULL;          // Initialize the message queue
  osalTimerInit();            // Initialize the timers
  osal_pwrmgr_init();         // Initialize the Power Management System
  osalInitTasks();            // Initialize the system tasks.
  osal_mem_kick();            // Setup efficient search for the first fr…（行尾截图不清）
  return ( SUCCESS );
}
```
⇒ 顺序里 **`osal_qHead = NULL` 在 `osalInitTasks()` 之前**：消息队列先于任务建立，
所以任何 `osal_msg_send` 都发生在任务表就绪之后 —— 排查"启动期丢消息"时不必怀疑队列没建。

### 6.3 `osalInitTasks()` 与 taskID 分配图（ch02/056、057、060、061、068、069）

```c
void osalInitTasks( void )            // ch02/056，sapuc.c 行 1023-1038
{
  uint8 taskID = 0;
  tasksEvents = (uint16 *)osal_mem_alloc( sizeof(uint16) * tasksCnt );   // ch02/060 绿框
  osal_memset( tasksEvents, 0, (sizeof(uint16) * tasksCnt) );
  macTaskInit( taskID++ );
  nwk_init( taskID++ );
  Hal_Init( taskID++ );
#if defined( MT_TASK )
  MT_TaskInit( taskID++ );
#endif
  APS_Init( taskID++ );
  ZDApp_Init( taskID++ );
  SAP?_Init( taskID );               // 末行函数名截图不清（057 同位置红框是 SampleApp_Init(taskID)）
}
```
- **taskID 对照图**（ch02/069，唯一副本）：`macTaskInit=0`、`nwk_init=1`、`Hal_Init=2`、`MT_TaskInit=3`、
  `APS_Init=4`、`ZDApp_Init=5`、**`SAPI_Init=6`**；右侧注明
  "通过 taskID 确定任务处理函数 `tasksArr[taskID]`"、"通过 taskID 确定任务的事件 `tasksEvents[taskID]`"。
  ⇒ §1"taskID 顺序 = 优先级"的**权威图证**；且 `MT_TaskInit` 受 `MT_TASK` 宏控制 ⇒ **不开 MT 时后面所有任务的号整体前移 1**，
  对照 callstack 时必须先确认工程的 `MT_TASK` 开关。
- ch02/057 的 `OSAL_SampleApp.c` 版本里还有 `#if defined( ZIGBEE_FRAGMENTATION …`、`#if defined( ZIGBEE_FREQ_AGILITY …`、
  `ZDNwkMgr…` 三个条件项 ⇒ **任务表项数随宏变**，不是固定 7 项。
- **`tasksArr[]` 的函数名**（ch02/065，唯一副本）：
  `{ macEventLoop, nwk_event_loop, Hal_ProcessEvent, /*#if MT_TASK*/ MT_ProcessEvent, APS_event_loop, ZDApp_event_loop, … }`
  ⇒ 注意**注册的是 `xxx_event_loop` / `xxx_ProcessEvent` 系列**，与 `osalInitTasks` 里的 `xxx_Init` 成对；
  文字层若出现 `macTaskEventHandler` 之类命名，属另一版（3.0.2）或记忆偏差，**以工程源码为准**。

### 6.4 事件数组在内存里长什么样（ch02/061、063、064，唯一副本）

- ch02/061 Watch：`tasksEvents = 0x0da (theheap + 2)` ⇒ **事件数组就是堆开头的块**，改堆大小会挪动它的地址。
- ch02/063 结构图：`tasksEvents` 指向 `0X0DA4`，按 `uint16` 逐项排：
  | idx | 地址 | hex | dec |
  |---|---|---|---|
  | 0 | 0X0DA4 | 0000 | 0 |
  | 1 | 0X0DA6 | 0110 | 272 |
  | 2 | 0X0DA8 | 0003 | 3 |
  | 3 | 0X0DAA | 0000 | 0 |
  | 4 | 0X0DAC | 0000 | 0 |
  | 5 | 0X0DAE | 1000 | 4096 |
  图顶部标"优先级高 → 极低"，并注明"任务队列 uint16 型 / `tasksEvents[idx]` 数据值"。
  ⇒ **实用判据**：调试时直接在 Memory 窗口看这一串 `uint16`，**哪个位置非 0 就是哪个任务有事件没处理完**；
  `0x1000` 出现在 idx=5（ZDApp）即 `ZB_ENTRY_EVENT` 位形态，可反推是谁在挂事件。
- ch02/060/064 的 Watch 里 `idx / tasksEvents[idx] / events` 显示
  `Error (col 1): Unknown or ambiguous symbol.` ⇒ **优化级下局部变量常被优化掉，Watch 看不到不等于没执行**，
  要看就得降优化等级或看汇编。

### 6.5 主循环与"未处理事件"的确切写法（ch02/059、062、066）

```c
void osal_run_system( void)                 // ch02/062，行 1041 起
{
  uint8 idx = 0;
  osalTimeUpdate();
  Hal_ProcessPoll();                        // This replaces MT_SerialPoll() and osal_check_time…
  do {
    if ( !tasksEvents[idx] )                // Task is highest priority tha…（红箭头指向这里）
      break;
  } while (++idx < tasksCnt);               // 红箭头指向 ++idx
  if (idx < tasksCnt) { … }
```
```c
// ch02/059，行 1062-1088（取事件 → 调用 → 写回，全程关中断）
HAL_ENTER_CRITICAL_SECTION(state);
events = tasksEvents[idx];      // Get the events for this task，是第 idx 个任务的事件发生了
tasksEvents[idx] = 0;           // Clear the Events for this task.
HAL_EXIT_CRITICAL_SECTION(state);
events = (tasksArr[idx])( idx, events );   // 绿框：对应用第 idx 个任务的事件处理函数，用 events 说明是什么事件
HAL_ENTER_CRITICAL_SECTION(state);
tasksEvents[idx] |= events;     // Add back unprocessed events to the current task.
HAL_EXIT_CRITICAL_SECTION(state);
#if defined( POWER_SAVING )
#else // Complete pass through all task events with no activity?
osal_pwrmgr_powerconserve();    // Put the processor/system into sleep
#endif
/* Yield in case cooperative scheduling is being used. */
#if defined (configUSE_PREEMPTION) && (configUSE_PREEMPTION == 0)
```
- `typedef unsigned short (*pTaskEventHandlerFn)( unsigned char task_id, unsigned short event );`（ch02/058 照抄）
  ⇒ **事件是 `unsigned short`（16 位）**，§1"事件位是有限资源"的字面依据。
- **任务侧的"清位"写法**（ch02/066，`Hal_ProcessEvent`）：
  ```c
  if ( events & SYS_EVENT_MSG ) {
      msgPtr = osal_msg_receive(Hal_TaskID);
      while (msgPtr) { osal_msg_deallocate( msgPtr ); msgPtr = osal_msg_receive( Hal_TaskID ); }
      return events ^ SYS_EVENT_MSG;
  }
  if ( events & HAL_LED_BLINK_EVENT ) {
  #if defined (BLINK_LEDS) && (HAL_LED == TRUE)
      HalLedUpdate();
  #endif
      return events ^ HAL_LED_BLINK_EVENT;
  }
  ```
  ⇒ 两条硬规则：**判位用 `&`、清位用 `^` 后 `return`**；**取消息要 `while` 抽干再释放**
  （这里与 §1"一次最多取 2 条"的表述不是一回事：`osal_msg_receive` 的取法由调用方的 `while` 决定，
  HAL 就是循环抽干的 ⇒ **自定义任务也应 `while` 抽干**，否则消息积压）。
  ⇒ `return events ^ …` 若漏写，未清位会被 `tasksEvents[idx] |= events` 加回去 ⇒ **同一事件反复触发**，
  这就是"任务里少了个 return / 忘了清位 → 表现为死循环空转"的机理。

### 6.6 `ZB_ENTRY_EVENT` 全链（ch02/068、070~077，唯一副本）

设置端（`SAPI_Init`，ch02/068）：
```c
sapi_TaskID = task_id;
sapi_bindInProgress = 0xffff;
sapi_epDesc.taskID = &sapi_TaskID;
sapi_epDesc.endPoint = 0;
#if ( SAPI_CB_FUNC )
  // 默认情况下关闭匹配描述符响应
  afSetMatch(sapi_epDesc.simpleDesc->EndPoint, FALSE);
  // 对 ZDApp 注册回调事件
  ZDO_RegisterForZDOMsg( sapi_TaskID, NWK_addr_rsp );
  ZDO_RegisterForZDOMsg( sapi_TaskID, Match_Desc_rsp );
#endif
#if defined(HAL_KEY) && (HAL_KEY == TRUE)
  osal_set_event(task_id, ZB_ENTRY_EVENT);      // 红框：设置事件以启动应用程序
#endif
```
处理端（`SAPI_ProcessEvent`，ch02/076）：
```c
if ( events & ZB_ENTRY_EVENT ) {                // 处理 ZigBee 进入事件
    uint8 startOptions;
#if ( SAPI_CB_FUNC )
    zb_HandleOsalEvent( ZB_ENTRY_EVENT );       // 在应用层中进行 ZB_ENTRY_EVENT 事件的处理
#endif
    // LED off cancels HOLD_AUTO_START blink set in the stack
    HalLedSet (HAL_LED_4, HAL_LED_MODE_OFF);
    zb_ReadConfiguration( ZCD_NV_STARTUP_OPTION, sizeof(uint8), &startOptions );
    if (startOptions & ZCD_STARTOPT_AUTO_START) zb_StartRequest();
    else { HalledBlink(HAL_LED_2, 0, 50, 500); }   // 原文拼写 HalledBlink
    return ( events ^ ZB_ENTRY_EVENT );
}
```
⇒ **完整链**：`osal_set_event(task_id, ZB_ENTRY_EVENT)` → OSAL 轮询 → `SAPI_ProcessEvent` →
`zb_HandleOsalEvent` → `zb_ReadConfiguration` → `zb_StartRequest()` → `ZDOInitDevice(zgStartDelay)`（ch02/077）。
⇒ §2"不调 `zb_StartRequest()` 就不会入网"在图里就是这一句 `if (startOptions & ZCD_STARTOPT_AUTO_START) zb_StartRequest();`
——**AUTO_START 位没置上就永远只闪灯等外部输入**（`HalledBlink(HAL_LED_2,0,50,500)`）。

节点类型自纠（ch02/070/071）：
```c
uint8 selType = NODE_TYPE;                       // 节点类型，在 sensor.h 中定义（产品自有）
zb_ReadConfiguration( ZCD_NV_LOGICAL_TYPE, sizeof(uint8), &logicalType );
if ( logicalType != ZG_DEVICE_TYPE_ENDDEVICE && logicalType != ZG_DEVICE_TYPE_ROUTER ) {
    zb_WriteConfiguration(ZCD_NV_LOGICAL_TYPE, sizeof(uint8), &selType);
    zb_SystemReset();                            // 系统软复位，重启设备
}
osal_nv_read( ZCD_NV_PANID, 0, sizeof(panid), &panid );
HalLedSet( HAL_LED_2, HAL_LED_MODE_FLASH );      // 网络灯（红色 LED）开始闪烁
```
⇒ §2"类型与固件不符会写入并重启"的**代码级依据**（也解释了"首启莫名复位一次"是正常行为）。
启动选项自纠（ch02/074/075）：`if (startOptions != ZCD_STARTOPT_AUTO_START) { 写入 + zb_SystemReset(); }`
⇒ **类型和启动选项两处都会"改 NV + 软复位"**，看到无规律复位先查这两个 `if`。
`zb_StartRequest()`（ch02/077）：`logicalType > ZG_DEVICE_TYPE_ENDDEVICE` 或与 `ZG_BUILD_*_TYPE` 编译宏冲突时
→ `logicalType = ZB_INVALID_PARAMETER; SAPI_SendCback(SAPICB_START_CNF, logicalType, 0);`，否则 `ZDOInitDevice(zgStartDelay)`
⇒ **编译宏与 NV 里的节点类型不匹配会在启动阶段直接回 CNF**，这是"改了工程配置类型却没改 f8w 宏"的典型症状。

### 6.7 MT 串口链的图证（ch02/080~087）

- `MT_UartProcessZToolData` 的 FCS 分支（ch02/080，照抄）：
  ```c
  case FCS_STATE:
      FSC_TOKEN = ch;
      /* Make sure it's correct */
      if(!SerialUART_FlushTimeout(uartMsg, msgLen), MT_…（行尾截图不清）
          osal_msg_send( AppTaskID, (byte *)pMsg );
      else {
          /* deallocate the msg */
          osal_msg_deallocate( (uint8 *)pMsg );
      }
      state = SOP_STATE;
      break;
  ```
  ⇒ **校验失败分支确实释放了 `pMsg`**（§4 收帧状态机的补全；此前我误记为"疑泄漏"，已按图更正）。
- 子系统号取法（ch02/082）：Watch 里 `rsp[1] & MT_RPC_SUBSYSTE…`（名字截断）= **9** ⇒ §4"APP 子系统 = 序号 9"的图证。
- `mtProcessIncoming[]` 表（ch02/083 照抄 9 项）：
  `MT_SystemCmdProcessing, MT_ZmacCmdProcessing, MT_NetworkCmdProcessing, MT_UtilitiesCmdProcessing,`
  `MT_ZdoCmdProcessing, MT_APSysCmdProcessing, MT_ZclCmdProcessing, MT_AFCmdProcessing, MT_AppCmdProcessing`
  ⇒ **APP 在下标 8、序号 9**，与上一条一致。
- `MT_AppCommandProcessing`（ch02/086，照抄，注意与 §4 的命名差异）：
  ```c
  epIndex = sfFindEndPointDesc( endpoint );          // 图中函数名如此（sf…，非 afFindEndPointDesc）
  if( epIndex ) {
      msg = (sapiCmdMsg_t *)osal_msg_allocator(sizeof(sapiCmdMsg_t) + datalen);   // 图中拼写 osal_msg_allocator
      if( msg ) {
          msg->hdr.event = MT_SAPI_CB_MSG;
          msg->endpoint  = endpoint;
          msg->command   = …（截图不清）
          msg->len       = datalen;
          osal_msg_send( (epIndex->taskID), (uint8 *)msg );   // 红框"发送到应用层"
      }
      retValue = ZSuccess;
  } else {
      MT_BuildAndSendZToolResponse(((uint8)MT_RPC_CMD_SRSP | (uint8)MT_RPC_SYS_APP), cm…（截断）
  }
  ```
  > ⚠校核：`sfFindEndPointDesc` / `osal_msg_allocator` / `ZSuccess` 与 §3/§4 的
  > `afFindEndPointDesc` / `osal_msg_allocate` 拼写不一致 —— 可能是**截图 OCR 误读**，也可能真是该版本/该工程的写法。
  > **抄代码前必须在源码里搜一遍函数名**，别照这段直接改。
- Watch 实测值：`rsp[1] = 0x29`、`rsp[2] = 0x00`（ch02/081）、`endpoint = 0x02`（ch02/084）。
  帧载荷（"TYPE=?,PANID=…"等）属**公司协议，未转写**。

### 6.8 SAPI 接收侧的真实签名与消息结构（ch02/088~095）

```c
// ch02/088（=090）sapic.c 行 754-757
case AF_INCOMING_MSG_CMD:   //数据包接收事件
    pMSGpkt = (afIncomingMSGPacket_t *) pMsg;
    SAPI_ReceiveDataIndication( pMSGpkt->srcAddr.addr.shortAddr, pMSGpkt->clusterId,
                                pMSGpkt->cmd.DataLength, pMSGpkt->cmd.Data);
    break;
```
```c
// ch02/089/094
void SAPI_ReceiveDataIndication( uint16 source, uint16 command, uint16 len, uint8 *pData )
{
#if defined ( MT_SAPI_CB_FUNC )
    if ( SAPICB_CHECK( SPI_CB_SAPI_RCV_DATA_IND ) )      // 图中宏名 SPI_CB_…，疑 OCR
        zb_MtCallbackReceiveDataIndication( source, command, len, pData );
    else
#endif
#if ( SAPI_CB_FUNC )
    zb_ReceiveDataIndication( source, command, len, pData );   // 红框：去向
#endif
}
```
- **`SAPI_ReceiveDataIndication` 是 4 参**（source/command/len/pData），
  与 §3 里 TI 手册常见的 8 参 `zb_SAPI_ReceiveDataIndication` **不是同一个函数** ⇒ 别混。
- 两个结构体定义（唯一副本，写解析代码必用）：
  ```c
  typedef struct { uint8 event; uint8 status; } osal_event_hdr_t;             // ch02/091
  // ch02/092 afIncomingMSGPacket_t 成员（顺序照抄）
  osal_event_hdr_t hdr; uint16 groupId; uint16 clusterId; afAddrType_t srcAddr;
  uint16 macDestAddr; uint8 endPoint; uint8 wasBroadcast; uint8 LinkQuality;
  uint8 correlation; uint8 rssi; uint8 SecurityUse; uint32 timestamp; afMSGCommandFormat_t cmd;
  ```
  ⇒ 想拿 **RSSI / 链路质量 / 广播标志**就在这一层取，不用自己加协议字段。
- 工程改写版（ch02/095）：`zb_ReceiveDataIndication` 里
  `uint16 pAddr = NLME_GetCoordShortAddr();` → `if (command == 0)`（**用 command==0 表示"这是自有数据"**）
  → `if (logicalType != ZG_DEVICEYPE_COORDINATOR) at_notify_data((char*)pData, len);`（**照抄原图拼写 `ZG_DEVICEYPE_`**）
  → `ZXbeeInfRecv((char*)pData, len);`
  ⇒ 可复用的手法：**用 `command`/clusterId 值当"数据类型分流"的第一判据**；其余属项目事实。
- 调试现场（ch02/093）：`pMSGpkt->srcAddr.ad… = 0x0049`、`pMSGpkt->clusterId = 0x0000`
  ⇒ 与"command==0 走自有数据"一致（数据内容公司专属，未转写）。

### 6.9 CC2530 在 3.0.2 上的工程配置截图（ch02/096~099，唯一副本）

| 项 | 图里取值（照抄） |
|---|---|
| 新建配置 | IAR `New Configuration`：Name `CC2530-Serial`、Tool chain **`8051`**、Based on configuration **`EndDeviceEB`**、Factory settings `Debug` |
| 链接库 | `Linker → Config` 勾 **`Use command line options`**，三行：`<PROJ_DIR>\..\Libraries\TI2530DB\bin\EndDevice-Prod.lib`、`…\Security.lib`、`…\MAC_CC2530.lib` |
| 预处理 | `C/C++ Compiler → Preprocessor` 勾 `Use command line options`，三行 `f$PROJ_DIR$\…\Tools\CC2530DB\f8w…cfg`（可辨 `f8wEnddev.cfg`、`f8wConfig.cfg`）⇒ **f8w 配置宏文件是用 `-f` 挂进来的** |
| printf | `General Options → Library Configuration`：**`Print formatter` 下拉选 `Large`**（列表里另有 `Full formatting`） |

> ⚠校核：`embedded/mcu-chip-families/cc2530-cc2538-cc2640.md` §1 的 printf 行写"IAR 里 printf 选项要选 **Full formatting**"，
> 而这张图选的是 **`Large`** ⇒ 两处不一致（不同 IAR 版本下拉项不同）。**以工程能编过 + 串口有输出为准**。
> 另：图里库名是 `EndDevice-Prod.lib`，§5 第 4 条写的是 `EndDevice-Pro.lib` ⇒ **文件名以库目录实际为准**，别手打。

### 6.10 三条常见问题的图证（ch02/100~106）

| 问题 | 图里读到的判据 |
|---|---|
| 系统自动设置标准网络状态（100） | Call Stack：`bdb_setFN ← bdb_reportCommissioningState ← bdb_nwkDiscoveryAttempt ← ZDApp_ProcessOSALMsg ← ZDApp_event_loop ← osal_run_system ← osal_start_system ← main` ⇒ **§5 第 6 条的 `bdb_setFN` 在 3.0.2 里是被 BDB 组网流程回调的**，不是自己乱调的入口 |
| 无限重启、2s 一次（101、102、105） | 串口反复成对打印 `-->HW:CC2530` 与 `-->RDY` ⇒ **看到这对周期性输出就是复位循环**；102 提示核对 IAR 工具栏当前配置是否 `EndDeviceEB`；103 只有一个监视项 `XDATA: = 0x400`（**上下文太少，用途截图不清**） |
| 一直在 `osalTimerUpdate` 死循环（104、105） | 手法：运行中点 **Break** 打断，看 PC 是否停在 `osalTimerUpdate`（104 就只是那个按钮）⇒ 原文未给出根因，**未验证** |
| 组网后过 10 分钟组网失败（106） | 串口序列：`zdo status 2 / 2 / 3 / 5 / 3 / 0 / uart init / 2 / 2 / 0 / uart init …`
  ⇒ **可复用判据：用 `zdo status <n>` 跟踪 ZDO 网络状态迁移，回落到 0 并伴随 `uart init` 表示掉网/重启**；
  原文对"10 分钟"这个时间点**没有给出成因**（未验证） |

### 6.11 无新增信息 / 跳过 / 看不清

- **无新增信息**：054（与 §2 端点号重复）、067（Z-Tool 串口窗口，只有 `Unsupported or unformatted message received` 警告）、090（=088）、104（只有工具栏按钮）。
- **跳过（项目专属）**：078、079（上位机工具发的帧字节）、085/087 载荷字段含义、093 的数据内容、
  070/071 里的 `at_init()`/`sensorInit()`/`CC2530_Serial`/`NODE_TYPE`/`ZBeeInit` 产品语义。
- **看不清**：055（`osal_mem_kick` 上方注释行尾）、056（末行 Init 函数名）、059（分发行字迹、右侧内存窗）、
  062/064（Watch 的 Location 数值）、077（`#if` 宏名前缀）、080（`if` 条件行尾）、083（部分字节）、
  086（`msg->command` 右值）、089（注释行尾、`SPI_CB_…` 宏名）、093（`DataLength` 值、工程树文件名）、
  098（三个 cfg 文件名细节）、099（下拉其余选项）、101（时间戳）、103（`XDATA:0x400` 用途）。

## 7. 概念易错点（校核结论）

| 原文说法 | 问题 | 置信 |
|---|---|---|
| "`ZCL_HA_DEVICEID_ON_OFF_LIGHT_SWITCH` 表示这是智能插座" | 该 DeviceID 是**通断灯开关**，不是插座（SampleSwitch 语义） | 高 |
| "A 设备加入绑定后触发 `ZDO_NEW_DSTADDR`" | 该事件是**收到 Bind/地址响应得到新目的地址**时触发，"加入绑定"表述不准 | 中 |
| "`ZB_ALLOW_BIND_TIMER` 处理系统定时绑定事件" | 实际是**超时关闭 match descriptor（`afSetMatch(EP, FALSE)`）以结束允许绑定窗口**，不是"定时做绑定"；**ch02/068 图里 `SAPI_Init` 默认就 `afSetMatch(..., FALSE)`，与这条一致** | 高（图证） |
| "`osal_msg_send` 的 `@param uint8 len`" | 函数只有 2 个参数 —— **TI 原注释缺陷**，不是作者错 | 高（源头在上游） |
| "每个设备最多 240 个端点" | 与 1~240 可用范围一致，可接受 | 无法判断 |
| 作者自标未验证 | "表 9-1 初始比较输出**不建议采纳**"、"ZDO_STATE_CHANGE 我理解不知对不对"、"不知道有没有用"、"改 lib 后 0xcd **原因未知**" | — |
