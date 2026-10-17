# P-0140 · EEZ CLI 构建每次把字体 .c 当孤儿删除；只有 GUI Build 才产出字体文件

- **工程**：watch (Design Watch)
- **日期**：2026-10-17
- **工具**：Qoder
- **状态**：fixed
- **标签**：eez,cli,codegen,字体,孤儿清理,ui_font,构建差异
- **关联提示词**：PR-0235

## 现象（看到什么）

用户报告：`watch/src/ui/ui_font_cn26.c` 在"AI 生成之后被删除，EEZ（GUI）output 时又生成"。
受控复现：每次 `--build-project` CLI 构建后 src/ui/ui_font_cn*.c **全灭**（日志有
Deleted orphaned file 行）；GUI 里点一次 Build（工具栏扳手）→ 7 个字体 .c 全部重新出现。

## 根因（真正的原因）

CLI 与 GUI 的 codegen 产物清单不同：**CLI 不跑字体提取**（lvgl-worker 提取只在 GUI 会话内做，
产物只写 fonts.h 声明）；而 EEZ 的产物管理按"本次构建写了哪些文件"清理孤儿——
字体 .c 不在 CLI 清单里 → 每次 CLI 构建都被当孤儿删掉。GUI Build 的清单含字体 .c → 重建。
（旧 src/ui/fonts/ 子目录+manifest.json 是 10-16 烘字体时代的重复产物，现行布局
字体 .c 直接在 src/ui/ 根，无 manifest。）

## 修复（做了什么）

`design/eez_build.py` 升级为自愈链：CLI 构建 → 校验 `src/ui/ui_font_<name>.c`
按工程 fonts 表全在 → 不齐自动起 GUI（P-0133 配方+调试口）→ 真实鼠标事件点工具栏
Build（React 对 el.click() 合成事件不敏感，必须 Input.dispatchMouseEvent）→
轮询 fonts_ready（≤300s）→ taskkill；仍不齐则 rc=1 FONT-EXTRACT-INCOMPLETE，
**绝不带缺口静默放行**。端到端实测：CLI 删 → 自动 GUI 补 → rc=0 七字体齐。

## 证据（数字 / 命令输出）

/tmp/ebB.log（修复前）：CLI ok 但 fonts 0/7 → 报 INCOMPLETE；
/tmp/ebC.log（修复后）：`GUI Build click @303,61` → `fonts 已由 GUI 会话补齐` → rc=0，ls=7。

## 沉淀（新增断言 / 案例 / 文档）

eez_build.py 头注（机制全文）；报告 §34；AGENTS.md 链路③ 备注；
断言：**凡走 CLI 构建，字体 .c 必被删——MCU 编译前必须确认 eez_build rc=0（含 GUI 补字体段）**。
