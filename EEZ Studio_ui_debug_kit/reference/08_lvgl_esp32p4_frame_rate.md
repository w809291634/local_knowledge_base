# LVGL 在 ESP32-P4 上的帧率优化清单（本工程实测配置 + 可选项 + 出处）

> 生成日期：2026-10-06。工程：`p4_touch_lcd4_3_exp/lvgl_demo_ai`（ESP32-P4 + Waveshare 4.3" MIPI-DSI + LVGL 9.4 Espressif fork）。
> ★ 写法纪律：**每条都带文件行号出处**；没测过的数字一律标「待测」，不拿官网宣传当结论。

---

## 0. 最值钱的一条：PPA 有两条路，和「双核」的关系完全不同

想同时「用 PPA」和「双核渲染」的人，必须走第 2 条：

| 路线 | 开关 | 机制 | 与 `LV_DRAW_SW_DRAW_UNIT_CNT=2`（双核）的关系 |
|---|---|---|---|
| ① adapter 的 PPA | BSP profile `.enable_ppa_accel` | 用 `lv_draw_sw_register_blend_handler()` **替换软渲染的 blend/fill 实现**（`lvgl_ppa_accel_v9.c:51-74`，注册 BLEND + FILL 两个 PPA client，要求 RGB565） | **互斥**。源码注释：`PPA acceleration assumes draw unit count is forced to 1`，`>1` 时打 WARN（`display_manager.c:612-618`） |
| ② LVGL 原生 PPA draw unit | `CONFIG_LV_USE_PPA`（+ `LV_USE_PPA_IMG`） | 注册**第三个 draw unit "ESP_PPA"**，认领 `LV_DRAW_TASK_TYPE_FILL` / `IMAGE` 任务（`lv_draw_ppa.c:53-82,120-134`），与 2 个 SW unit 并存 | **不冲突**，不需要降到 1 |

⇒ 本工程要"PPA + 双核"，答案是开 `CONFIG_LV_USE_PPA`（路线②），**不是**把 BSP 里那个 `enable_ppa_accel` 打开。

---

## 1. 本工程当前状态（逐项出处，`sdkconfig` 行号为实测）

| 项 | 当前值 | 出处 | 说明 |
|---|---|---|---|
| LVGL | 9.4（Espressif fork） | `managed_components/lvgl__lvgl` | 有 `src/draw/espressif/ppa` |
| 颜色深度 | RGB565 | `sdkconfig:3272-3275` | PPA 也只吃 RGB565 |
| **SW draw unit 数** | **2（双核软渲染已开）** | `sdkconfig:3337` | ⇒「双核渲染」不是待办，已经在用 |
| 刷新周期 | 13ms（≈77fps 上限） | `sdkconfig:3297` | 调大只会更慢，调小不会变快 |
| **性能表** | **`LV_USE_PERF_MONITOR=y`（开着）** | `sdkconfig:3616` | 屏上右下角就是 FPS/CPU ⇒ **基线数字现在就能抄** |
| 快速代码进 IRAM | `LV_ATTRIBUTE_FAST_MEM_USE_IRAM=y` | `sdkconfig:3409` | 已开 |
| 绘制缓冲对齐 | `LV_DRAW_BUF_ALIGN=4` | `sdkconfig:3320` | ⚠ PPA/cache 更友好是 16/64（adapter 里 `ppa_align()` 取 `esp_cache_get_alignment(MALLOC_CAP_SPIRAM)`） |
| 离屏层预算 | `LV_DRAW_LAYER_SIMPLE_BUF_SIZE=24576` | `sdkconfig:3321` | transform / opacity 组图层走这里，超了就退软件合成 |
| 图片缓存 | `LV_CACHE_DEF_SIZE=0`、`LV_IMAGE_HEADER_CACHE_DEF_CNT=0` | `sdkconfig:3393-3394` | ⇒ 专辑封面每帧重新解头 |
| 样式缓存 | `LV_OBJ_STYLE_CACHE=y` | `sdkconfig:3397` | 已开 |
| SW 汇编 | `LV_DRAW_SW_ASM_NONE` | `sdkconfig:3344-3348` | RISC-V 上没有 ARM 那套 asm，这条在本平台是空选项 |
| `LV_USE_PPA` | **未开** | `sdkconfig:3356` | 路线②待试 |
| `LV_USE_OPENGLES` | 未开 | `sdkconfig:3668` | P4 无 GPU，别追 |
| 显示缓冲 | `use_psram=true`、`buffer_height=100`、`require_double_buffer=true`、`enable_ppa_accel=false` | BSP `esp32_p4_wifi6_touch_lcd_4_3.c:672-686` | 双缓冲已开 |
| 抗撕裂 | `TEAR_AVOID_MODE_TRIPLE_FULL` | `main/main.c:47` | ⇒ 每帧多一次全幅 PSRAM 搬运（800×480×2B=768KB/帧） |
| PSRAM | 32MB / 200MHz / XIP（.text/.rodata 都在 PSRAM） | 开机 log | 带宽是共享资源 |

---

## 2. 先度量，再动手（协议，别跳）

1. **抄基线**：`LV_USE_PERF_MONITOR` 已经开着 ⇒ 屏上就有 FPS + CPU%。三个固定场景各抄一次：
   ① 待机页（天气卡 8 秒自翻 + 260ms 翻转动效）；② 音乐页（唱片 npAnim 每帧改 angle + 歌词 5 行）；
   ③ 对话页灌满 100 条并滚动。
2. **一次只改一项**，同一场景重抄三个数字。混改 = 无法归因（本工程的铁律）。
3. 要 ms 级细节就在 flush 前后打 `esp_timer_get_time()`，把"绘制耗时"和"送屏耗时"分开看——
   两者的优化方向完全不同。
4. 正式版本记得关 perf monitor（它自己也要画字、也占一帧）。

---

## 3. 候选项，按性价比排序

### A. 应用侧（零依赖、零风险，先做这些）
1. **大面积 transform 是帧率杀手**：LVGL 对带 rotation/scale/opacity 组 的对象要先画进**离屏 ARGB 层**再合成（`lv_refr.c` 的 `lv_draw_layer` 路径）。本工程的天气卡翻转（rot+scale+opa 260ms）就是这种。
   缓解：缩小动效面积 / 只用 opacity 不用 scale+rot / 降低动效帧数（260ms 里 8 帧就够，不必每帧）。
2. **npAnim 每帧改唱片 angle** ⇒ 每帧 invalidate 唱片那块并重画。缓解：把链里的 `Delay` 拉长（等于降帧），或页面不可见时停链。
3. **自动宽度 label 每次换文本都重算布局**（本工程 DSL 的 label 默认 `wUnit=content`）。缓解：固定宽度 + 只在内容真变化时 `set_text`。歌词已经这么做（行号不变就一格都不写，P-0118）。
4. 少用大面积阴影、渐变、圆角叠加（缓存只有 16/8 个槽）。

### B. 配置侧（改 Kconfig，不动代码）
5. **`CONFIG_LV_USE_PPA=y`（+ `LV_USE_PPA_IMG=y`）** —— 路线②，保双核。
   ⚠ 风险要先看：本 adapter 组件带 `0001-bugfix-lcd-Fixed-PPA-freeze.patch`，CHANGELOG 有
   "Fix a crash that occurred in some cases when PPA acceleration was enabled" ⇒ 开之前确认依赖版本已含修复；
   PPA 只吃 RGB565，且有 cache 对齐要求（见下条）。
6. `LV_DRAW_BUF_ALIGN` 4 → 16 或 64：PPA/DMA + cache 一致的友好对齐。
7. `LV_CACHE_DEF_SIZE` / `LV_IMAGE_HEADER_CACHE_DEF_CNT` 从 0 抬起来：专辑封面、图标反复被画时省重复解头。
8. `LV_DEF_REFR_PERIOD` 13 → 16/20 不是提速，是"允许更低"；反过来调到 5 也不会更快（受绘制能力限制），只会白烧 CPU。

### C. 显示链路（要改 BSP/共享组件 ⇒ 先征得同意）
9. `enable_ppa_accel = true`（路线①）：**必须同时把 `LV_DRAW_SW_DRAW_UNIT_CNT` 降回 1**（源码写死的要求）。
   所以它和 5 是**两条互斥的路线**，收益要各测一遍再定，不能想当然叠加。
10. `tear_avoid_mode` 从 `TRIPLE_FULL` 降级（两缓冲 / 不抗撕裂）：省下每帧那 768KB 的 PSRAM 搬运。
    代价是可见撕裂——要不要换，是产品决定，不是技术决定。
11. `buffer_height=100` 的分块高度与 render mode（partial / full / direct）要配着调：
    分块小 = 一次绘制少、但要多次送屏；分块大 = 反之。

### D. 结构性（本工程已有规矩）
12. **P4 零阻塞铁律本身就是帧率保障**：任何在 LVGL 线程里做的同步 IO、`portMAX_DELAY` 取锁、
    HTTPS/SD 读，都会直接吃掉那一帧。慢操作一律进工作任务 + 快照过桥（见 §11.22 与 P-0113/P-0115）。
13. **PSRAM 带宽竞争**：播放音乐时同时有 SD→PSRAM 缓冲、解码、I2S 取数，DSI 每帧还要从 PSRAM 读帧缓冲。
    若"一放歌就掉帧"，先量带宽/内存争用，再怀疑渲染（本工程已有一起 PSRAM 堆被踩的未结案例，P-0115/P-0117）。

---

## 4. 明确没做的事（诚实记账）

- **没测过基线 FPS**：perf monitor 开着但没人抄过数 ⇒ 本清单是「可选项 + 出处」，不是「已验证收益」。
- **「双核渲染」不是待办**：`LV_DRAW_SW_DRAW_UNIT_CNT=2` 早已生效；真正待决的是 PPA 走哪条路线。
- 路线①/②各自的实际增益、TRIPLE_FULL 的带宽代价，都要真机数字才能写结论。
