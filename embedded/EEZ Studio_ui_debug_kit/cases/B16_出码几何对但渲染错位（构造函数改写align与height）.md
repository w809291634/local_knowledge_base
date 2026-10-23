# B16 出码几何全对、渲染却整块错位（控件构造函数改写 align / height）

## 现象

480×320 的 Wi-Fi 连接半页（sheet），EEZ 出码里 `lv_obj_set_pos(kb_main, 8, 92)` +
`lv_obj_set_size(kb_main, 464, 132)` 与设计源逐字节相同，静态几何对账（[④A]）全绿，
但仿真截图里：

- 键盘**只剩一行**贴在屏幕底边，半页中间一大片空白；
- 同一屏的 one-line 密码框设计高 36px，渲染出来只有 **17px**（一根细胶囊）；
- 「连 接」按钮看不见（底色与半页底色同值，属另一类问题，见"通用化"）。

## 证据

运行时探针（本工程 `design/sim_cmake/main.c` 里 `WIFI_KBPROBE=1` 分支，打印
`lv_obj_get_coords` 的**绝对屏幕坐标**）：

| 对象 | 设计应有 | 修复前实测 | 修复后实测 |
|---|---|---|---|
| `kb_main` | abs (8,188)-(471,319) | abs **(16,280)-(479,411)**（低 92px，91px 出屏） | abs (8,188)-(471,319) ✓ |
| `kb_main` align | TOP_LEFT | **BOTTOM_MID** | TOP_LEFT |
| `pwd_ta` 高 | 36 | **17** | 35 |

`kb` 的实测位置正好等于 `设计位置 + 自身 pos`（8+8, 96+92+92）——这是"pos 被当成锚点偏移"的指纹。

## 曾经的误判

第一轮把现象解释成 **"132px 装不下 4 行，LVGL 默认一行键约 50px"**，还做了"加高到 168 变 2 行"的
对照实验，据此提出两个方案（压键帽 / 加高半页）让用户二选一。

推翻它的是探针：键盘真实高 132、行高实测 30 + 间距 4，**4 行完全装得下**，问题是整块下移 92px。
"加高到 168 变 2 行"其实是把出屏的部分挪回来了一点，被误读成"行数与高度成正比"。

→ 教训：**先量渲染坐标，再谈布局预算**。没有探针之前，所有关于"装不下"的推断都是猜。

## 真因

两条都是 LVGL 控件构造函数在运行时改写了声明式几何：

1. `lv_keyboard_constructor()` 末尾写死
   [`lv_obj_align(obj, LV_ALIGN_BOTTOM_MID, 0, 0)`](../../../../apl_lvgl_v9_4/src/widgets/keyboard/lv_keyboard.c)
   （LVGL 9.4 `lv_keyboard.c:452`）。LVGL 中 `lv_obj_set_pos` 的语义是
   **"相对 align 锚点的偏移"**，锚点不是 TOP_LEFT 时，(8,92) 就不是左上角坐标。
2. `lv_textarea_set_one_line(true)` 内部执行
   `lv_obj_set_height(obj, LV_SIZE_CONTENT)`（`lv_textarea.c:557`），
   以局部样式形式覆盖了 EEZ 显式写下的 36px。

## 修法

都在**设计源**（`build_example.py`）里改，不改 `src/ui`：

```python
# 键盘：显式把锚点改回左上角，set_pos 才是"左上角坐标"
local={"MAIN": {"DEFAULT": {"align": "TOP_LEFT", ...}}}

# one-line 输入框：高度只能靠上下 pad 撑
# ★ 行高要实测（cn14 = 19），不要拿字号 14 当行高
TA_LINE_H = 19
SHEET_TA_PAD = (SHEET_TA[3] - TA_LINE_H) // 2
local={"MAIN": {"DEFAULT": dict(ZERO_PAD, pad_top=SHEET_TA_PAD,
                                pad_bottom=SHEET_TA_PAD, ...)}}
```

这是根治而不是打补丁：把"声明几何"与"渲染几何"之间的换算交回给框架自己
（TOP_LEFT 锚点 = 声明即渲染），而不是在 native 里按实测差值反向平移。

## 验证

- `design/preflight.py` [④A] 第 ④ 组两条守卫：`kb_main` 必须出现
  `lv_obj_set_style_align(obj, LV_ALIGN_TOP_LEFT`；`pwd_ta` 必须出现
  `lv_obj_set_style_pad_top(obj, <SHEET_TA_PAD>,`。
- 反向测试（`tmp/_negtest_gate.py`）：分别删掉这两行出码 → `preflight rc=1` 且 FAIL 行点名；
  复原 → `rc=0`。守卫不是假门禁。
- 探针复测：`kb abs=(8,188)-(471,319)`、`pwd_ta h=35`。
- `build/sim_shots/sheet_open.png`：4 行键帽齐全、输入框成胶囊、蓝色主按钮可见。

## 通用化

- **同一类机制**：CSS 的 `position` 决定 `top/left` 是否有意义；Android 的 `LayoutParams`
  会覆盖子 View 的自设尺寸；任何"组件构造函数/挂载钩子改写声明式属性"的框架都会出现
  "生成码正确、渲染错位"。判据一样：**静态读生成码不足以证明几何，必须量渲染坐标**。
- 需要排查的其他 LVGL 控件（构造函数里带 `lv_obj_align` 的）：`lv_msgbox`、`lv_win`、
  `lv_menu`、`lv_tabview` 的子页等；带 `LV_SIZE_CONTENT` 强制的还有 `lv_label` 长文本模式。
- 关联：[B3 默认主题 padding 偏移](B3_默认主题padding偏移.md)（同一族：主题/构造函数改写几何）、
  [B6 样式值写错语法被静默吞掉](B6_样式值写错语法被静默吞掉.md)
  （本案顺带证实：EEZ 的 `localStyles` 只出 `LV_PART_MAIN`，写 `"ITEMS"` 部件样式会被**静默丢弃**，
  键帽底色改不动，只能让设计图去对齐 `DARK_COLOR_CARD 0x282b30`）。
- 另一条同屏暴露的通则：**按钮底色不得与它所在面板同色**（`ELEVATED == SHEET_BG` 让按钮隐形），
  设计图与出码的配色令牌要成组对账，不能只对几何。
