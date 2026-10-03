# P-0090 · 真机构建失败：`GetBoard` was not declared —— 顺带把"真机改动"的验证姿势升级为真编译

- **工程**：小艺·智能屏 8（eez-test）/ 真机 ESP32-P4（xiaozhi-esp32 板级桥接 + src/native）
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：GetBoard,Board::GetInstance,引用不可判空,真编译验改动,只替换-o,multiple files,-DBOARD_TYPE
- **关联提示词**：（未对应，该轮提示词未进 PROMPT_LOG）

> 补档说明（2026-10-03）：正文按 `index.md` 的 P-0090 行 +
> 工程日志 `.workbuddy/memory/2026-10-02.md`「第 107 轮（22:45）修真机构建失败：GetBoard 未声明
> （P-0088 板级桥接）」回填。★ 日志该轮标题里的编号是**工程侧自己的 P-0088**，
> 与本库 `P-0088`（左栏切 tab 页）**同号两义**（这类撞车见 PR-0135 的自查记录），
> 本库按 index 行把它登记为 P-0090。

## 现象（看到什么）

用户 `idf.py build` 直接失败：

```
board_p4_audio.cc:119: 'GetBoard' was not declared in this scope; did you mean 'Board'?
```

出错的那行是**上一轮（第 104 轮「UI 控件接硬件第一批」）加的音量桥接函数**里写的。
PC 仿真侧当时是全绿的（第 104 轮验证记录：`all.py --sim` PASS、设备侧 4 文件 0 错 0 警），
但 `board_p4_audio.cc` **不在这些门禁的编译范围里**，只有真机 `idf.py build` 才爆。

## 复现（怎么稳定重现）

真机 `idf.py build`。★ **PC 仿真永远复现不了**：仿真不编译 xiaozhi 那棵树
（`managed_components` / `xiaozhi-esp32/main/...`），也完全不碰 `board_p4_audio.cc`
—— 与 P-0045 / P-0050 记的"设备侧盲区"同族。

## 根因（真正的原因）

**本工程根本没有 `GetBoard()` 这个函数**（那是别的项目的写法，凭印象抄过来的）：

- 板级单例是 **`Board::GetInstance()`**（`board.h:62`），返回的是**引用**，内部 static 懒建
  `create_board()`；
- 本板类是 `P4AudioBoard : public WifiBoard`，codec 取法是
  `Board::GetInstance().GetAudioCodec()`；
- 而且原先还写了 `if (!b)` 判空 —— **引用不能判空**，这个写法本身也不成立。

为什么以前没发现：桥接代码写在 `board_p4_audio.cc`（真机专属翻译单元），
PC 侧门禁照不到；写的时候没先 grep 确认符号真身。

## 修复（做了什么）

1. `main/board_p4_audio.cc` 的桥接函数改成：
   ```cpp
   AudioCodec* codec = Board::GetInstance().GetAudioCodec();
   if (codec) { ... }
   ```
2. ★★ **真机改动的验证姿势升级（P-0050 的补强）**：不再用 `-fsyntax-only`（它不跑优化器，
   抓不到 `-Werror` 类问题，见 P-0052），改**真编译**：
   - 取 `build/compile_commands.json` 里该文件的**原命令**；
   - **只把 `-o` 后面那个产物路径**换成临时 `.obj`；
   - 其余参数与源文件**一律照抄**。

## 证据（数字 / 命令输出）

- 真编译实测覆盖：`board_p4_audio.cc` + `src/native/{io_esp,app_model,native_actions,native_vars}.cpp`
  → **全 exit 0、零警告**。
- `xiaozhi` 组件里的 `wifi_board.cc` 需手工补 **`-DBOARD_TYPE` / `-DBOARD_NAME`**
  （这两个宏在它自己的 cxxflags 里，compile_commands 条目的 response 文件是空的）→ 补后也 exit 0。
- 两个"自伤写法"的实测报错（照抄原命令的原因）：自己再补 `-c` + 源文件、
  或剥掉 `-c` 却留着源文件，都会报
  `cannot specify '-o' with '-c' … with multiple files`。

## 沉淀（新增断言 / 案例 / 文档）

- ★ **写板级 / 组件桥接前必须先 `grep` 确认符号真身**：单例通常是 `GetInstance()` 返回**引用**，
  不是 `GetBoard()` 返回指针；引用不能判空。
- ★ **PC 仿真编译永远照不到 xiaozhi 那棵树** —— 只有这套"照抄 compile_commands 只换 -o"的
  真编译能在烧录前拦住设备侧错误。MEMORY.md「设备侧文件是 PC 构建盲区」条目据此把自检手段
  写成"真 `-O2 -c` 编译；`-fsyntax-only` 不跑优化器 = 假绿"。
- 同型教训串：P-0045（注释吞码）→ P-0050（重复定义）→ P-0052（`-fsyntax-only` 局限）→
  **P-0090（本条，命令照抄法）**→ P-0092（真机先取证再改码）。
- 可加断言（本次未加）：`_device_syntax_check.py` 扩到能吃 xiaozhi 组件的翻译单元
  （需自动补 `-DBOARD_TYPE/-DBOARD_NAME`）。
