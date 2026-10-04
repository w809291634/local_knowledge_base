# P-0115 · 曲库接真 SD 卡：BSP 的 bsp_sdcard_mount 早就链进固件只是没人调用；FATFS 关着长文件名 + API 编码默认 ANSI 会让中文歌名变豆腐

- **工程**：eez-test
- **日期**：2026-10-04
- **工具**：Qoder
- **状态**：open
- **标签**：SD卡,SDMMC,FATFS,长文件名,UTF-8编码,曲库,lv_list重灌,generation,假反馈,ESP_PLATFORM分界,无热插拔
- **关联提示词**：PR-0178

## 现象（看到什么）

曲库/播放页全是内置演示表（app_model.cpp 硬编码 6 首，ui_data_sync 一次性闸门灌完就锁死），与真机无关。用户要求改成从 SD 卡读。

## 复现（怎么稳定重现）

真机：音乐页列表永远那 6 首；插着卡也不变。PC：EEZ_SIM_SD 无从模拟，空态根本看不到。

## 根因（真正的原因）

三块。①硬件：这块板 SD 走 **SDMMC slot0 / 4bit**（CLK43 CMD44 D0-D3=39..42，片内 LDO 通道 4 供电），BSP 里 `bsp_sdcard_mount()` 已实现且**已链进 ELF**，全工程无人调用；卡检测脚没接（slot_config.cd=NO_CD）⇒ 天生没有热插拔。②文件系统：`CONFIG_FATFS_LFN_NONE=y` 时长文件名根本读不出来；而且 `FATFS_API_ENCODING` 的 **默认是 ANSI/OEM**（components/fatfs/Kconfig:126-132）⇒ 不改 UTF-8 就把 GBK 字节喂给 UTF-8 字库。③UI 数据流：曲表一次性闸门 + 链表只追加不重置 ⇒ 换表必然重灌/漏内存。

## 修复（做了什么）

新增 platform/io_sdcard.{h,cpp}：挂载+扫描放**一次性任务 ui_sd_scan**（prio 3，扫完 vTaskDelete 自杀），结果写快照；LVGL 线程每拍 io_sdcard_publish() 比生成号，变了才 memcpy + app_songs_replace + 发状态文案。app_model 的曲表改成可整表替换（`app_songs_replace/_generation`，静态表 64×96B，读写都在 LVGL 线程 ⇒ 不加锁），ui_data_sync 从一次性闸门改成**盯 generation**（列表指针缓存 + lv_obj_clean 重灌 + song_list_reset 释放旧节点）。扫描只收 /sdcard/music 一层的 .mp3/.wav（大小写不敏感、去扩展名当歌名、qsort 按名字排、上限 64）。sdkconfig + sdkconfig.defaults 同时开 FATFS_LFN_HEAP + API_ENCODING_UTF_8 + MAX_LFN=255。正在播放页 np_title/np_sub 从 16px/12px 降到 **13px 档**（那一档已烘 GB2312 一二级，任意中文歌名零风险、零体积）。★ 诚实性：扫描没结果时**真的清空曲表**并显示『未插入SD卡/未建 music 目录/SD卡里没有音乐/SD卡读取失败』，而不是留着演示歌冒充真内容（我第一版写的就是 n>0 才替换，自己审出来了）。

## 证据（数字 / 命令输出）

挂载参数逐条来自代码：components/esp32_p4_wifi6_touch_lcd_4_3/esp32_p4_wifi6_touch_lcd_4_3.c:151-187 与 include/bsp/...h:50-55,212；与 C6 的 esp_hosted（SDIO slot1 / GPIO14-19）不同槽不同脚，不冲突。PC 侧：门禁 all.py --sim rc=0、9 屏 9.92%，逐屏与上一轮差 ≤0.03pp（默认态文案为空串 ⇒ 基线不动是**正确结果**）；另用 `EEZ_SIM_SD=nocard` 直接驱动仿真 exe 出图，目检曲库页 = 『音乐库 0 首 未插入SD卡』+ 空列表，13px 中英混排无豆腐块；np_title 已确认生成物里 font=YaHei_Consolas_Hybrid_13（查 design/ui.json:1453）。真机侧：reconfigure 后 compile_commands 收录 io_sdcard.cpp（4 次命中，2405 条），7 个 native 文件官方命令全 rc=0/0 错/0 警；idf.py build rc=0（2470 步），src/native 零警告，bin 0x4CCAB0 → **0x4D7E10**（+69KB：FATFS LFN + 扫描模块），分区空闲 40%→39%。

## 沉淀（新增断言 / 案例 / 文档）

①新建设备专属文件仍要 `#if ESP_PLATFORM` 划界，但**共用部分（文案/表）要留在界外**，否则 PC 侧拿不到同一份措辞，两端文案就会漂。②CMakeLists 的 EEZ_SIM 分支也要收这个文件（本工程 PC 是 GLOB 收 src/native，IDF 侧是显式列表 ⇒ 两边都要写，漏一边就 undefined 或空实现）。③『一次性闸门』型 UI 灌入在数据可变时必须改成 generation 比对，同时补链表 reset（只回头尾指针 = 漏内存）。④sdkconfig 改动一律同步 sdkconfig.defaults（本轮 LFN/UTF-8 两处都写了）。⑤待办：批B 播放（esp-audio-player 注 write_fn 到小智 codec + 播放时 EnableWakeWordDetection(false)）；无热插拔这条要在 UI/文档里如实说明（插卡需重启）。

## ★ 追加（真机第一轮）：任务被自己的局部变量打穿栈 —— Core0 Stack protection fault

用户烧完直接 Guru Meditation：

```
Guru Meditation Error: Core 0 panic'ed (Stack protection fault).
Detected in task "ui_sd_scan" at 0x4809826e
--- sd_scan_once() at .../io_sdcard.cpp:94
Stack pointer: 0x4ffa6450   Stack bounds: 0x4ffa64f8 - 0x4ffa7cf0
--- 0x4809874a: bsp_sdcard_mount at .../esp32_p4_wifi6_touch_lcd_4_3.c:165
```

算术就是结论：栈区 `0x4ffa7cf0 - 0x4ffa64f8 = 0x17F8 = 6136B`（我给的 6144），
而 `sd_scan_once()` 开头写着 `sd_snap_t s;` —— 这个结构体是
`char names[64][96] + int + enum` = **6152B**，**比整个任务栈还大**。
函数一进来压栈就把 SP 顶到栈底之外，崩在哪一行只是运气（这次崩在 `bsp_sdcard_mount` 里面）。

修法（两条一起做，缺一不可）：
1. **工作区改文件级静态** `static sd_snap_t s_work;`，函数里 `sd_snap_t *const s = &s_work;`
   ⇒ 栈上只剩指针。发布侧的 `s_pull[64][96]` / `s_ptrs[64]` 本来就是 `static`（写的时候就是按
   "别上栈"写的，只有扫描函数漏了 —— 说明这类错误是**局部**的，不能靠"整体风格"保证）。
2. 栈 6144 → **8192**（FatFS 挂载 + opendir 自己要几百到上千字节），
   并在扫描结束打一条 `uxTaskGetStackHighWaterMark(NULL)*sizeof(StackType_t)` 的真实余量，
   下次烧完一眼看到用量，不用再猜。

顺手把同批新写的其它函数都按同一把尺量了一遍（**证据 = 手算局部量**）：
`wx_fetch_once` 最大局部是 `char url[512]` + `wx_entry_t parsed[4]`(≈384B) + config(≈100B) < 1KB，
栈 8192 ⇒ 安全；`io_weather_publish` 局部 ~96B ⇒ 安全；`io_sdcard_publish` 全静态 ⇒ 安全。

验证：`design/_verify_weather.py` 7 个 native 文件官方命令 rc=0、0 错 0 警；
`idf.py build` rc=0，bin `0x4D7E10 → 0x4D7EC0`，分区空闲 39%，src/native 零警告。

⇒ 通则（值得进 skills）：**给 FreeRTOS 任务定栈大小时，必须先算它调用的每个函数里的最大局部对象**；
超过 ~1KB 的缓冲/结构体一律 static 或 heap，"任务栈 = 结构体大小"这种巧合就是定时炸弹。
小任务（<8KB）里放 6KB 局部量，编译器不会警告、静态检查不会报、PC 仿真根本不会跑这段 ——
**只有真机会炸**，所以这类代码必须"写完就手算一遍栈用量"。


## ★★ 追加（同一次真机第二轮）：Core0 Store access fault @ transport_drv_sta_tx —— SDIO 发送池取空 + assert 被 release 编掉

日志现场：
```
I (16583) HttpClient: Established new connection to api.tenclass.net:443 protocol=https cost=4965
Guru Meditation Error: Core 0 panic'ed (Store access fault).
MEPC: memcpy .../newlib/src/port/riscv/memcpy.c:89
RA  : transport_drv_sta_tx at esp_hosted/host/drivers/transport/transport_drv.c:242 (inlined by :215)
A0 = 0x0000000c   A2 = 0x20   MTVAL = 0x0000000c
```

三个数字对上就是结论：
1. `transport_drv_sta_tx` 里是
   `copy_buff = mempool_alloc(memp, MAX_TRANSPORT_BUFFER_SIZE, true); assert(copy_buff); memcpy(copy_buff + H_ESP_PAYLOAD_HEADER_OFFSET, buffer, len);`
2. `H_ESP_PAYLOAD_HEADER_OFFSET = sizeof(struct esp_payload_header)`，该结构 packed = **12 字节**；
3. 崩时 memcpy 的 dst = `0xc` ⇒ `copy_buff + 12 = 12` ⇒ **copy_buff == NULL**，
   而 `assert()` 在 release（NDEBUG）下被整个编掉 ⇒ 直接写空指针偏移。
   （`mempool_alloc` 第三参只是 need_memset，**不会阻塞等待**，取不到就是返回 NULL。）

再一条关键事实（决定它和"我加了功能"有没有关系）：
`host/drivers/mempool/mempool.h` 里
`#define MEM_ALLOC(x) heap_caps_aligned_alloc(64, x, MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA | MALLOC_CAP_8BIT)`
⇒ **SDIO 发送缓冲只从内部 DMA RAM 拿**。开机那句 `sdio_mempool_create free:28900312` 是 PSRAM，
和这个池不是一回事，别被那个 28MB 骗了。

### 本轮我做了什么（把自己吃掉的内部 RAM 还回去，并把判据打出来）
| 项 | 改前 | 改后 | 省 |
|---|---|---|---|
| io_sdcard 快照 | s_snap + s_work + s_pull 各 6152B | 只留 s_snap（扫描直接在锁内写它；发布只拷 32 个指针） | **−12.3KB .bss** |
| app_model 曲表 | 64 × 96 = 6144B | 32 × 64 = 2048B | **−4.1KB .bss** |
| 观测 | 无 | 扫描完打 `internal free=? maxblock=?`（`heap_caps_get_free_size/largest_free_block(MALLOC_CAP_INTERNAL)`） | 下次一眼看出是不是内部 RAM 见底 |
顺带修掉一个自己埋的坑：`io_sdcard_publish` 原来是**先吃掉 generation 再去有界拿锁**，
拿失败就把这一代吞了 ⇒ 曲库可能永远停在旧内容；改成拿锁成功才提交 generation。

### 还没做、需要单独一炉验证的（时序，会改变行为，不能和上面的"还内存"混在一炉归因）
1. **并发 HTTPS**：崩在 OTA(`api.tenclass.net`) 建连之后 0.5s 内，而天气抓取正好也在这个窗口起（wifi_up 于 11.5s，
   任务每 5s 醒一次）⇒ 两条 TLS 会话同时在跑。可选：天气首抓延后（开机 30~60s）、或 AI 非"在线·待命"时跳过本轮。
2. **加大 esp_hosted 队列**：`CONFIG_ESP_HOSTED_SDIO_TX_Q_SIZE` 现在没写进 sdkconfig ⇒ 走默认 20（Kconfig:909）。
   这是 Kconfig 不是组件源码，允许改。
3. 组件里那个 `assert(copy_buff)` 是 esp_hosted 的健壮性缺口（该丢包而不是 panic），
   但 **managed_components 不能改**（.component_hash + gitignore）⇒ 只能从我们自己这侧降负载/加队列，并把现象记库上报上游。

验证：7 个 native 文件官方命令 0 错 0 警；`idf.py build` rc=0、bin `0x4D7EC0 → 0x4D7E70`、src/native 零警告。

