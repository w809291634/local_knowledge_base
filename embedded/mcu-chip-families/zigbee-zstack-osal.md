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

## 6. 概念易错点（校核结论）

| 原文说法 | 问题 | 置信 |
|---|---|---|
| "`ZCL_HA_DEVICEID_ON_OFF_LIGHT_SWITCH` 表示这是智能插座" | 该 DeviceID 是**通断灯开关**，不是插座（SampleSwitch 语义） | 高 |
| "A 设备加入绑定后触发 `ZDO_NEW_DSTADDR`" | 该事件是**收到 Bind/地址响应得到新目的地址**时触发，"加入绑定"表述不准 | 中 |
| "`ZB_ALLOW_BIND_TIMER` 处理系统定时绑定事件" | 实际是**超时关闭 match descriptor（`afSetMatch(EP, FALSE)`）以结束允许绑定窗口**，不是"定时做绑定" | 中 |
| "`osal_msg_send` 的 `@param uint8 len`" | 函数只有 2 个参数 —— **TI 原注释缺陷**，不是作者错 | 高（源头在上游） |
| "每个设备最多 240 个端点" | 与 1~240 可用范围一致，可接受 | 无法判断 |
| 作者自标未验证 | "表 9-1 初始比较输出**不建议采纳**"、"ZDO_STATE_CHANGE 我理解不知对不对"、"不知道有没有用"、"改 lib 后 0xcd **原因未知**" | — |
