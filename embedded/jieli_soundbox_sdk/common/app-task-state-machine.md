# 启动链与模式任务状态机（杰理 soundbox SDK 通用）

## 1. 上电到进模式的完整链路（证据均为 SDK 内相对路径）

```
main()                                  apps/soundbox/common/init.c:217-250
 ├ wdt_close → os_init → setup_arch
 ├ board_early_init
 ├ task_create(app_task_handler, "app_core")     ← 主任务在这里诞生
 └ os_start()

app_core 任务体 = app_init() + app_main()          init.c:193
 ├ app_init()                              init.c:104-148
 │   ├ early/platform/initcall 五级初始化  ← 靠段自动登记，不需要改 Makefile
 │   ├ board_init()                        板级外设（顺序见下）
 │   ├ audio_enc_init() / audio_dec_init()
 │   ├ update_result_deal()                ← 处理上次升级结果
 │   └ check_power_on_key()                init.c:68-102  长按 >70×10ms 才放行，否则软关机
 └ app_main()                              apps/soundbox/app_main.c
     ├ 充电在线标志判断 → 决定 APP_IDLE_TASK 还是 APP_POWERON_TASK（app_main.c:112-130）
     ├ app_curr_task = APP_POWERON_TASK    app_main.c:134
     └ app_task_loop()                     app_main.c:34-96  一个大 switch 分发 14 个模式
```

`app_task_loop` 每一轮的**出口固定做两件事**：`app_task_clear_key_msg()`（清按键消息）+ `vm_check_all(0)`（VM 整理检查）。

真实开机 log 对照（工程里那份 `log.md` 就是样本）：`setup_arch` → `[SDFILE]VM size...` → `sdfile mount succ` →
`[BOARD]Power init` → 一串 `[USER_CFG]` → `app_main` → `cur---1/new+++3`（POWERON→BT）。
**学会用 log.md 逐行对代码，是这套 SDK 最快的读码法。**

## 2. 任务状态机

- 模式枚举 `APP_POWERON_TASK=1 … APP_IDLE_TASK=11`（`apps/soundbox/include/app_task.h:10-26`，共 14 个取值：
  POWERON/POWEROFF/BT/MUSIC/FM/RECORD/LINEIN/RTC/PC/SPDIF/IDLE/SLEEP/SMARTBOX_ACTION）。
- 三个全局量 `app_curr_task / app_next_task / app_prev_task`（`task_manager/app_task_switch.c:41-43`）。
- `app_task_switch_to(x)`（`:250`）不是立即切：
  1. **进入检查** `xxx_app_check`：music/linein/pc/record 要求设备在线（`:141-174`）；
  2. **退出检查** `xxx_exit_check`：bt 在 `init_start && !init_ok` 时**拒绝退出**（`:119`、`bt.c:1290-1294`）——
     这就是"点了切换没反应"的正常原因；
  3. 置 `app_next_task` 并 `app_task_put_usr_msg(APP_MSG_SWITCH_TASK)`；
  4. **旧任务自己在 `app_task_exitting()`（`:307`）里完成切换**并关掉按键消息。
- 轮转顺序由 `app_task_list[]`（`app_task_switch.c:11-39`）决定，且按 `TCFG_APP_*_EN` 编译裁剪 →
  **改板级开关会直接改变"下一个模式"是谁**。
- 每个模式任务的共同骨架（`bt.c:1196-1320`、`music.c:1003-1042`、`power_on.c:129-159`）：

```c
task_init(); 放提示音;
while (1) {
    app_task_get_msg(msg, 32, 1);           // 32=队列长度, 1=block
    switch (msg) {
      case APP_MSG_SYS_EVENT:
          if (本模式 sys_event_handler(...) == FALSE)
              app_default_event_deal(...);   // 兜底
          break;
      ...
    }
    if (app_task_exitting()) { task_close(); return; }   // 切换在这里落地
}
```

## 3. 新增一个模式要改的 5 处（手册 p24-25）

1. `app_task.h` 加任务 id；
2. 加入 `app_task_list`（决定轮转位置）；
3. `task_key.c` 加该模式的按键转换表（ad/io/ir 各一张）；
4. `task_manager/` 下建模式目录 + 头文件目录；
5. 实现 `app_xxx_task` / `xxx_app_check` / `xxx_sys_event_handler` / `xxx_key_event_opr`，
   并在 `app_main.c:app_task_loop` 的 switch 里加 case。
外加 `TCFG_APP_XXX_EN` 板级开关与 `task_table.c` 的栈登记。

## 4. 系统事件分派规则（重要且反直觉，手册 p28）

事件分三类来源：**按键 / 设备 / 蓝牙**；每一类又分"**模式内处理**"和"**公共处理**"两级。

- 先查当前模式的事件处理，**命中即执行且不再走公共类**；未命中（返回 FALSE）才落到公共类；两边都没有 → **事件作废**（静默丢弃）。
- 特例：**蓝牙模式下未处理的设备事件会被丢给"公共蓝牙事件"而不是"公共设备事件"** —— 排查"拔卡没反应"时先看这条。
- 消息接口：`app_task_put_usr_msg` / `app_task_get_msg`（block 传 0=内部 pend，1=直接返回）/ `put_key_msg` / `clear_key_msg`；
  消息码 `APP_MSG_SYS_EVENT = Q_EVENT`、`APP_MSG_SWITCH_TASK = Q_USER+1`、`APP_MSG_USER = Q_USER+2`。

## 5. 任务表与优先级（`apps/soundbox/common/task_table.c`）

`const struct task_info task_info_table[] = { {"名字", 优先级, stack_size, 时间片}, ... }`，
含 `app_core / sys_event / btctrler / btencry / tws / btstack / local_dec / audio_dec / audio_enc / audio_out / aec / aec_dbg / update / dw_update ...`。

- **栈大小必须是 32 的倍数**（文件第 5 行注释写死）。给小了表现为随机跑飞/hardfault，极难定位。
- 优先级：**任务最低 0 最高 6**，中断 `irq_pro_list[]` **最低 0 最高 7**。手册两处都标"不建议改，避免系统崩溃"。
- 谁创建主任务：`main()` 里 `task_create(app_task_handler, NULL, "app_core")`（手册 p16）。
- 自定义线程也要在这里登记（本工程用户加了 `{"rf_decode", 3, 128, 128}`、`{"users_seg", 3, 256, 128}`）。

## 6. 时钟管理（BR23 有，跨型号机制相同）

`cpu/br23/clock_manager.c`：`clock_enum[]` 给每个模式定 idle 时钟
（BT/MUSIC 24、FM 48、LINEIN 96、PC 120、REC/RTC/SPDIF 12、BOX 24），算法时钟如 `AEC16K_ADV 120`、`DEC_MP3 46`。
接口 `clock_add / clock_remove / clock_set_cur`（延迟生效）与 `clock_add_set / clock_remove_set`（立刻生效），
**用完必须 remove**，否则时钟下不来、功耗异常。`CLOCK_FIX` 非 0 = 固定频率。
UI 相关有自己的类型 `DEC_UI_CLK` / `LCD_UI_CLK`（`clock_cfg.h`）。

## 7. 坑清单

- 模式任务里**不许死等/长阻塞**：会把 `app_task_clear_key_msg` 和 `vm_check_all` 一起卡住（`app_main.c:93-95`）。
- 模式切换是**异步**的，检查未通过就悄悄失败，没有任何日志——要加 `xxx_app_check` 打印才知道。
- `board_init()` 顺序要紧（`board_ac695x_demo.c:932-969`）：power → adc_init → cfg_file_parse → … →
  `dev_manager_init` → `board_devices_init(key_driver_init)`；因为 **adkey 依赖 ADC 先初始化**（`adkey.c:54` 注释）。
- 充电在线时 `app_main` 直接进 IDLE（`#ifndef PC_POWER_ON_CHARGE`，`app_main.c:112-130`），
  上电开机逻辑与"插电开机"逻辑不是一条路，改动前先读 `init.c:105-139`。
- 需进一步确认：`VM_ITEM_MAX_NUM`、`KEY_EVENT_MAX` 在源码里没有 `#define`，疑似由构建参数 `-D` 注入
  （`syscfg_id.h:88` 引用）。
