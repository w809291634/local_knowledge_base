# P-0033 Screen 直下挂 tab：EEZ GUI 报 Invalid position of Tab widget（headless 不查）

- **状态**：fixed
- **发现日期**：2026-09-30
- **提示词**：PR-0059
- **标签**：EEZ结构校验, tab, tabview, headless, GUI校验, 钉态页, 死代码, 结构不变量

---

## 一、现象（用户贴 EEZ Studio 错误面板原文）

```
Pages / Main / Components / Screen / Children
显示 · 钉态   Invalid position of Tab widget inside Widgets Structure
唤醒 · 钉态   Invalid position of Tab widget inside Widgets Structure
通知 · 钉态   Invalid position of Tab widget inside Widgets Structure
浮层 · 钉态   Invalid position of Tab widget inside Widgets Structure
```

而 `eez_build.py`（headless CLI）从头到尾 **No error and no warning**，
仿真 11 屏出图、对照全绿——运行时行为完全正常。

## 二、复现

EEZ Studio GUI 打开 `test.eez-project` → 错误面板即报。
headless 链路复现不了（这就是问题所在）。

## 三、根因

1. **结构违规**：四张「钉态」隐藏页（当时的设计：给仿真脚本提供干净背景出图）
   是 **Screen 直下的 `tab` 节点**。EEZ 规定 Tab（`LVGLTabWidget`）必须是
   Tabview（`LVGLTabviewWidget`）的**直接子对象**——Screen 直下挂 tab 就是
   「Invalid position of Tab widget inside Widgets Structure」。
2. **为什么一直没暴露**：headless CLI build **不做这层结构校验**。
   「**headless build 过 ≠ 结构合法**」——GUI 的 Widgets Structure 校验更严。
3. **顺手清出的死代码**：`m_shot_*` 在 sim.py / MAIN_C / 冒烟脚本里**零引用**。
   四态状态图最终走 `sim.py --states`（真实页 + io_pc `EEZ_SIM_STATE` 钉态钩子，
   见 §11.18 配方）路线，钉态页是废弃的中间方案，纯死代码——
   ui.json / 生成 C 平白多约两千行。

## 四、修复

`design/build_ui.py`：删除 `_shot_tab()` / `_shot_pop_tab()` 两函数及 `s_home()`
里四个调用点（scr children 只剩 statusbar + main_nav + rail）。
原地留注释：**再要「干净背景截图页」必须包进一个隐藏 tabview（tabSize=0、页填满）
或改普通 container，不能裸挂 Screen。**

## 五、证据

- 自写校验遍历 `test.eez-project` JSON：**13 个 LVGLTabWidget 的 parent 全部是
  LVGLTabviewWidget**（4 个 tabview：main_nav / ai_nav / mus_nav / sett_nav），
  违例 **0**；`shot_` / 「钉态」字符串**零残留**。
- `all.py --shots` EXIT=0，11 屏平均 **8.62%** 与删除前一致（证明删的只是隐藏死页，
  可见 UI 无任何变化）。
- `verify_center.py` **58/58** 居中（此前 65 处，少的 7 处即钉态页里复制的图标）。

## 六、沉淀

- `skills.md §11.20`：DSL 结构不变量（tab 只能活在 tabview 下）+
  headless / GUI 校验差异。
- **遗留建议**：把「tab 必须在 tabview 内」做成 `json2eez.py` 的门禁断言
  （本次为手工校验脚本，未落成常驻断言）。
