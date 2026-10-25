# P-0211 · EEZ CLI 的工程参数必须紧邻；字体烘焙不能直写 `src/ui`

- **工程**：watch2
- **日期**：2026-10-25
- **工具**：Codex
- **状态**：fixed
- **标签**：EEZ,CLI,字体烘焙,生成物,目录边界,PC仿真
- **关联提示词**：PR-0385

## 现象（看到什么）

执行 EEZ CLI 时日志出现 `Build project: --no-sandbox`，随后报找不到
`<工程根>/--no-sandbox`；修正后 CLI 已导出 12 个 UI 文件，但字体补烘焙后
`src/ui/screens.c`、`images.c` 等又全部消失。把字体文件放到根目录后，PC 仿真链接报
11 组 `multiple definition of ui_font_cn*`。

## 复现（怎么稳定复现）

1. 以 `EEZ Studio.exe --build-project --no-sandbox <工程>` 调用 CLI；
2. 调用 `eez_font_bake.bake(project, "src/ui")`；
3. CMake 用 `GLOB_RECURSE src/ui/*.c` 编译仿真。

## 根因（真正的原因）

1. `--build-project` 只消费**紧随其后的一个参数**作为工程文件，Electron 运行开关必须放在它之前；
2. 通用 `eez_font_bake.bake()` 的约定是先 `rmtree(out_dir)` 再输出字体，直接传 `src/ui`
   会清空整棵 EEZ 生成目录；字体若误留在 `src/ui/` 根又会与标准
   `src/ui/fonts/ui_font_*.c` 被 CMake 同时收集。

## 修复（做了什么）

工程侧固定顺序：

```text
EEZ Studio.exe [Electron 开关…] --build-project <工程文件>
```

字体先烘到 `build/font_bake/`，验证 `manifest.json` 和字体数量后，只替换
`src/ui/fonts/`；清理范围严格限定为历史误产出的 `src/ui/ui_font_*.c`，不删除
`screens.c`、`images.c` 等其他生成物。

## 证据（数字 / 命令输出）

EEZ CLI 打印 12 个 `File "…" built` 和 `Build successfully finished`；官方字体引擎产出
11 个 `ui_font_cn*.c`；PC 仿真重新链接成功，导航/快捷页回归 `80 PASS / 0 FAIL`。

## 沉淀（新增断言 / 案例 / 文档）

**通用字体烘焙工具的输出目录必须是专用暂存目录，不能是多类生成物共存的 `src/ui`。**
所有工程侧字体胶水都应把“暂存→数量核验→仅替换字体子目录”写成固定步骤。
