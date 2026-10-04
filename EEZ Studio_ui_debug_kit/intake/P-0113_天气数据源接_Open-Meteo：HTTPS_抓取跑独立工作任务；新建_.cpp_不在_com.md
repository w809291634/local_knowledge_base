# P-0113 · 天气数据源接 Open-Meteo：HTTPS 抓取跑独立工作任务；新建 .cpp 不在 compile_commands，逐文件真编译会把它当成没编译却报通过

- **工程**：eez-test
- **日期**：2026-10-04
- **工具**：Qoder
- **状态**：fixed
- **标签**：天气,Open-Meteo,esp_http_client,esp_crt_bundle,工作任务,P4零阻塞,快照互斥,compile_commands,验证盲区,export.ps1
- **关联提示词**：PR-0173,PR-0174

## 现象（看到什么）

P-0112 把天气卡改成绑变量后，真机四项恒为诚实空态（-- / 暂无天气数据），因为真机侧根本没有数据通路。用户选方案 A（Open-Meteo，免 key）接上。

## 复现（怎么稳定重现）

编译烧录 → 待机页右上卡永远停在空态；串口无任何 http 相关日志；此时用逐文件真编译脚本验证新加的 io_weather.cpp，输出「0 错 0 警」，但那是因为该文件压根没出现在build/compile_commands.json（cmake 没 reconfigure），脚本静默跳过。

## 根因（真正的原因）

两点。①数据源缺失：io_esp 只发空态，没有网络抓取模块。②验证链的坑：新文件要 cmake reconfigure 才会进 compile_commands，而本机 idf.py 的入口脚本 export.ps1 在这台 PowerShell 上直接报 BadExpression（. $idf_exports），拿不到 reconfigure；于是「借 compile_commands 真编译」这套取证法对新文件是失明的 —— 属于 P-0012 那一类：把「没检查」伪装成「通过」。

## 修复（做了什么）

新增 src/native/platform/io_weather.{h,cpp}，只在设备分支编译：①独立 FreeRTOS 工作任务 ui_weather_work（prio 2、栈 8192）里 esp_http_client GET api.open-meteo.com/v1/forecast?...&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code&timezone=Asia%2FShanghai，crt_bundle_attach = esp_crt_bundle_attach（443 是通的，P-0092 只卡 8883，OTA 已验证同路径）；②cJSON 解析 current，WMO weather_code 映射成 kind(0晴/1多云/2雨/3无数据)+cond，词表严格限制在 DSL 的 WEATHER_GLYPHS 内以免豆腐；③结果写进互斥保护的小快照（kind/temp/cond/detail/valid），LVGL 线程侧io_weather_publish() 每拍最多取一次、lv_mutex_take 超时 20ms（有界，不自旋不无限等），memcmp 无变化就不推模型；④15 分钟刷新、失败 60 秒退避、失败保留上一次值（不做闪空态）；⑤io_init 起任务并先发布空态，publish_state_locked 里 io_weather_net(s_wifi_up) 通知网络可用性，io_sample_inputs 里发布；⑥src/native/CMakeLists.txt 设备分支加 platform/io_weather.cpp，REQUIRES 补 esp_http_client esp-tls json mbedtls。

## 证据（数字 / 命令输出）

取证脚本 eez-test/build/_verify_weather.py（本轮留档）：★ compile_commands 在**上级** IDF 构建树 lvgl_demo_ai/build/compile_commands.json，共 2403 条，里面 io_weather 出现 **0 次**（新文件对逐文件真编译完全隐形），io_esp.cpp 有 4 次。借 io_esp.cpp 的真实命令（同 target、127 个 -I）改三处：把 `-o <obj>` 换成 -fsyntax-only、把结尾 `-c <src>` 换成目标文件、补 6 个 -I（esp_http_client/include、esp-tls、tcp_transport/include、mbedtls/mbedtls/include、mbedtls/esp_crt_bundle/include、esp_timer/include）。结果：io_weather.cpp 以及 io_esp / native_vars / app_model / native_actions / app_settings 全部 rc=0、错误 0、警告 0。反向对照：去掉补的 -I，io_weather.cpp 立刻 fatal error: esp_http_client.h: No such file or directory —— 证明这 6 个目录确实必要。★ 途中一个真坑：`bash -c "$CMD"` 会让 gcc 报 no input files（命令里的 \" 被 Python→CreateProcess→MSYS bash 二次转义吃掉，源文件参数变形），改成把命令写进 .sh 再 `bash xx.sh` 就正常。PC 侧不改构建：io_weather.cpp 不在 PC 分支，io_pc 继续发演示值保截图基线。真机验证待用户烧录。

## 沉淀（新增断言 / 案例 / 文档）

通则（本轮新增）：用「借 compile_commands 真编译」取证时，**先把新文件的命令跑通再说 0 错 0 警** —— 新文件通常不在compile_commands 里（cmake 没 reconfigure），脚本文本匹配不到就静默跳过，报的是「没编译」而不是「通过」（P-0012 同一类）。命令必须走 **.sh 文件**执行，不要用 bash -c；反证法（去掉补的 -I 应当报错）能证明 include 不是白加的。另一条：P4 上任何网络抓取都放工作任务，UI 侧只读快照，互斥 take 必须带超时（这里 20ms）且拿不到就跳过这一拍。附带：本机 PowerShell 的 export.ps1 不可用（. $idf_exports BadExpression），reconfigure 只能等用户侧 idf.py build 时自动发生。

## ★ 追加更正（同轮，登记后自查发现）

上面「证据」里写的 `-fsyntax-only` **违反本库 P-0052**：`-fsyntax-only` 不跑 tree 优化器，抓不到
`-Wstringop-truncation` 这类优化期警告（P-0050 就是靠这条翻过车）。改成**真实编译**：保留 `-c` 与原 `-O2`，
只把 `-o <原 obj>` 指到 scratch obj。重跑结果不变且更硬：`io_weather.cpp` 及 `io_esp / native_vars /
app_model / native_actions / app_settings` **6 个文件 rc=0、错误 0、警告 0**；
反证（`VW_NOEXTRA=1` 去掉补的 6 个 `-I`）仍立刻 `fatal error: esp_http_client.h: No such file or directory`。
skills.md §11.22 已按「保留 -c，别换 -fsyntax-only」改写。教训形式上是老规矩踩第二次：**取证手法也要先查库里怎么说的**，
别照着「本轮想到的最简版」写。

## ★★ 追加（同轮，门禁抓到一个真回归 —— 比上面的更正更值钱）

跑 `design/all.py --shots` 时 PC 仿真构建**炸了**：

```
src/native/platform/io_weather.cpp:9:10: fatal error: freertos/FreeRTOS.h: No such file or directory
mingw32-make: *** [CMakeFiles\main.dir\build.make:454: .../io_weather.cpp.obj] Error 1
```

根因：PC 仿真收 `src/native` 的方式是 **`file(GLOB_RECURSE)` + 按名字排除**
（`common/PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt:27-30`，正则是 `(io_esp|test_native)\.(c|cpp)$`）。
新建的 `io_weather.cpp` **不在排除名单里** ⇒ 被仿真构建当成 PC 侧源文件捞走 ⇒ 撞 FreeRTOS/IDF 头。
这和 P-0045 是**同一对盲区的双向**：老坑是「io_esp.cpp 在 PC 根本不编，所以改动潜伏」，
新坑是「**新加的设备专属文件会在 PC 被编，而你以为它不会**」。两边都不安全，别拿任何一边当"必然验不到"。

修法（关键取舍）：**不动那个多工程共用的构建壳**（它还在本工程 git 之外，改了不留痕），
改成让文件自己在两种构建下自证身份 —— ESP-IDF 给每个源文件必带 `-DESP_PLATFORM`（实测借来的命令里就有），
PC 仿真没有 ⇒ 整个文件体包进 `#if defined(ESP_PLATFORM)`，PC 侧编成**空翻译单元**，零外部改动、零 harness 依赖。
`src/native/CMakeLists.txt` 的设备分支照旧（IDF 侧本来就只在那儿列它）。

改后证据：设备侧借命令真编译 6 文件仍 **rc=0 / 错误 0 / 警告 0**；PC 门禁 `all.py --shots` **rc=0**、
9 屏 **平均明显差异 9.90%（阈值 25%）、无缺屏**，逐屏与上一轮（_gate_q）比只差 0.01~0.02 个百分点（均匀漂移，非回归）。
⇒ 通则：**新增源文件后必须跑一次 PC 门禁**，"借 compile_commands 验过"绝不等于"两边构建都通"。
（上面「证据」段那句 *PC 侧不需要改构建：io_weather.cpp 不在 PC 分支* **作废** —— 它恰恰被 PC 的 GLOB 编到了。）

## ★★★ 追加（同轮，用户给了编译入口 ⇒ 上面「本机拿不到 reconfigure」作废）

用户贴出他的 VS Code tasks.json：入口是 `idf_cmd_init.bat && idf_build.bat <reconfigure|build|flash|monitor|size…>`
（cwd = 工程根），并明确「如果你要编译，使用如上方法即可」。`idf_build.bat` 在他那边的 workspaceFolder，
本侧找不到 ⇒ 用 `export.bat` 自建等价包装 `eez-test/build/_idf.bat`，**四个坑一次踩齐**：

1. **`set MSYSTEM=` 必须先清**。从 Git Bash 起 `cmd.exe` 时 MSYSTEM 有值，
   `export.bat` 第 2 行 `if defined MSYSTEM ( echo This .bat file is for Windows CMD.EXE shell only. & goto :eof )`
   ⇒ export 静默不干活，后面 `idf.py` 报「不是内部或外部命令」。
2. **`IDF_PYTHON_ENV_PATH` 要显式指**。不指时它按 PATH 上的 python 猜成 `idf5.5_py3.10_env`，
   而实际装的是 `idf5.5_py3.11_env` ⇒ `ERROR: ESP-IDF Python virtual environment ... not found`。
3. **别给 `idf_cmd_init.bat` 传参**。它 `if /i "%PARAM:~0,7%"=="esp-idf"` 分支会把 `IDF_TOOLS_PATH` 盖成参数值，
   随后 `%IDF_TOOLS_PATH%\idf-env.exe` 变成不存在的路径，报一句天书级的「命令语法不正确（段 `%1\idf-env.exe`）」。
4. **`.bat` 里只写 ASCII**。UTF-8 中文注释在 GBK 代码页下被切碎成垃圾命令执行
   （实测报 `'sks.json' 不是内部或外部命令` —— 是从注释里 `tasks.json` 中间切出来的）。

跑通后的收益（把本条前面的两个「等号」补上了）：
`idf.py reconfigure` **rc=0**，输出里明确 `-- [native] ESP32 hardware backend (io_esp.cpp + io_weather.cpp)`，
`compile_commands.json` 从 2403 条变 **2404 条、io_weather 出现 4 次** ⇒ **新文件不再是验证盲区**，
以后新建源文件只需先 `reconfigure`，不必再「借兄弟文件的命令 + 手补 include」（§11.22 第 1 条的适用前提因此变了：
**能 reconfigure 就先 reconfigure**，借命令只在没有构建入口时用）。
`idf.py build`（链接 + 体积这一层）同时在跑，结果见下一段。

## ★★★★ 追加：`idf.py build` 全绿（真机构建这一层补齐了）

`cmd.exe //C "build\_idf.bat build"` **rc=0**，36 步增量里明确有
`[23/36] Building CXX object .../__idf_native.dir/platform/io_weather.cpp.obj`
⇒ 新文件真的进了 IDF 构建、`esp_http_client/esp-tls/json/mbedtls` 四个 REQUIRES 全部解析成功、链接通过。
产物与余量：`lvgl_demo_v9.bin = 0x4C6870`（≈4.98 MB），最小 app 分区 `0x800000`（8 MB），
**空闲 0x339790 = 40%** ⇒ P-0102 那条「字库把 app 分区吃光」的余量焦虑，在加了 TLS+HTTP 客户端之后仍然不紧张。
整份日志里 `warning:/error:` 只有 3 行，全是 `cc1plus: warning: command-line option` 那种
（C 文件吃 CXX flags 的老噪音），与本轮改动的 6 个文件无关。
⇒ 本轮的三级验证到此齐了：**借命令单文件编（早）→ PC 门禁 9 屏 9.90%（防 GLOB 误编）→ 真机 idf.py build + 分区余量（最终）**。

## ★★★★★ 追加：reconfigure 后改用「官方命令」，反而暴露借命令的一个隐藏失真

留档脚本升级为「有官方条目就用官方条目，没有才借兄弟文件」并挪到跟踪目录：
**`eez-test/design/_verify_weather.py`**（构建入口挪到 **`eez-test/design/_idf_build.bat`**；
放 `build/` 会被 fullclean 带走，`.gitignore:2 build/` 也不收）。

用 io_weather.cpp **自己的官方命令**跑，第一次是 **FAIL**：
```
mbedtls/include/mbedtls/build_info.h:115:10: error: #include expects "FILENAME" or <FILENAME>
esp_crt_bundle/include/esp_crt_bundle.h:70:34: error: 'mbedtls_x509_crt' does not name a type
```
根因不在工程，在**取证脚本**：我把命令里所有 `\` 无差别换成 `/`（为了喂 bash），
连 `-DMBEDTLS_CONFIG_FILE=\"x\"` 也被换成 `/"x"/` ⇒ mbedTLS 的配置头加载失败 ⇒
`MBEDTLS_X509_CRT_PARSE_C` 没定义 ⇒ 报成「类型不存在」，长得像缺 `-I` 其实缺 **define**。
改法：`re.sub(r'\\(?!")', '/', cmd)` —— 路径的反斜杠换，`\"` 转义引号原样留给 bash。
改后 6 个文件用官方命令 **全 rc=0 / 错误 0 / 警告 0**。
⇒ §11.22 第 2 条已补这句；另一条通用教训：**借来的命令连"看不见的 define"也是借的**，
兄弟文件不需要 MBEDTLS_CONFIG_FILE 是因为它不碰 TLS 头 —— 所以能 reconfigure 就别借（第 1 条现在把"能 reconfigure"排在最前）。
