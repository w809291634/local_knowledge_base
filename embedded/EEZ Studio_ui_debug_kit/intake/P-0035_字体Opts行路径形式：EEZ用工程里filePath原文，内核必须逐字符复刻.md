# P-0035 字体 Opts 行路径形式：EEZ 用工程里 filePath 原文，内核必须逐字符复刻

- **状态**：fixed
- **发现日期**：2026-09-30
- **提示词**：PR-0061
- **标签**：字体烘焙, Opts, filePath, 相对路径, KERNEL_HASH, bake.js缓存, 黄金样本

---

## 一、现象（用户原话：EEZ 生成的应该是 `--font design\fonts\...`，而你们生产的都是绝对路径）

对比 GUI（Check and Build）产物与后台引擎产物：`ui_font_*.c` 头注释
`* Opts:` 行里 `--font` 的路径形式不一致 —— GUI 是**相对工程根**
（`design\fonts\YaHei_Consolas_Hybrid.ttf`），后台引擎产物出现
**绝对路径**（`D:\...\design\fonts\...`）。

## 二、取证（asar 反编译，不是猜）

EEZ `build/project-editor/features/font/font.js` 的 `_lvglExtractFontParams`：

```js
l += `--bpp ${this.bpp} --size ${this.source.size} --no-compress --font ${this.source.filePath}`;
...
l += ` --font ${e.filePath}`;   // 附加源同
```

**opts_string 用工程 JSON 里 filePath 的原文，无任何相对化**；
worker 把 opts_string 原样传给 lv_font_conv 写头注释。
所以：**Opts 行的路径形式 = 工程里存的形式**。GUI 产物是相对 →
GUI 保存的工程里就是相对路径。内核曾把 `--font ${abs}`（path.resolve 成绝对）
——只要工程里存绝对路径就必然和 GUI 不一致。

## 三、修复（三层）

1. **上游（正解）** `design/json2eez.py`：主字体 + FontAwesome 附加源的
   `filePath` 一律写**相对工程根**（`os.path.relpath(..., PROJECT_DIR)`，
   Windows 下自然产 `design\fonts\...` 反斜杠形式，与 GUI 保存行为一致）。
2. **内核** `tools/eez_font_bake.py`（BAKE_JS）：读文件以**工程目录**为基准
   （`path.resolve(projDir, filePath)`，等价 EEZ `getAbsoluteFilePath`，
   不依赖 cwd）；opts_string 改用 filePath **原文**（`${font.source.filePath}` /
   `${e.filePath}`）—— 逐字符复刻 EEZ。
3. **胶水缓存缺陷（连带揪出）** `design/eez_font_engine.py::ensure_engine`：
   引擎缓存命中（`.engine_ok` 存在）时**不重写 bake.js** —— 内核驱动代码更新后
   缓存里还在跑旧版（症状：相对路径被拼到引擎缓存目录、烘焙失败）。
   修复：命中后比对 bake.js 内容，与要写入的 js 不一致就重写。

## 四、证据

- 11 个产物 Opts 行 `--font` 全部相对，`grep -l "D:\\esp32" src/ui/ui_font_*.c` = **0**。
- `all.py --shots` EXIT=0：11 屏平均 8.62% 无缺屏、6 条 swipe 断言全过、
  verify_center 58/58。
- KERNEL_HASH 更新 `242c651b…` → `7c210f0d…`（BAKE_JS 逐字同步内核与工程副本）。
- 连带发现：同步前「工程内置副本 vs 内核」本就不一致（指纹自锁本应拦住）——已归位。

## 五、沉淀

- `skills.md §11.12`「必踩准的点」从 7 条扩到 **8 条**：第 8 条 =
  「opts_string 用工程 filePath 原文 + 工程必须存相对路径 + 读文件以工程目录为基准」。
- `ensure_engine` 的 bake.js 内容校验（缓存只该缓存引擎，不该缓存驱动）。
- 方法论：**「逐字节一致」的背书必须覆盖注释行** —— 数据对了、注释路径形式不对，
  黄金样本比对照样 FAIL。

## 六、终验（2026-09-30 深夜闭环）

- 用户在 GUI 里跑 Check and Build（src/ui 21:51 被 GUI 重写 = 黄金样本），
  留底后后台引擎 `--force` 重烘，`cmp` 逐字节比对：**11/11 一致、0 不一致**
  —— 「与 GUI Build 逐字节一致」的背书现在覆盖到 Opts 注释行。
- 工程相对路径与 EEZ GUI 双向兼容（GUI 打开/保存均保持 `design\fonts\...`）。
- freetype wasm 偶发段错误（node 子进程 SIGSEGV，重跑即过）—— 已在本轮实测
  一次，与改动无关，但内核可考虑加「崩了自动重试一次」。
