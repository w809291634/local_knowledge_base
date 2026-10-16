# P-0133 · CDP 启动 EEZ Studio 打开工程：工程路径必须放在 argv 最后（主进程取 argv[last] 作为待打开工程）

- **工程**：watch (Design Watch)
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：cdp,eez-studio,启动参数,单实例,argv
- **关联提示词**：PR-0218

## 现象（看到什么）

按 eez_build 风格给 EEZ Studio 传『工程路径 + --remote-debugging-port=9222 …』→ 窗口停在 Home，工程不开；端口一度也不监听（先被单实例导入旧实例/再被杀）

## 复现（怎么稳定重现）

EEZ Studio.exe "<proj>" --remote-debugging-port=9222 --no-sandbox …（工程不在最后）→ Home；把 "<proj>" 放最后 → 直接打开 watch - EEZ Studio

## 根因（真正的原因）

main.js 的 open-command-line-project 处理：无 --build-project 时 openFile(process.argv[process.argv.length-1]) —— 取的是最后一个参数；开关如果排最后就会被当成工程路径打开失败。另：实例已在运行时不加 --build-project 的二次启动会走 second-instance 分支（同样打开 argv 最后一项）

## 修复（做了什么）

启动命令固定：EEZ Studio.exe <全部开关…> "<工程绝对路径>"; 用 nohup … & 脱离会话；旧实例残留时 taskkill 后重启

## 证据（数字 / 命令输出）

同一条命令行换序即从『Home』变为『watch - EEZ Studio』+ 9222 LISTEN；随后 CDP 点击 Dial→AppList、拖拽滚动、canvas-shot 全程可驱动

## 沉淀（新增断言 / 案例 / 文档）

PLAYBOOK §3.2 启动小注（清单加一行）
