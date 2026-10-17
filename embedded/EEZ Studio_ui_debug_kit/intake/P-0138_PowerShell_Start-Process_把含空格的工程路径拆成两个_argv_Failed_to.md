# P-0138 · PowerShell Start-Process 把含空格的工程路径拆成两个 argv → "Failed to load file!" 假象（症状酷似会话损坏）

- **工程**：watch (Design Watch)
- **日期**：2026-10-17
- **工具**：Qoder
- **状态**：fixed
- **标签**：cdp,eez-studio,启动参数,powershell,argv,空格路径,failed-to-load-file
- **关联提示词**：PR-0231

## 现象（看到什么）

`powershell Start-Process -FilePath "EEZ Studio.exe" -ArgumentList '开关…','C:\Users\…\Design Watch\watch\watch.eez-project'`
→ 窗口标题正常 `watch - EEZ Studio`，但页内显示 **"Failed to load file!"**；
清 Local/Session Storage、删 ui-state 均无效（曾被误判为 P-012x 家族的会话损坏）。

## 复现（怎么稳定重现）

控制台日志实锤：`loadProject Watch/watch/watch.eez-project` →
`ENOENT: C:\Users\yjt54\sim_watch\Watch\watch\watch.eez-project`——
PowerShell 把 `"…\Design Watch\watch\watch.eez-project"` 在空格处拆成
`…\Design` + `Watch\watch\watch.eez-project` 两个 argv，EEZ 取 argv[last]（P-0133 机制）
拿到的是**被截断的相对路径**，按 CWD 解析必然 ENOENT。工程 JSON 本体完好（校验通过）。

## 根因（真正的原因）

Electron 主进程 argv 解析（P-0133）+ PowerShell -ArgumentList 对含空格元素的再分词。
两个已知坑叠加产生新症状：单看"Failed to load file!"会先怀疑工程/会话，绕远路。

## 修复（做了什么）

带空格路径的 EEZ 启动一律 **bash 直启 + 双引号**（PLAYBOOK §3.2 原配方）：
`"/c/Users/…/EEZ Studio.exe" <开关…> "C:\Users\…\Design Watch\watch\watch.eez-project" &`
（nohup 脱离会话）。PLAYBOOK §3.2 已补禁条款。

## 证据（数字 / 命令输出）

同一工程 bash 直启 → 编辑器完整加载（工具栏/页面树/flow 组件全在）；
PowerShell 启动 → 同机同秒必现 ENOENT。watch_console.js 抓到的 loadProject 行是判据。

## 沉淀（新增断言 / 案例 / 文档）

PLAYBOOK §3.2 警示块；skills §11.39；诊断顺序断言：**"Failed to load file!" 先查 argv
（console 里 loadProject 打的路径是不是被截断），再怀疑会话/工程**。
