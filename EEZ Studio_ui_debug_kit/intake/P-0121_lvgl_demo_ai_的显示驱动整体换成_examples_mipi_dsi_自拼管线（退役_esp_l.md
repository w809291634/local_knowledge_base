# P-0121 · lvgl_demo_ai 的显示驱动整体换成 examples/mipi_dsi 自拼管线（退役 esp_lvgl_adapter 路线）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_ai（EEZ UI + 小智语音）
- **日期**：2026-10-11
- **工具**：Qoder
- **状态**：open（编译/链接/配置已自证，**行为待真机**）
- **标签**：LVGL,帧率,ESP32-P4,自拼管线,DIRECT,PPA SRM,LV_OS_CUSTOM,钉核,include路径,managed_components,GT911,触摸离线程,真机取证
- **关联提示词**：PR-0199, PR-0200, PR-0201
- **关联经验**：esp32 子库 §22/§23/§24（管线与钉核定稿）、§16（PPA fill/blend 越界，**保持不打开**）、`reference/08`（帧率取舍 v2）、`reference/09`（构建通路）

## 动机（为什么换）

两条路线在本工程的 DSI/面板参数**逐字相同**（480x800、dpi 30MHz、porch 42-12-42/2-8-60、2 lane/500Mbps、RGB565、num_fbs=3），
所以帧率差不在显示链路上，全在 LVGL 侧：旧路线是 `esp_lvgl_adapter` 的 `TRIPLE_FULL + ROTATE_90` ⇒
**FULL 渲染 + 只有 1 块绘制缓冲（就是面板 fb2）+ SRM 阻塞提交**，实测 23ms 渲染 + 8ms 刷屏 = **27fps**（§19.1，本工程的数）。
要把那 8ms 藏起来，按 §20 只能改托管组件 `lvgl_bridge_v9.c`（用户规则禁止，且升级即被冲掉）；
自拼路线反过来**一行库都不用改**（§24.9：打了仪表补丁 38.7 vs 没打 38.8）。⇒ 用户拍板「完全按它的驱动适配」。

## 做法（落地清单，全部在本工程自己的文件里）

新增本地组件 `components/dsi_display/`：`dsi_display.c`（面板 + SRM 送屏 + DIRECT 双缓冲 + LVGL 任务/tick + 锁）、
`dsi_touch.c`（GT911 独立轮询任务 20ms 写快照，read 回调只拷快照）、`lv_os_pinned.c/h`（`LV_OS_CUSTOM` 钉核）、
`private/dsi_board.h`（只放时序与 LV 几何，板级接线事实继续从 `bsp/display.h` 取，不留第二份）、
`private/st7701_init_cmds.h`（参考表的逐字拷贝，已用「命令+数据字节序列」比对证明与 BSP 自带表完全一致：62 项、双向无差）。
改 `main/main.c`（3 处：入口 + 锁）、`main/CMakeLists.txt`（REQUIRES）、顶层 `CMakeLists.txt`、`sdkconfig(.defaults)`。

## 本轮真正学到的（不是抄来的）

1. ★ **include 路径机制在不同工程里不等价**：参考工程只给 `__idf_lvgl__lvgl` 目标加 include 就够，
   本工程还有 `esp_lv_decoder` / `esp_lvgl_adapter` 等多个托管组件间接 include LVGL 头，
   于是在它们的 TU 里报 `fatal error: lv_os_pinned.h: No such file or directory`，
   **且报错位置指向 `build/config/sdkconfig.h` 里 `#define CONFIG_LV_OS_CUSTOM_INCLUDE` 那一行**
   （宏展开点，不是 sdkconfig.h 本身坏了）。正解 = 全局搜索路径，且必须写在 **`project()` 之前**：
   `idf_build_set_property(COMPILE_OPTIONS "-I<dir>" APPEND)`。
   ⚠ **没有 `COMPILE_INCLUDE_DIRS` 这个属性名**：写错不报错、被静默忽略（我第一次就踩了，现象是「改了 CMake 却没生效」）。
2. **9.4 → 9.5 的 API 差**：`lv_display_get_render_mode()` 是 9.5 才有的（9.4 只有 setter），移植参考代码时
   这类「只读回配置」的打印要逐个核；`lv_display_set_tile_cnt/get_tile_cnt`、`lv_display_get_buf_active`、
   `LV_OS_CUSTOM`（Kconfig 的 `255: CUSTOM`）、`lv_thread_t/lv_mutex_t/lv_thread_sync_t` 字段在 9.4 全都有 ⇒ 原样可用。
3. `ESP_RETURN_ON_ERROR` 的宏体是 `return err_rc_` ⇒ **不能用在返回指针的函数里**；
   指针函数只能用 `ESP_RETURN_ON_FALSE(cond, NULL, TAG, ...)` 或显式 if。
4. `ninja: error: failed recompaction: Permission denied`（build.ninja 被占）在这台机上**是瞬时的**：
   `tasklist` 里没有 ninja/cmake 残留进程时，直接重跑就好，别去 fullclean。
5. 换完链接器把旧路线整条丢掉了：**bin 0x4efae0 → 0x4e8110（-30KB），app 分区空闲 38% → 39%**
   —— 这条差值本身就是「旧路线已不再被执行」的独立证据（比读代码强）。
6. 顺带把当年塞进托管组件的 2 行 DIAG 日志**还原**了（`esp_lvgl_adapter/src/display/display_manager.c`），
   现在 `lvgl__lvgl` 与 `esp_lvgl_adapter` 对上游缓存 **各 0 文件差异**；还原用的干净副本 =
   `AppData\Local\Espressif\ComponentManager\Cache\service_*/<组件>_<版本>_<hash>`（见 §24.7）。

## 与参考工程的有意偏差（下次别当成"照抄漏了"）

| 项 | 参考 | 本工程 | 为什么 |
|---|---|---|---|
| LVGL | 9.5.0 | **9.4.0**（托管，不动） | 升版本会牵动 EEZ 产物与 PC 仿真 |
| LVGL 内存 | `LV_USE_CLIB_MALLOC` | **保留 `LV_USE_CUSTOM_MALLOC`（全 PSRAM）** | §17：内部 RAM 撑不起 EEZ 11 屏；代价是多占 PSRAM 带宽 |
| 绘制缓冲 | 2x768000B + 4KB 护栏 | 同 + **护栏每 1s 自数**（`check_guards`） | 未结的 PSRAM 堆损坏需要证据；开机还打 fb/缓冲地址与 psram largest |
| 背光 | 自己 `backlight_init` | **继续走 BSP 的 `bsp_display_brightness_init/on`** | `output_invert=1` 那条修复在 BSP 里，且原生层的亮度/息屏 API 也在那儿 |
| 触摸 bring-up | 自建 I2C0 + 双地址探测 | **继续走 BSP `bsp_touch_new`**（I2C1、50+50/150ms 复位、重试 5 次） | 已在真机验过；本文件只换「读放在哪个线程」 |
| 旋转完成等待 | 超时后 `portMAX_DELAY` 二次等 | **只有 200ms 有界等，超时就丢这一帧** | 参考工程 §24.10 自己列为欠账：旋转中断一旦丢失会永久冻 UI，而 Task WDT 只看 idle 兜不住 |
| 仪表 | `dsi_test.c` 全套 | 只留屏上性能表 + 开机日志 | 一次一炉；`task cpu` 报表等数字不明确时再加 |

## 待真机（这一炉只看这些）

1. `lv_os_pin: thread 'swdraw' #0 pinned to cpu0 prio 3` + `#1 pinned to cpu1` ⇒ 双核是真分核了（旧路线这条是假的）。
2. 屏上右下角 FPS：旧基线 27（§19.1）；参考场景同管线 38.8。
3. `dsi_disp: render_mode=DIRECT tile_cnt=1 | mem: ... psram free/largest` ⇒ largest 要够 2 块 772096B（分配发生在打印前，所以能过就是够）。
4. 触摸四个角：`touch press #N at lvgl x=.. y=..`，x 覆盖 0-799、y 覆盖 0-479；反向只翻**一个** mirror（镜像作用在 swap 之前，改 mirror_x 动的是 LVGL 的 y）。
5. 回归面（本工程独有，参考工程没有）：小智唤醒/连续对话（`audio_input` 钉 cpu0 prio 8，会抢 `swdraw@0` 的 prio 3）、音乐播放、天气抓取、息屏/亮度、语音命令切页。
6. 不该出现：`SRM submit failed`、`rotate not done after 200ms, frame dropped`、`draw buffer #N tail overwritten`。


## 追加（同日）：自拼管线有个结构性空窗 —— 没有脏区就没人 flip

用户报「滑动收尾时最后一帧停一下才跳到位」。读证就成立，不必等真机：

- `lv_refr.c:415`：`if(disp_refr->inv_p == 0) goto refr_finish;` ⇒ **没有脏区时 LVGL 完全不调 flush_cb**；
- 而参考实现的 flip 只挂在 flush 开头（`pipeline_drain()` 唯一调用点）⇒ 动画/惯性滚动**一停**，
  最后提交那笔 SRM 的目标 FB 就一直没人翻，屏上停在"倒数第二帧"，直到某个不相关的失效（定时器、
  别处重绘）带来下一次 flush 才突然跳到位。停顿长度 = 到下一次脏区的间隔，看着就像"固定 200ms 上下"。

改法（本工程已落地）：task 循环里记住"这一趟有没有渲染过"（在 flush 的 last 分支置位），
**没渲染过就在 `_lock_release` 之后补一次 `pipeline_drain()`**。要点三条：
1. 不能无条件补 —— 刚提交完就去等自己的完成，等于把 7.3ms 旋转重新搬回关键路径（回到旧的阻塞行为）；
   只在"这一趟没画图"时补，此时等待的对象早已完成，代价为 0。
2. 补调用放在锁外：它等硬件但不碰对象树，别让它把等锁的别的任务一起拖住。
3. 顺带修好开机第一次上屏：原来要等第二帧才 flip。

★ 通用判据：**只要送屏是"下一帧开头才 flip"的管线，就必须回答"最后一帧由谁 flip"**。
参考工程没被这个问题绊住，是因为它的场景（demo widgets + 整页轮播）永远有脏区。
