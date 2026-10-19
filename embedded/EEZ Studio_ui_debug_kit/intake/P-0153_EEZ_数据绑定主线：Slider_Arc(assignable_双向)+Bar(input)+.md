# P-0153 · EEZ 数据绑定主线：Slider/Arc(assignable 双向)+Bar(input)+Label 表达式，一个 flow 全局变量驱动全屏；native 变量需自实现桥

- **工程**：EEz_stidio_examples/slider-arc-bar
- **日期**：2026-10-19
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：Slider,Arc,Bar,flow全局变量,assignable,input,数据绑定,native变量,set_var桥,表达式拼接,PC_SIM
- **关联提示词**：PR-0259

## 现象（看到什么）

想做'调节与指示'：拖 Slider/Arc 时 Bar/数值标签实时跟随；不确定 EEZ 里 Slider/Bar/Arc 的 value 能否绑定、绑定方向、以及数值文本怎么拼

## 复现（怎么稳定重现）

EEZ v3 + flowSupport：flow 全局变量 g_val(integer, 默认25)；Slider/Arc 的 value=valueType expression+表达式 g_val（assignable）；Bar 的 value 同式（input）；Label text=textType expression+表达式 "Value: " + g_val；Bar enableAnimation=true

## 根因（真正的原因）

三个控件的 value 语义不同（asar 挖证）：Slider/Arc 是 assignable（VALUE_CHANGED 回写表达式变量 + tick 反向同步，双向）；Bar 是 input（单向只跟随）；Label 的 text 支持 expression，EEZ flow 的 + 对 string+int 自动转串拼接（安装包无 IntToStr 函数）。全局变量 native:true 时 EEZ 生成对 set_var_xxx/get_var_xxx 的调用，桥函数必须用户自实现，否则链接 undefined reference（P-0083 native_vars 桥的入口）

## 修复（做了什么）

纯 EEZ 演示用 native:false（flow 引擎内部管理，零 C）；要接传感器/wifi 等运行时数据时才 native:true 并在 C 里实现 set_var_g_val/get_var_g_val。产出 slider-arc-bar 示例：拖 Slider 或 Arc，Bar 平滑跟随（LV_ANIM_ON）、Label 实时变

## 证据（数字 / 命令输出）

screens.c 产物对账：VALUE_CHANGED 里 lv_slider_get_value→写回 g_val；tick 里 slider/bar/arc 三方 set_value 同步（bar 带 LV_ANIM_ON）；native:true 时链接报 undefined reference to set_var_g_val，改 false 后 PC_SIM 7/7 链接 0 错；CLI 表达式 0 错 0 警

## 沉淀（新增断言 / 案例 / 文档）

slider-arc-bar/README.md、根 README 索引第 10 行、workspace memory 2026-10-19

## 补充（同日）：手册章节号命名规范 + W 号总表

- 用户要求示例目录名带手册章节号（如 W1）。编号出处 = KB 内
  EEZ-Studio-reference-guide.pdf（784 页，W1..W87，与 asar 控件文档字母序一致），
  用 pypdf 提取标题正则 `W(\d+)\.\s*(\w+)` 全表可复现。
- 本例更名：slider-arc-bar → **w67-w3-w2-slider-arc-bar**（W67 Slider(LVGL) /
  W3 Bar / W2 Arc；同名词多变体时以 (LVGL) 后缀为准，如 Slider W65=Dashboard、
  W66=EEZ-GUI、W67=LVGL）。改名要点：目录、.eez-project 文件名、
  build_example.py 的 PROJECT_FILE、cli_build.py 的 PROJ、README、根索引同步改；
  build_rel 缓存含旧路径须删除全量重配。
- 已提取完整 W 号表存 workspace memory（W34 Label、W47 Meter、W70/W71 Spinner、
  W78 Tabview、W40-42 List×3、W72-74 Switch×3 等）。
