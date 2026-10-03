# P-0083 · 点单修复 4 实锤 + 扫描态不居中：transform_height 吃掉 MAIN 背景、EEZ label 没有 textAlign

- **工程**：小艺·智能屏 8（eez-test）/ LVGL 9.4 · 800×480（PC 仿真 + 真机两侧）
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：textAlign不存在,transform_height吃MAIN背景,轨道底box垫底,knob裁半,pad防clip,定宽串%3d,wUnit断链,静态居中,绝对坐标体系,%%转义
- **关联提示词**：PR-0107

> 补档说明（2026-10-03）：正文按 `index.md` 的 P-0083 行 +
> 工程日志 `.workbuddy/memory/2026-10-02.md`「第 98 轮（17:30-18:25）用户点单修复 5+1 项（P-0083）全部完成」回填。

## 现象（看到什么）

用户点单原话：「实锤 4 个，还有一个 正在搜索网络 不居中」（PR-0107 逐字记录），即第 97 轮
只查未改的那份对齐/间隔清单里被确认的 4 个实锤 + 1 个居中问题，本轮全修 + 附赠 1：

1. **通知卡时间与按钮不齐**：时间是顶对齐标题行、按钮对齐卡中心 → 实测**差 11px**。
2. **滑杆轨道底整个消失**（`transform_height` 加在 `LV_PART_MAIN` 把 obj 背景绘制吃掉，
   INDICATOR 收缩是生效的）。
3. **knob 在 0 / 100 两个端点被 obj 裁成半圆**。
4. **「42 %」有 6px 空隙**（数值右缘不恒定）。
5. **「正在搜索网络…」/「未找到可用网络」不居中**（全失效）。
6. 附赠：状态栏电量显示成 **"% 85"**（顺序反了，`%` label 排在数字左，是既有 bug）。

## 复现（怎么稳定重现）

- `python design/all.py --sim` 出图后**分区放大目检**（通知页时间/按钮、状态栏电量串）；
- 拖动滑杆看轨道底是否还在、拖到 0% 与 100% 看 knob 是否被裁；
- `python design/sim.py --walk=net_states` 抓搜索态截图看「正在搜索网络…」是否居中；
- 坐标取证用走路器 `audit` / `audit_all`（第 96 轮 P-0081 加的运行时体检命令）。

## 根因（真正的原因）

1. 时间那行写的是 `label_mid_right(tm_right, ly+11, lh(13), …)` —— y 多加了 11，
   于是对齐的是标题行而不是卡中心。
2. **`transform_height` 加在 `LV_PART_MAIN` 会吃掉该控件 obj 的背景绘制**：
   INDICATOR 的收缩生效、MAIN 轨道底整个消失 ⇒ **P-0049 那套技法的盲区**
   （当时只验了 knob / indicator，没验 MAIN 背景还在不在）。
3. knob 直径 = 控件高度（P-0049），端点值时圆心贴到 obj 边缘 → 被 obj 矩形裁半。
4. ★ **EEZ 的 label 根本没有 `textAlign` 属性**：W35 官方属性表 + asar 挖证都不存在；
   实测在 widget 的 "style" 字段发射 `text_align` **也不生成**。所以"靠样式做右对齐"这条路
   在 EEZ 里走不通 —— 这就是为什么以前一直没治好。
5. `label()` 显式传 `w` 时 **`wUnit` 没跟着切成 px**（被 `content` 吞掉）→
   `w=iw` + CENTER 的居中全失效（这是「正在搜索网络…」不居中的另一半根因）。
6. 电量是 `%` 与数字两个 label 拼接，排的顺序反了。
7. DSL 是**绝对坐标体系**：helper 组合容器时子对象必须给绝对坐标（`to_relative` 递减），
   写 `(0,0)` 会算出负值被 `check_bounds` 拦下。

## 修复（做了什么）

1. 通知卡时间：`label_mid_right(tm_right, ly+11, lh(13), …)` → `(tm_right, ly, h, …)`，与卡中心对齐。
2. **`track()` 重构（5 个调用点零改动）**：透明容器 `grp` 包 `[轨道底 box, slider]` ——
   轨道底改用**普通 box 垫底**（废掉用 transform_height 画底这条路），
   slider 的 MAIN `bg_opa=0` + **`pad_left/right = kd/2`**（knob 到 0/100 不再被 clip）。
3. 「正在搜索网络…」/「未找到可用网络」：`label()` 显式传 w 时自动置 `wUnit=px` +
   静态 `tw()` 居中（`x = ix + (iw - tw)/2`）。
4. 废弃 textAlign 思路，改 **`"%3d %%"` 定宽字符串变量**（`clock_text` 同款 native 模式：
   ASCII 走 Consolas 等宽 ⇒ 左对齐时右缘恒定）：
   - 新增变量 `volume_pct_text` / `brightness_text` / `music_vol_text` / `alert_vol_text`
     （+ `battery_pct_text`）；`app_model.h` 枚举 **+5**；`native_vars.cpp` 桥 get/set；
     `io_pc` / `io_esp` 各写入点 `snprintf("%3d %%")`；
   - `pct_label_right` 重写为单 label 绑 `<var>_text`（调用点 `+=` → `append` ×2）；
   - `sim.py` 冒烟里的 `objects.m_np_prog` 引用不受影响（slider 保留显式 id，`grp` 用 `id+"_grp"`）。
5. 状态栏电量同 4：改 `battery_pct_text` 单 label（`" 85 %"`）。

## 证据（数字 / 命令输出）

- 坐标实证（`audit_all`）：修复后时间 y = **157 / 287 / 351**，按钮 y = **157 / 287 / 352** ⇒ 对齐。
- 像素实证：knob 是**完整 14px 圆**；中心线上 knob 右侧整条 `#262c3c`（轨道底回来了）。
- 居中实证：「正在搜索网络…」中心 **439.5 = 列表中心**；`--walk=net_states` 截图目检 ✓。
- 门禁：`all.py --sim` **PASS**；设备侧 `_device_syntax_check.py` **4 文件 0 错 0 警**。
- 自己踩到的转义坑：Python 模板串里 `%3d %%` 写丢成 `%3d %` **共 6 处**，
  靠 `_device_syntax_check` + `grep` 兜住。
- 环境噪音（非代码问题）：walk 重跑时沙箱 safe-delete 钩子拦「删旧截图目录」，
  报 `SAFE_DELETE_BULK_CONFIRM_REQUIRED` / exit=1，截图实际已生成。

## 沉淀（新增断言 / 案例 / 文档）

- ★ **EEZ label 无 `textAlign`、widget "style" 不发射 `text_align`** ⇒ 文字对齐只有两条腿：
  静态 `tw()` 计算居中，或 native 定宽串。别再试样式链。
- ★ `transform_height` 加在 MAIN 的**第二条**副作用（第一条是 P-0049 的几何误解）：
  吃 obj 背景。本条与 P-0084（负面积 → INDICATOR 画到轨道上方）合起来把这套技法判死，
  细指示条改用 **MAIN pad**。
- ★ DSL 绝对坐标体系写进规矩（MEMORY.md「DSL 要点」段已有：DSL 绝对坐标、容器 pad=0）。
- 定宽串 `%3d %%` 成为「数字+单位」显示的统一范式（`clock_text` 同款），5 个 `_text` 变量全链路。
- 可加断言（本次未加）：扫 DSL 里 `textAlign` / style 发射的 `text_align` —— 在 EEZ 侧无效，出现即警告。
