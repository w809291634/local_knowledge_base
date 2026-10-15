# 按键与事件流（杰理 SDK 通用）

## 1. 一条完整链路

```
① 扫描     10ms 软定时器 → key_driver_scan()            apps/common/key/key_driver.c:61
② 消抖     filter_time 滤波（:91-101）
③ 事件判定 单击/双击…五击（:166-191）、LONG、HOLD（:204-222）→ 组 SYS_KEY_EVENT
④ remap   弱符号 key_event_remap()（:53）
⑤ 通知     sys_event_notify()（:275）
⑥ 映射     app_key_event_remap()（app_task_switch.c:53，用 SYS_EVENT_HANDLER 优先级 3 注册 :111）
           按 key->type 调 task_key.c 里的 xxx_event_to_msg()
⑦ 查表     [任务号] → [key->value][key->event] → 事件码   task_key.c:52-62
           返回 KEY_NULL 则 consumed=1，事件被吞掉（:102）
⑧ 消费     app_common_key_msg_deal()（app_common.c:84）公共处理；
           模式内优先，未命中才走公共（见 app-task-state-machine.md §4）
```

事件码从 `0x80` 起，定义在 `apps/soundbox/include/key_event_deal.h:9`。
按键表内容在板级目录 `board/br23/board_ac695x_demo/key_table/adkey_table.c`，
**列序 = 单击 / 长按 / hold / 抬起 / 双击 / 三击**。

## 2. 按键类型与各自的坑

SDK 内建：`iokey`（`iokey.c`）、`adkey`（`adkey.c`，单 ADC 多键）、`adkey_rtcvdd`、`irkey`（`irkey.c`）、
`touch_key` / `ctmu_touch_key`、`rdec_key`（旋转编码器）、`slidekey`。手册能力表还列 `rdekey`、`slidekey`。

- **iokey 时序以扫描周期为单位**：`long=75` 实际是 75×10ms≈0.75s（`iokey.c:27-36`）。改 `scan_time` 会同步改变长按手感。
- `filter_time=0` 会让消抖逻辑直接失效（`key_driver.c:91`）。
- iokey **组合键要求键值 < 7**（`iokey.c:39`）。
- adkey 里 **BIT(7) 是"只发单击"的保留位**（`key_driver.c:159`）。
- `key_event_deal.h` 的 `KEY_IR_NUM_0~9` 区间**中间不允许插入**新事件（`:163-172`）。
- 按键表维度 `KEY_AD_NUM_MAX=10 / KEY_IO_NUM_MAX=6 / KEY_IR_NUM_MAX=21` 定义在**板级 cfg**（demo `:200-202`），
  表里越界 = 数组越写，症状是随机按键串。
- `KEY_EVENT_MAX` 在源码里没有 `#define`，疑似构建参数 `-D` 注入（`syscfg_id.h:88` 引用）——写表前确认维度。

## 3. 新增一种按键源：要改的 5 处

1. `include_lib/system/device/key_driver.h:8-23` 的 `KEY_DRIVER_TYPE` 枚举加类型；
2. 写驱动 `.c`：实现 `get_value()` + 填 `struct key_driver_para`
   （字段逐项说明在 `key_driver.h:33-51`：`scan_time / filter_time / long_time / hold_time / click_delay_time / key_type / get_value`；
   部分字段带 `const`，**编译期定死，运行时改不了**）；
3. `key_driver_init()`（`key_driver.c:296-404`）里加 init 并挂定时器（普通用 `sys_s_hi_timer_add`，
   本工程 RF 键在 `:332` 用 `sys_s_hi_timer_add(&rfkey_scan_para, key_driver_scan, 38)`）；
4. `app_key_event_remap()` 加 case，`task_key.c` 加该类型的 `xxx_event_to_msg`；
5. 各板级 `key_table/` 加对应模式表。

## 4. 旁路模式：不进系统按键事件（本工程 RF 键就是这么做的）

`key_driver.c:234-252` 识别到 `KEY_DRIVER_TYPE_RF` 后**不发系统按键事件**，而是查自己的表后
`os_taskq_post_msg("rf_decode", 1, msg)` 直接投给业务线程。适用场景：键值语义与 SDK 事件体系不同构
（如遥控器的"学习键"需要长窗口状态机）。代价：绕开了公共消抖/连击处理，要自己做（实现细节见
`yjt/ac695n_soundbox/user_apps-custom-drivers.md`）。

## 5. 提示音与按键的耦合

按键音走 `audio_key_tone.c`（`apps/common/audio/decode/`）；提示音文件与索引在 `tone.cfg` + `INDEX_TONE_*` 表，
具体哪个事件放哪段音由**量产配置文件**或板级 `status_config` 决定（见 `config-three-layers-and-macro-mutex.md` §5）。
