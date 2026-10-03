# P-0087 · 开机自己弹出 Xiaozhi-xxxx 配网热点：三条路径汇到一个总闸

> 本条是**回填**（2026-10-03 由 Qoder 按 INTAKE 方式 B 补建）。素材 = 工程日志
> `.workbuddy/memory/2026-10-02.md` 第 103 轮（20:59）原文；当时 index 无行、intake 无正文。
> 改动仍在树里（`git log` 见 commit `bb3555c`），本条记录的是**为什么这么做**和边界。

- **工程**：eez-test / lvgl_demo_ai（`xiaozhi-esp32/main/boards/common/wifi_board.cc`）
- **日期**：2026-10-02（回填 2026-10-03）
- **工具**：WorkBuddy（原轮次）/ Qoder（回填）
- **状态**：fixed
- **标签**：配网,AP热点,StartWifiConfigMode,TryWifiConnect,总闸,自家UI配网,回填
- **关联提示词**：无（第 102/103 轮的提示词当时未逐字补录，PR-0112 之后直接跳到 PR-0113）

## 现象（看到什么）

真机日志：开机 → `State: starting -> wifi_configuring`，同时设备开出热点
`Xiaozhi-2645`，并起 DNS + Web server，提示「手机连接热点…」。
本产品用的是自家 LVGL UI 配网（设置-网络面板：扫描 → 点网 → 输密码 → 连接，长按=忘记），
这个热点是多余的第二套配网入口。

## 复现（怎么稳定重现）

清掉已保存网络（或首次开机）后上电即可。三条进入路径都会命中：
① 无保存网络开机 ② 连不上超时 ③ 按 BOOT 键。

## 根因（真正的原因）

`xiaozhi-esp32/main/boards/common/wifi_board.cc` 的 `WifiBoard::TryWifiConnect()`（:98）：
`SsidManager` 列表为空（无保存网络）→ `else { vTaskDelay(1500); StartWifiConfigMode(); }`。
另两条路径 `OnWifiConnectTimeout()`（连不上超时）与 `EnterWifiConfigMode()`（BOOT 键，
`main/board_p4_audio.cc:78`）同样汇到 `StartWifiConfigMode()`。**三条路径一个出口** ——
逐个堵会漏，堵出口最省。

## 修复（做了什么）

在 `WifiBoard::StartWifiConfigMode()` **入口**加一行日志 + `return;`（现为 :168 起，
注释标注 P-0087 与三条路径清单）：不开 AP/DNS/Web、不迁移 `wifi_configuring`
（设备停在 `starting`，等我们 UI 触发扫描）、不弹热点提示。**要恢复只删那 3 行。**

★ 合法性依据（以后有人质疑"为什么能动框架源码"就看这条）：
`xiaozhi-esp32/` 是**工程内 vendor 的源码树、git 跟踪**（改动有 commit `bb3555c`），
与 `managed_components/`（`.gitignore:11` 忽略 + 带 `.component_hash`，改了会被重新拉取覆盖）
不是一回事 —— 前者可以改，后者不能改（P-0094 的剪枝方案就是为了不碰后者）。

## 证据（数字 / 命令输出）

当轮用 `build/compile_commands.json` 的真机编译命令做 `-fsyntax-only`，exit 0。
★ 同轮沉淀的 Windows 工具链要点：gcc **不支持 `@"D:/..."` response 文件**（含引号即报
"linker input file not found"），要在脚本里把 `@file` 的**内容展开**成参数数组；
`BOARD_TYPE`/`BOARD_NAME` 宏由 `build/toolchain/cxxflags` 提供（该轮后来被 P-0090 的
「真编译 = 只替换 `-o` 产物路径」方案取代）。

## 沉淀（新增断言 / 案例 / 文档）

- 预期副作用（写清别当 bug）：无网络时设备不再自建热点，语音 / OTA 等联网功能
  **必须先在自家 UI 配过网**；BOOT 键配网一并失效。
- 「三条路径汇一个出口 ⇒ 堵总闸」这个判断式适用于任何框架侧行为抑制，
  比在每个调用点加条件更不容易漏。
