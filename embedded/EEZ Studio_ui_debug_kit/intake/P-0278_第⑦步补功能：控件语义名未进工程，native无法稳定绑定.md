# P-0278 · 第⑦步补功能：控件语义名未进工程，native 无法稳定绑定

- **工程**：多参数监护仪 UI（multipara_monitor_ui）
- **日期**：2026-11-08
- **工具**：Trae
- **状态**：fixed
- **标签**：第⑦步,功能补齐,控件绑定,identifier,数据模型
- **关联提示词**：PR-0628

## 现象（看到什么）

EEZ 生成的控件句柄全是自动序号（`main_w01`、`main_st02`、`main_hr55`），
设计里的语义名（“心率读数”“血氧读数”）在工程和代码里都不存在。
native 想刷读数时，只能靠猜序号或硬编码下标，设计源一改就错位。

## 复现（怎么稳定重现）

`design_source.json` 的控件只有 `type/text/x/y/...`，没有 `name`；
生成器的 `identifier` 规则是 `<page>_<code><idx:02d>`。任何按语义绑定的代码
都没有稳定锚点。

## 根因（真正的原因）

export 阶段把控件行的 `name` 丢了；生成器只保证「模板字段集正确」，
不保证「语义可在运行期找到」。

## 修复（做了什么）

- `export_design_source.py`：所有控件 spec 增加 `name`（来源 `pages.py` 的行名）。
- 新增 `design/gen_ui_ids.py`：按生成器同一 identifier 规则派生
  `src/native/app/ui_ids.h`——42 个 read 控件的 `key → objects.<ident>` 表
  （`key` 为 ASCII 语义键，如 `main.hr`、`main.spo2`；未列出的按 `<page>.r<idx>` 兜底）。
- 新增 `src/native/app/value_model.{h,c}`：仿真生理参数（正弦 + 抖动）。
- 新增 `src/native/app/ui_bind.{h,c}`：唯一 `fmt_read(key, vitals, buf)` 统一格式化，
  只在文本变化时 `lv_label_set_text`，避免整屏重绘。
- `main.c`：运行时 `value_model_tick(10) + ui_bind_tick()`；`MON_AUTOTEST` 不启动绑定，
  保持 B2 截图基线；`MON_SMOKE=1` 做无头冒烟。

## 证据（数字 / 命令输出）

- `MON_SMOKE=1`：300×10ms 内读数刷新 **36 次**，输出 HR/SpO2/RR/TEMP/NIBP 合理变动。
- `MON_AUTOTEST=1` 回归：导航 **43/43 PASS**，B2 基线未变（绑定未启动）。
- 构建：`run_sim.bat build` 成功，native 层零警告。

## 沉淀（新增断言 / 案例 / 文档）

- 规则：**设计源的控件名必须落到工程**，运行期绑定只认派生表，不认序号。
- 第⑦步最小链路：`name → gen_ui_ids.py → ui_ids.h → 单一 fmt_read() → Label`。
- 坑：`objects.*` 是运行期变量，不能用于静态初始化，派生表要生成 `ui_reads_init()`。
