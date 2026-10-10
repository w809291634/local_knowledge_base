# LVGL 在 ESP32-P4 上的帧率优化清单（本工程实测配置 + 可选项 + 出处）

> **第二版（2026-10-06 同日更正）**。第一版是错的，而且错得危险：我把**已被实测证明必崩、
> 并且被刻意关掉**的 `enable_ppa_accel` 当成"待试优化"写进清单，还推荐了一条未测的 PPA 路线。
> 根因是取证范围不全——我只在 `EEZ Studio_ui_debug_kit/` 里 grep 了「帧率/PPA/FPS」就说"全库零命中"，
> 而**同一知识库的另一个子库 `local_knowledge_base/esp32/` 里早有整篇实测结论**。
> ★ 权威出处（先读这两节，本文只是索引 + 本工程当前配置）：
> - `../esp32/esp32-p4-lvgl9-touch-lcd-debug-optimization.md` **§8 帧率优化清单（横屏+PPA 约束下已到顶）**
> - 同文 **§16 LVGL PPA 绘制单元 DMA 越界写 → PSRAM 堆损坏崩溃（禁用 enable_ppa_accel 解决）**
> - 工程侧历史：`prompts/PROMPT_LOG.md` **PR-0093**（帧率下降根因 = WifiManager 轮询过频，hosted RPC 阻塞 LVGL 线程）、
>   `.workbuddy/memory/2026-10-03.md`（帧率三项：tick 5ms→16ms、`io_sample_inputs` 变化才发布、NVS+codec 移出 LVGL 线程）

---

## 0. 结论先说：这个板子的帧率天花板不在"渲染配置"

1. **横屏是软件旋转，物理瓶颈消不掉**（esp32 文 §9）：ST7701 是 480×800 竖排 RGB/MIPI-DSI video-mode 面板，
   MADCTL 只能镜像、**没有 90° 行列交换硬件** ⇒ 800×480 必须软件/PPA 旋转每一帧。
2. **PPA 绘制加速在本组件版本上 = 必崩**（esp32 文 §16，板上实锤）：
   `.enable_ppa_accel = true` 时启动约 0.5s（首帧整屏刷新）就 `Store access fault`，
   栈在 TLSF（`remove_free_block`/`block_trim_used`/`tlsf_malloc`）；被覆盖的 free-list 值是
   `0xAEABAFDE` 这种**典型 RGB565 像素颜色** ⇒ 是 PPA fill/blend 的 DMA 按 128B 块凑整、
   在帧缓冲末端越界写（一行 480px×2B=960B，960÷128=7.5 除不尽 + 脏块边缘悬空）。
   ⇒ **BSP 里那个 `false` 是修复结果，不是"还没优化"**（`esp32_p4_wifi6_touch_lcd_4_3.c:685`）。
3. **历史上真正的掉帧原因都在 LVGL 线程被阻塞**（PR-0093 + 10-03 三项），不是渲染参数：
   hosted RPC 轮询、NVS 写、codec 调用、tick 过密。⇒ 排查顺序应该反过来：
   **先看任务表和线程占用，再看渲染配置。**

---

## 1. 已排除的提速路径（别再做，出处 esp32 文 §8）

| 路径 | 结论 | 原因 |
|---|---|---|
| `enable_ppa_accel = true` | **禁止** | §16：DMA 越界写坏 PSRAM 堆，必崩 |
| 多核 `LV_DRAW_SW_DRAW_UNIT_CNT=2` 换 PPA | 二者互斥 | adapter 源码写死 PPA 要求 unit==1（`display_manager.c:612-618`）；PPA 既然禁用，多核就是剩下的选项——**当前已经是 2**（`sdkconfig:3337`） |
| MIPI-DSI lane 提速 | 无效 | 500Mbps×2lane 远超需求，非瓶颈 |
| `LV_OS_NONE` + 手动互斥循环 | 无效且有害 | 锁不是瓶颈；还会破坏 adapter 的撕裂规避与 PPA 同步 |
| CPU 频率 / 优化等级 / PSRAM 速率 | 已到顶 | 400MHz（CPLL 上限）、`-O2`（IDF 无 -O3、无 LTO）、PSRAM 200MHz + XIP |
| PSRAM 大绘制缓冲 | 有前置坑 | esp32 文 §4：`heap_caps_aligned_alloc` 无 fallback；当前 BSP 注掉一句 "DIAG: 绘制缓冲改 PSRAM 释放内部 RAM"（`:683`）⇒ **这一条与 §8 的"100 行内部 RAM 双缓冲"已经不一致，改之前要先确认当初为什么挪去 PSRAM、有没有触发 §4 的分配失败** |

---

## 2. 本工程当前状态（实测值，行号为 `sdkconfig` / 源文件）

| 项 | 当前值 | 出处 |
|---|---|---|
| LVGL | 9.4（Espressif fork，有 `src/draw/espressif/ppa`） | `managed_components/lvgl__lvgl` |
| 颜色深度 | RGB565 | `sdkconfig:3272-3275` |
| SW draw unit | **2（双核软渲染已开）** | `sdkconfig:3337` |
| 刷新周期 | 13ms | `sdkconfig:3297`（§8 建议 10ms；10-03 那轮把 tick 从 5ms 放宽到 16ms——**两处口径要对齐，别再改回去**） |
| 性能表 | `LV_USE_PERF_MONITOR=y`（开着） | `sdkconfig:3616` ⇒ 屏上就是 FPS/CPU，**基线随时能抄** |
| 快速代码进 IRAM | 已开 | `sdkconfig:3409` |
| 绘制缓冲对齐 | 4 字节 | `sdkconfig:3320`（PPA/DMA 想要 128B 对齐——但 PPA 已禁，这条只对"改缓冲位置"有意义） |
| 离屏层预算 | 24576 | `sdkconfig:3321`（transform/opacity 组图层走这里） |
| 图片缓存 | 全 0 | `sdkconfig:3393-3394` |
| 阴影/圆形缓存 | 16 / 8 | `sdkconfig:3342-3343`（与 §8 一致） |
| `LV_USE_PPA`（LVGL 原生 draw unit，另一条路） | 未开 | `sdkconfig:3356` |
| 抗撕裂 | `TRIPLE_FULL` | `main/main.c:47` |
| 面板旋转 | 软件旋转（横屏必需） | esp32 文 §9 |

---

## 3. 还想提速，只剩这些（按性价比，全部要求"一次一项 + 抄基线"）

### A. 应用侧（零风险，本项目已有成功先例）
1. **先查 LVGL 线程有没有被阻塞**（本项目历史上唯一真正有效的方向，PR-0093）：
   开 FreeRTOS 任务表/CPU 监控（esp32 文 §12.3），看 `ui`/LVGL 任务的占用与等待；
   任何同步 IO、`portMAX_DELAY` 取锁、HTTPS/SD 读、NVS 写都要挪到工作任务 + 快照过桥。
   ★ 本工程还留着一处形式违规：`io_music_player_play/stop/mute` 用 `portMAX_DELAY` 且调用点在 LVGL 线程。
2. **发布节流**：值没变就不写变量（10-03 已做 `io_sample_inputs` 变化才发布；歌词按行号变化才发布）。
3. **少画**：大面积 transform（天气卡翻转 = rot+scale+opa ⇒ 走离屏 ARGB 层再合成）是本项目自己加的
   最大绘制负载；npAnim 每帧改唱片 angle 也是。缓解 = 缩面积 / 只用 opacity / 拉长动画帧间隔 / 页面不可见时停链。
4. 自动宽度 label 每次换文本都重算布局 ⇒ 固定宽度 + 变了才写。

### B. 配置侧（低风险，但要实测）
5. `LV_CACHE_DEF_SIZE` / `LV_IMAGE_HEADER_CACHE_DEF_CNT` 从 0 抬起（封面、图标反复画）。
6. `LV_DEF_REFR_PERIOD` 与 tick 对齐（13 vs §8 的 10 vs 10-03 的 16ms）——**先统一口径再谈数值**。
7. `CONFIG_LV_USE_PPA`（LVGL 原生 ESP_PPA draw unit，与 adapter 那条**不是同一个开关**）：
   ⚠ **未测，且风险同类**——它同样是 DMA 写帧缓冲的路径，§16 的"按块凑整越界"机理对它一样成立。
   要试也只能在**能随时回退**的炉子里试，并且第一判据就是：启动 0.5s 内会不会再出现
   TLSF `remove_free_block` 崩溃 + 被覆盖值是不是像素颜色。**默认结论：不试，收益不确定、代价是堆损坏。**
   - ★ 2026-10-10 已测（`intake/P-0120`，见 §7 表 H 行）：横屏 widgets 满负荷滚动下 **35.8 vs 37.0 = 无收益**，
     45s 未见 TLSF 崩溃；但**没必要承担这个风险**。另记：它有两道硬前置
     （`LV_DRAW_BUF_ALIGN==64` + `LV_ATTRIBUTE_MEM_ALIGN_SIZE==64`，否则 `lv_draw_ppa_private.h:40-42` 直接 `#error`；
     lvgl 组件还不含 `esp_driver_ppa`/`esp_mm` 头路径）。

### C. 显示链路（要改共享组件 ⇒ 先问用户）
8. `tear_avoid_mode` 从 `TRIPLE_FULL` 降级：省每帧全幅 PSRAM 搬运。代价 = 可见撕裂，属产品决定。
9. 绘制缓冲回到内部 RAM（对齐 §8 的"100 行内部 RAM 双缓冲"）：省 PSRAM 带宽，
   但会吃紧内部 RAM（esp32 文 §4/§17 的账），且当前那句 "DIAG" 改动的原因还没查清。

---

## 4. 度量协议（没有基线就别改配置）

1. 屏上 perf monitor 抄 FPS/CPU；三个固定场景：①待机页（天气卡翻转）②音乐页（唱片动画+歌词）
   ③对话页灌 100 条并滚动。
2. **一次只改一项**，同场景重抄（本项目铁律：混改无法归因）。
3. 要 ms 级就在 flush 前后打 `esp_timer_get_time()`，把"绘制耗时"和"送屏耗时"分开——方向不同。
4. 正式版关 perf monitor。

---

## 5. ★ 与当前未结崩溃的联动（这条最实用）

现在挂着的「播放音乐 + WiFi RX 时 PSRAM 堆空闲链表被踩」（P-0115 追加 / P-0117）症状形态
= `remove_free_block` 里写 `next->prev_free`、`MTVAL` 是小常数 —— **和 esp32 文 §16 的崩溃形态同类**。
所以取证时先做这两件事，能省一轮：
1. **看被覆盖的 free-list 值是不是像素颜色**（RGB565 那种 `0xAExx BAxx` 模式）：
   是 ⇒ 显示/DMA 路径写穿；不是 ⇒ 才轮到音频缓冲/解码器/静态表越界。
2. **量损坏点相对哪个大缓冲的末端**（esp32 文 §16.3 的方法：把 fb0/fb1/fb2 与我们的
   `s_raw/s_pcm/s_res`、歌词表的地址打出来，看谁后面紧跟空闲块）。
   ★ 注意本工程 PPA 是**关着**的，所以 §16 那条具体成因不成立；但**方法**完全适用，
   且我们也有 DMA 参与的路径（SDMMC 读、I2S 写）与 PSRAM 大缓冲。

---

## 6. 本文的更正记录

- 第一版（同日 20 分钟前）错在三处：①把已实测必崩的 `enable_ppa_accel` 列为"候选优化"；
  ②把未测的 `CONFIG_LV_USE_PPA` 推荐成"保双核的正解"；③声称"知识库此前无此总结"——
  实际漏搜了 `local_knowledge_base/esp32/` 子库与 `.workbuddy/memory/` 工程日志。
- 教训（已同步进 `skills.md §11.30` 的更正段）：**"全库没有"这种话，必须先把所有子库和工程日志
  一起 grep，或者干脆问用户一句"这块以前做过吗"。**

---

## 7. ★ 2026-10-10 实测：`08_lvgl_demo_v9_opt` 横屏 widgets demo（`intake/P-0120`）

工程：`examples/08_lvgl_demo_v9_opt`（干净示例工程，无 EEZ/无网络，纯 LVGL 负载）；
负载：`lv_demo_widgets()` + `lv_demo_widgets_start_slideshow()`（持续滚动，实测每帧重绘 **84%** 屏）；
度量：`CONFIG_ESP_LVGL_ADAPTER_ENABLE_FPS_STATS=y` + `esp_lv_adapter_get_fps()` 每秒一条串口日志（COM20），
并用 `LV_EVENT_FLUSH_START/FINISH` 把「送屏」与「绘制」拆开。45s 一轮（终版 90s，84 个采样）。

| 轮 | 配置（其余同前） | 均值 | 最低 | 峰值 | 送屏 | 绘制 |
|---|---|---|---|---|---|---|
| 空载 | 出厂示例，静止画面 | 3.1 | 3 | 7 | — | **每帧恒 300ms** = 性能表周期，非瓶颈 |
| A | `buffer_height=50`(14块/帧) 单核 | 23.4 | 15 | 34 | 5.4 | 45 |
| B | bh=50(14块) **双核** | 19.9 | 12 | 32 | 5.5 | 57 |
| C | bh=128(6块) 单核 | 29.9 | 21 | 37 | 6.7 | 20~40 |
| D | bh=128(6块) 双核 | 29.3 | 20 | 39 | 6.7 | — |
| E | `TRIPLE_FULL` 整屏渲染 | 25.7 | 21 | 29 | 7.8 | 27~40 |
| F | **bh=200(4块) 单核** | 35.2 | 25 | 43 | 4.8 | 18.5~35 |
| G | **bh=200(4块) 双核 ← 最佳** | **37.0** | **26** | **47** | 4.8 | 16~33 |
| H | G + `LV_USE_PPA`(+IMG) 真生效 | 35.8 | 26 | 48 | 4.8 | 指纹 `lv_ppa=1` 确认生效 |
| I | G + `LV_DEF_REFR_PERIOD` 15→10 | 36.0 | 26 | 47 | 4.8 | 无收益（连续动画下没有节拍量化损失） |
| J | bh=267(想要 3 块/帧) | 起不来 | — | — | — | `alloc primary buffer 256320 bytes failed` → assert `esp32_p4_wifi6_touch_lcd_4_3.c:690` |
| K | L2 cache 512KB | 起不来 | — | — | — | `Could not reserve internal/DMA pool (0x101)` → abort `app_startup.c:179` |

**新增结论（补 §0/§1/§3 的缺口）**：

1. **绘制分块高度是本项目实测最大的单项抓手**（+58%：23.4→37.0），比双核、比 PPA 都有效。
   机理是 adapter 在旋转下把块算小了：`TRIPLE_PARTIAL` 的绘制缓冲 = **面板** `hor_res(480) × buffer_height`
   （`display_manager.c:868-872`），而 `ROTATE_90` 后 LVGL 宽 800 ⇒ 每块只有 `0.6 × buffer_height` 行。
   `buffer_height=50` 名义 50 行，实际 30 行 → 一帧 16 块；块边界是同步点。
2. **双核收益随块大小变号**：14 块时 `DRAW_UNIT_CNT=2` **更慢**（19.9 vs 23.4），4 块时才转正（37.0 vs 35.2）。
   与 esp32 子库 §19 记的 "+6fps" 一致——那条正是在大块配置下测的。
3. **上限是内部 RAM，不是想要多少块都行**：bh=267（256KB 连续内部 RAM）直接分配失败并 assert 复位循环；
   bh=200（192KB）是这套 BSP 的实际上限 ⇒ **4 块/帧到头了**。
4. **送屏不是瓶颈**（4.8ms/帧，含 PPA SRM 旋转 4 次 + 整幅 DSI blit）；瓶颈是**逐像素软件混合**：
   重相位（Analytics：表格/图表/大量文字）绘制 32ms，轻相位 16ms，面积都是 84%。
   PPA 帮不上忙的原因见 `skills.md §11.31` 第 5 条（没有 per-pixel mask 输入，圆角/描边/字形 AA 全部留在 CPU）。
5. ⇒ **40fps 最低帧率在这个满屏滚动场景下拿不到**（实测最低 26）。要过 40 只有两条：
   把动画面积压到 <50%（轻相位本来就 47~48fps），或者改 adapter 让渲染与送屏重叠
   （`TRIPLE_PARTIAL` 把 `draw_buf_secondary` 写死 NULL，`:871`，属于共享组件改动）。

