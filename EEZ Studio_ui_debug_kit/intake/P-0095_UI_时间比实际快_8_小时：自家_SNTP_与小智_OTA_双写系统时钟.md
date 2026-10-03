# P-0095 · UI 时间比实际快 8 小时：自家 SNTP 与小智 OTA 双写系统时钟

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：时间,SNTP,OTA,settimeofday,时区,息屏,双写冲突
- **关联提示词**：PR-0130 / PR-0131

## 现象（看到什么）

待机页显示 22:44，实际 14:44；且有时候对有时候错，时间还会自己来回跳。

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

xiaozhi-esp32/main/ota.cc:193-206 把 server_time 的 timestamp + timezone_offset 直接 settimeofday —— 系统时钟里存的是本地时间；而 io_esp 的 sntp_ensure_started 在首次 Connected 后起 esp_sntp（写回 UTC）并 setenv TZ=CST-8，localtime 再加 8 小时。两个源互相覆盖：OTA 后写=显示 +8，SNTP 后写=正确。同一根因还导致息屏计时（time(NULL) 差值）被时钟阶跃瞬间推过超时线。

## 修复（做了什么）

用户定案：以小智 OTA 的 server_time 为唯一时间源。删掉 sntp_ensure_started 定义/前向声明/调用与 esp_sntp.h include，并且不再 setenv TZ、不再 tzset（进程默认 UTC 时 localtime 即等于存入的本地时间）；time(NULL) 只留给时钟显示。CMakeLists 注释与文件头线程模型段同步更正，io_pc 无需改（宿主机时钟本就是本地时间）。

## 证据（数字 / 命令输出）

生效配置自证：build/config/sdkconfig.h 与源码 grep 只剩解释性注释；用户原话作为定案依据记入 PR-0131。

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md 时间源约定；P-0097 息屏改单调时钟互为表里
