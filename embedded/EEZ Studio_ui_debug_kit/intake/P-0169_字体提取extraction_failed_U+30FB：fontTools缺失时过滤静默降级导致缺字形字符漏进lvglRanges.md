# P-0169 · 字体提取 extraction failed（U+30FB）：fontTools 缺失 → 过滤静默降级 → 缺字形字符漏进 lvglRanges

- 状态：fixed（根治：缺 fontTools 改为硬失败，不再静默降级）
- 日期：2026-10-21
- 标签：字体,lv_font_conv,cmap,fontTools,extraction_failed,U+30FB,GB2312,静默降级,硬失败

## 现象
EEZ Studio（GUI）打开工程点 Build / 字体提取时报：
`Font "cn14" extraction failed: Font doesn't have any characters included in range 0x30fb-0x30fb`。
报错那个字符（0x30FB = 日文间隔号 `・`，UNICODE 名 KATAKANA MIDDLE DOT）在 SimHei 里**根本没有**字形。

## 复现条件（关键：为什么"总是出现"）
工程字体走「GB2312 全量字符集」：`build_example.py` 的 `gb2312_charset()` 用 GB2312 编解码器把
0xA1A1–0xF7FE 全部映射成 Unicode——其中符号区含 U+30FB。字符集本应由 `_filter_by_font_cmap()`
按 SimHei 的 cmap 过滤掉字体没有的字，**但该函数 catch 了 `ImportError` 后只是 WARN 并原样返回**。
于是只要运行环境没装 fontTools，U+30FB 就原封不动写进 eez-project 的 `lvglRanges`，EEZ GUI 一提取
就报 extraction failed。**每次换环境/重装/新机器只要没装 fontTools 就再犯——这就是"总是出现"的根因。**

## 根因
1. 字符集来源含字体没有的字（GB2312 符号区 U+30FB）；
2. 过滤逻辑把"无 fontTools"当可降级错误，静默放行未过滤字符集；
3. EEZ 字体提取对 lvglRanges 里任何一个缺字形字符都会硬失败（非警告）。

## 修复
**两处，缺一不可：**
1. 安装 fontTools：`python -m pip install fontTools`（本机已装进托管 3.13.12 venv）；
2. 把 `_filter_by_font_cmap()` 的 `except ImportError` 分支从「WARN+返回原串」改为**`sys.exit(2)` 硬失败 + 明确提示安装命令**——缺工具直接终止，绝不把脏字符集写进工程。

过滤生效后日志会打印 `font coverage: dropped 1 chars not in TTF: ・`，eez-project 里不再出现 12539(0x30FB)。
随后按纪律重生成：`build_example.py` → `cli_build.py` → `gen_font.py` → `run_sim.bat build`。

## 验证
- `grep -c 12539 app-wifi-connect2.eez-project` → 0（已清除）；
- 重编 12/12 通过；无头运行 `[UI] list rebuilt: 12 rows from io` 正常；GUI 提取不再报错。

## 顺带发现（同族未修）
U+00B7（·，middle dot）SimHei 也没有，同样被过滤掉。native 代码若仍用 `·` 当副行分隔符，界面会
继续是方框（豆腐）——显示问题，不是提取问题。根治：分隔符改用 `/` 或补字形到 font entry。

## 检测法（防再犯）
- 静态：`grep -c 12539 app-wifi-connect2.eez-project`（或任何非 BMP/字体拥有的码点）；
- 构建：`build_example.py` 跑完看是否打印 `dropped ...`；无 fontTools 现在直接 FATAL 退出。

## 沉淀
- 凡是"字体没装→过滤跳过→脏数据进产物"的防御，**绝不该静默降级**，必须硬失败让构建红掉。
- GB2312 全量字符集 ≠ 字体实际覆盖：生成前必须按目标 TTF cmap 过滤，且工具缺失即阻断。
