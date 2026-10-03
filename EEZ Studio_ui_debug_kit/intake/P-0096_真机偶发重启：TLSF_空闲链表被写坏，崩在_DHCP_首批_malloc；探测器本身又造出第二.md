# P-0096 · 真机偶发重启：TLSF 空闲链表被写坏，崩在 DHCP 首批 malloc；探测器本身又造出第二个崩溃

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：open
- **标签**：崩溃,heap,TLSF,addr2line,esp_hosted,中断看门狗, sdkconfig
- **关联提示词**：PR-0126

## 现象（看到什么）

连上 WiFi 后 Guru Meditation Core1 Store access fault，MTVAL=0x0000000c；栈解出 remove_free_block / block_locate_free / tlsf_malloc / heap_caps_malloc_prefer / mem_malloc / dhcp_handle_offer。开了堆探测器重烧后，变成 551ms 的 Interrupt wdt timeout on CPU1（vListInsert / vTaskPlaceOnEventList），原问题反而没复现。

## 复现（怎么稳定重现）

烧录带 CONFIG_HEAP_POISONING_COMPREHENSIVE=y + CONFIG_HEAP_TASK_TRACKING=y 的版本，开机自动连网即复现第二种；原始崩溃在纯自动连接路径偶发（用户日志未必现）。

## 根因（真正的原因）

第一种：堆元数据早被越界写或 use-after-free 破坏，直到 lwIP 成批分配才撞上，真凶在更早。第二种：探测器自身开销（全块 poison+canary 校验、记任务句柄）落在 esp_hosted 建 SDIO 内存池的关中断批分配区间，超过 CONFIG_ESP_INT_WDT_TIMEOUT_MS=800。另注意 sdkconfig 里 ASSERTIONS_DISABLE 把 configASSERT 编掉，误用只静默踩堆不报警。

## 修复（做了什么）

解码姿势固定：先比 build/lvgl_demo_v9.elf 的 sha256 前缀与日志 ELF file SHA256 一致再用地址；addr2line 在 esp-idf-tools_for_idf_v5_5_1/tools/riscv32-esp-elf/... 排查档降到 POISONING_LIGHT 并关 TASK_TRACKING；HEAP_POISONING_* 是 choice，改一个必须把另一个写成 is not set，否则 kconfgen 静默改回。原崩溃仍未定位。

## 证据（数字 / 命令输出）

两次崩溃地址都解到具体行；sdio_mempool_create 是崩溃前最后一行日志；生效配置从 build/config/sdkconfig.h 读出。

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md 增加崩溃解码与探测器降档两条纪律；sdkconfig 属排查期临时项
