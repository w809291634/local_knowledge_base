# ESP32-P4 + LVGL v9 帧率优化手册（playbook）

> **本页只做一件事**：把"P4 上 LVGL 帧率能优化到什么程度、按什么顺序做、哪些是假的"讲清楚，
> 并给出每一项的实测数字与出处。**故障现象/修复步骤的原文在**
> [`esp32-p4-lvgl9-touch-lcd-debug-optimization.md`](./esp32-p4-lvgl9-touch-lcd-debug-optimization.md)
> （下文用 `§N` 指其节号），本页不复制证据链，只写结论与判据。

**适用范围**：ESP32-P4（双核 RISC-V 400MHz、PPA 2D-DMA、MIPI-DSI）+ LVGL v9.4/9.5 + ST7701S
480×800 玻璃（Waveshare ESP32-P4-WIFI6-Touch-LCD-4.3），横屏 800×480，RGB565。

**数值归属（硬规矩）**：同一个数字在不同工程含义不同，跨工程引用**必须带工程名**。

| 工程 | 显示路线 | 数字代表 |
|---|---|---|
| `lvgl_demo_ai`（EEZ UI） | `esp_lvgl_adapter` + `TRIPLE_FULL/ROTATE_90` | §8、§19、§20 |
| `08_lvgl_demo_v9_opt` | `esp_lvgl_port` | 本库 `intake/P-0120`、`reference/08 §7` |
| `examples/mipi_dsi` | **自拼管线**（本页多数新数字） | §22、§23、§24 |

---

## 1. 先算账，再动手（三行判据，避免白干）

一帧的时间必须同时满足三条，**任何一条超预算就到不了目标帧率**：

| 账 | 60fps（16.6ms）下的 P4 实测 | 结论 |
|---|---|---|
| ① **串行段**：对象树走查 + 动画引擎 + 布局，全在 LVGL 一个线程 | `examples/mipi_dsi` 整页轮播场景 = **LVGL 线程 18.5-18.9ms/帧 CPU** | ❌ 已经超 16.6ms ⇒ 此场景软件渲染**不可能** 60fps |
| ② **像素功**：脏区像素写入 + 混合 | 同上场景 22-23ms/帧，分两核后单核 16.0 + 6.7 | ⚠ 勉强够，但没有余量 |
| ③ **PSRAM 带宽** | 实测写 179 MB/s、拷贝 86 MB/s（=172 流量）；60fps 需要 显示流量 135 MB/s + 绘制 ~90 MB/s | ❌ 超过实测上限 |

⇒ **判据用法**：先用仪表测出"主线程 CPU/帧"。若它 > 目标帧时，**别调管线**，去减对象数/动画数/脏区。
真实产品页（一屏几个控件、局部动画）实测脏区 35% ⇒ 同一条管线 60fps 可得；
`lv_demo_widgets()` + 整页轮播是刻意构造的 torture 场景（脏区 84-91%），它的实际上限是
**≈48fps（总功 42ms/帧 ÷ 2 核）**，已推到 **38-39fps** 并稳定。

---

## 2. 两条路线怎么选

| | `esp_lvgl_adapter`（官方组件） | 自拼（LVGL + `esp_lcd_dpi` + PPA 直用） |
|---|---|---|
| 谁做横屏旋转 | adapter 的 `flush_full_rotate`（PPA SRM）| 自己在 flush 里提交一次整帧 SRM |
| 帧缓冲 | 3 FB + 2 绘制缓冲（`TRIPLE_FULL`）| 自己拿 3 FB + 自己 alloc 2 绘制缓冲 |
| 撕裂规避 | 组件内建（`tear_avoid_mode`）| 靠 `esp_lcd_dpi_panel_get_frame_buffer` 的多 FB + 在 vsync 换指针（§22）|
| 坑 | `TRIPLE_PARTIAL + ROTATE_90` 画面冻结（§5）；PSRAM 大块对齐分配无回退（§4）；改点在托管组件内、升级会被覆盖（§20）| 要自己保证"旋进的不是正在扫描的 FB"、缓存维护、PPA 客户端与 ISR 时序 |
| 何时选它 | 直接用 BSP/EEZ、不想碰驱动 | 要**可测量、可解释**的帧率与零拷贝路径（本手册多数数字来自这条路）|

**共同前提**：ST7701 **没有硬件 90° 行列交换**，横屏必须软件/PPA 旋转（§9）⇒ 旋转的开销与同步是
P4 横屏帧率的一等公民，不要指望"关掉旋转"除非改竖屏。

---

## 3. 有效清单（按收益从大到小，全部实机）

| # | 手段 | 实测 | 出处 / 注意 |
|---|---|---|---|
| 1 | **绘制线程固定核**（`LV_DRAW_SW_DRAW_UNIT_CNT=2` + 真分核） | 33 → **38-39**（+6fps 一档）；不改库的做法见 §24.9 | 根因：LVGL 用 `xTaskCreate`（`tskNO_AFFINITY`），非 SMP 内核把无亲和任务 **pend 到唤醒它的那个核** ⇒ 两个绘制线程挤在同一核。P4 **没有 SMP 内核**（`FREERTOS_SMP depends on !IDF_TARGET_ESP32P4`）⇒ 事后无法改亲和，只能在建线程那层：`LV_USE_OS=LV_OS_CUSTOM` |
| 2 | **渲染模式 FULL → DIRECT**（只重画脏区） | 31.8 → 35.7（+12%）| §24.4。DIRECT 双缓冲下 LVGL 自己把脏区同步进另一块（`refr_sync_areas`，CPU 拷贝）⇒ 这正是"能流水线"的前提 |
| 3 | **送屏与渲染重叠**（SRM `NON_BLOCKING` + 完成后换帧） | EEZ 路线：省掉串行的 ~8ms；自拼路线：旋转 7.3ms **完全隐藏**，`flush=0.6ms/帧` | §20（要素：非阻塞提交 + 独立补发任务 + **计数**信号量 + mutex）、§22、§24.1 |
| 4 | **`lv_display_set_tile_cnt(disp, 1)`**（DIRECT 下不切 tile） | 35.2 → 37.9（切 4 或 8 都更差）| LVGL 按 tile 数**重走对象树**，而像素分布并不会更均衡。tile 是给 `DRAW_UNIT_CNT>1` 找独立区域用的，双核已由手段 1 解决就不需要 |
| 5 | 编译/时钟基线：`-O2`、关断言、CPU 400MHz、SPIRAM 200MHz + `XIP_FROM_PSRAM`、L2 256KB/128B | 合计几个百分点；关断言 ≈0 但省 flash | §8。`LV_ATTRIBUTE_FAST_MEM_USE_IRAM=y` 已在 defaults |
| 6 | **仪表/后台任务优先级低于被测线程** | 37.8 → **38.8**（+1.0fps）| 同优先级会与 `swdraw` 时间片互抢。凡是自己写的采样/日志任务，都要压到低优先级并钉在有余量的核 |
| 7 | 观感不动的前提下：`LV_OBJ_STYLE_CACHE`、阴影/圆形位图缓存保持默认 | ≈0（测过 8→24 / 16→48 无变化）| 别指望它，留着是因为不影响观感也不影响性能（§24.4）|

---

## 4. 无效 / 负收益清单（省下这些弯路）

| 手段 | 实测 | 为什么不行 |
|---|---|---|
| **`CONFIG_LV_USE_PPA`（LVGL 的 PPA fill/blend 加速）** | **−8%**（33.7 vs 36.8）| 官方单元只接 FILL/IMAGE，且 `LV_PPA_NONBLOCKING_OPS` 被强制 0 ⇒ 绘制线程原地等硬件；还要独占对齐（`LV_DRAW_BUF_ALIGN=128`）并**与送屏 SRM 抢同一 2D-DMA** |
| **PARTIAL + 内部 RAM 分块绘制缓冲**（内部 RAM 写带宽 1036MB/s，是 PSRAM 的 5.8×） | **30.1** vs DIRECT 38.1 | LVGL 9.5 的 PARTIAL **每个 chunk 重走一遍对象树**，且跨块边界的对象被重复绘制 ⇒ 任务数 2.7×、像素功 1.6×，把带宽优势全吃掉。**只有脏区小到 1-2 块/帧时才占优** |
| 两个绘制线程都钉到同一个核 | 35.7 / 33.7 | 像素功在同一核排队；帧是在走树末端才创建完的，排队只会把帧尾推后 |
| LVGL 主线程优先级降到绘制线程之下 | 36.1（−2.7） | 延迟不是抢占造成的，是任务创建得太晚 |
| 走树期间提前喂任务 / 每 32 个对象 `lv_draw_dispatch()` | 38.2 vs 38.3（**一字不差**）| 限制在"同一层内任务必须按序"，不在喂料时机 |
| `DRAW_UNIT_CNT=1`（一核画、一核算树） | 33.1 | 退化成串行链：走树 8.4 + 画 19.2 + 动画 |
| 走树剪枝（跳过与脏区不相交的对象） | 上限只 +3fps | 实测"访问的对象里只有 25% 在脏区外"，而走树本身 8ms/帧 ⇒ 收益 ~2ms，不值得动语义（§24.3）|
| 提高 MIPI DSI lane 速率 | 无 | 500Mbps×2lane 远超需求（整帧 768KB@60fps ≈ 370Mbps） |
| 关屏上性能表 `LV_USE_PERF_MONITOR` | **测不出差异** | 它在 `LV_USE_SYSMON` 下被 Kconfig `default y` 强行置回 y，改 `sdkconfig` 那行无效 ⇒ 要关得连 sysmon 一起关；且用户要求保留 |
| 触摸读放在 LVGL 线程（`lv_indev` 回调里 `esp_lcd_touch_read_data`） | **35.7，最差帧 298ms** | GT911 会拉伸 I2C 时钟；判据是**帧率降 + `IDLE` 反而升 = 阻塞，不是算力不够**。改法：独立轮询任务写快照，回调只拷快照（§24.11）|

---

## 5. 四张根因卡片（遇到现象先看这里）

1. **`DRAW_UNIT_CNT=2` 是假的** → 看每线程 CPU/帧与所在核（§6 的测法），别信配置。修法见 §24.9。
2. **横屏旋转不能省** → ST7701 无 90° 硬件（§9）；旋转走 PPA 且必须"非阻塞 + 完成后再让面板扫它"，
   否则要么串行 8ms（§19.4 旧状态），要么拖影（只改 `NON_BLOCKING` 不改 `flush_ready` 时点 = 排序≠同步）。
3. **PPA fill/blend 越界写坏堆**（启动 ~0.5s 后 `Store access fault`，损坏值形如 RGB565 像素）→ §16；
   自拼管线**只用 SRM 不注册 fill/blend 客户端**即绕开；但注意护栏的盲区（见 §6 最后一条）。
4. **"写进了没在扫的那块 FB"** → `esp_lcd_panel_draw_bitmap()` 只有当传入指针**落在某块 FB 地址区间内**
   才是换指针（零拷贝），否则驱动 `do_copy` 永远写同一块 ⇒ 自拼管线必须"旋进 FB + 轮转 3 块"（§22）。

---

## 6. 怎么测（不改任何库源码）

- **每线程 CPU/帧 + 亲和核**：`CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS=y`（源=esp_timer ⇒ 单位就是 µs，
  选 `RUN_TIME_COUNTER_TYPE_U64` 免回绕）+ `CONFIG_FREERTOS_VTASKLIST_INCLUDE_COREID=y`（`xCoreID`
  给的是**亲和性**，固定核之后才可信），每秒 `uxTaskGetSystemState()` 快照按 handle 差分 ÷ 帧数。
  ⚠ 同一核各任务之和会比帧周期大 ~15%（中断/切换计入被中断任务）⇒ 只做**任务间横向比较**；
  看哪核有余量用 `IDLE0/IDLE1`。
- **送屏三段**：`wait_rot / srm_submit / flip`（定稿 0.00 / 0.61 / 0.01 ms）——`wait_rot` 非 0 就说明
  旋转跑到了关键路径上。
- **画面是否真的换代**：对 3 块面板 FB 采样哈希，每轮应 `changed=3/3`；另用 DSI `on_vsync` 计数
  证明面板在扫（哈希证明不了"在刷新"）。
- **PPA 落位（越界证据）**：涂黑一块 FB → SRM 旋入一个矩形 → 回读（先 `M2C` 失效，回读**不能**带
  `UNALIGNED`，驱动会拒）→ 数矩形内/外像素，判据 `inside==want && bleed==0`，含"边不在 128B 网格"和
  "16×16 内部小块"两种刁钻形态（`examples/mipi_dsi/test/`）。
- ★ **护栏有盲区**：4KB `0xA5` 尾区只能护住**自己分配的绘制缓冲**；`esp_lcd_dpi` 给的 FB 后面放不了护栏，
  而 §16 的事故正是发生在 fb 之后 ⇒ 要真闭死这条风险，周期跑 `heap_caps_check_integrity_all(true)`。

---

## 7. 硬约束（用户定的，优化时不许越）

1. **不改托管库源码**：`managed_components/**`（含 LVGL）必须与上游逐字节一致，**仪表也算改**；
   要钩子就用官方扩展点（`LV_OS_CUSTOM`、`lv_draw_create_unit`、`lv_display_add_event_cb`、Kconfig）。
   验证：`diff -rq managed_components/lvgl__lvgl <ComponentManager 缓存>/lvgl__lvgl_9.5.0_*` = 0 差异。
2. **屏上帧率指示器保持打开**（`LV_USE_PERF_MONITOR=y`）。
3. **不牺牲观感**：不关 `LV_DRAW_SW_COMPLEX`、不降色深、不改圆角/阴影/渐变来"换帧率"。
4. **一次一项改动 + 一次烧写**，测不到的数字要撤回并写进文档。
5. 配置文件（`sdkconfig.defaults`/Kconfig/CMakeLists）**只用 ASCII 注释**；改 defaults 后用
   "备份并删 `sdkconfig` → `idf.py reconfigure` → diff `build/config/sdkconfig.h`" 验可复现性
   （构建通路见 [`esp-idf-windows-build.md`](./esp-idf-windows-build.md)）。

---

## 变更记录

- 2026-10-11：从主文档拆出并补新页。新增/更新数据来自 `examples/mipi_dsi` R0-R48（自拼管线，
  定稿 **38.7-38.9fps 无触摸 / 37.9fps 带触摸**，`LVGL 线程 18.5-18.9ms/帧` 为 60fps 的判据），
  以及 §8/§19/§20（adapter 路线）与 §16/§22/§23/§24 的实测记录。
