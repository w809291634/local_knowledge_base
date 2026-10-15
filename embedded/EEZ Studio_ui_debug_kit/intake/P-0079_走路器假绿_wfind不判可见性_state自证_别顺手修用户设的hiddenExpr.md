# P-0079 走路器「假绿」：`wfind()` 不判可见性 → 状态自证要加 `state`；以及别顺手修用户定死的热区 hiddenExpr

日期：2026-10-02（第 94 轮）

## 现象
用户报「仿真里点可用的 WiFi，还是弹不出输入密码」。排查过程里连续踩到三个坑：

1. **`ta` 读回 `"abc"` 看着像"密码输进去了"，其实密码面板压根没弹。**
2. 修热区 hiddenExpr 之后"点谁都弹面板"，被用户当场要求还原 —— 那行是**用户上轮特意设的**。
3. 编译反复失败在 `liblvgl.a`（`file truncated` / 符号 undefined），根因是**孤儿 make 占着库句柄**。

## 根因 1：走路器 `wfind()` 只是查名字表，不检查可见性 → 假绿
`w_do_key()` / `ta` 命令走 `wfind("pwd_kb")` / `wfind("pwd_ta")`，名字 map 里**对象名一直都在**，
哪怕面板是 hidden 的也一样拿到指针 → `kbdkey` 照常向隐藏 textarea 发 VALUE_CHANGED、
`ta` 照常读回 `"abc"`。整条"输密码→连接"链路全是绿的，其实一步都没走通。

**判据（加 `state` 命令，用 `lv_obj_is_visible()`）**：

```
[walk] state 密码面板=<可见|隐藏/未开|不存在> 键盘=<...> 列表=<...>
[walk]   AP 行热区（绝对坐标，中心点即点击落点）:
[walk]     slot0 @(167,226) 544x44 中心(438,247) 可见=0
```

原本自证里那个 `面板在活动屏=1/-1` 是**假自证**：`s_pwd_panel` 只在 `w_do_key` 里赋值，
面板早就弹了但它还是 NULL，显示 -1 只说明"还没轮到赋值"，跟面板开没开无关。

## 根因 2：用户定死的 hiddenExpr 被我当成 bug
`build_ui.py` 里（约 1960 行）——

```python
cur4 = "wifi_state == 4 && wifi_conn_slot == %d" % i   # 失败态
hit["hiddenExpr"] = "wifi_slot%d_ssid == '' || !(%s)" % (i, cur4)
```

`!(cur4)` = **热区只在失败态那一行显示**，与「重试」pill 的 `!(cur4)`（只在失败态显示）
严格互补，一次点击永远只命中一个控件。这就是用户上轮定的「**不要一点就弹 WiFi 连接**」。
我按"点不动就是 bug"把它改成 `/(cur4)`（正常态也有热区）→ 点谁都弹面板。
**判据：点 AP 行命中可见的 `net_net_slotN`（不是 `net_net_slotN_hit`）+ 面板始终"隐藏/未开"
= 正常态，不是 bug。** 已还原（`git diff design/build_ui.py` 对这行无输出）。

## 根因 3：孤儿 `mingw32-make.exe` 占着 `liblvgl.a`
被中断/超时的编译会留下 `mingw32-make.exe` 挂着不死。它占着
`PC_SIM/build/apl_lvgl_build/lib/liblvgl.a` 的文件句柄 → ar 每次都写出坏档，
报错在三处之间跳：`error reading xxx.c.obj: file truncated` →
`ar: lib\liblvgl.a: file format not recognized` → `ld: undefined reference to
lv_draw_buf_create_ex`（符号缺失）。
修：`taskkill //PID <三个孤儿> //F` → `mv` 走脏 `.a` 到 `_libtrash/` →
内核源码 `find src -name "*.c" -exec touch {} +`（1051 个）全量重编。
（fd 冲突时 `mv` 报 "Device or resource busy"，重试 1-2 次通常就成。）

## 修法清单
1. **新增走路命令**（都在 `sim.py` 模板里，`--walk` 分支已改为无条件 `write_main()`，
   否则改了 sim.py 还跑旧 main.c —— 和 P-0057 同族）：
   - `state`：可见性自证（面板/键盘/列表 + 5 行热区坐标与可见位）。
   - `mousef <obj>`：`s_mouse_fast=1` → press/release **同帧**（真人手速），
     与 `mouse` 的 press 后停 50ms 做对照，用来验证"点快了是不是没反应"。
   - `scan` / `disc`：仿真侧钩子，入口里 `extern void io_wifi_scan(int) /
     io_wifi_disconnect(int)` 直接调，抓「正在搜索网络…」和「未连接」两块界面出图目检
     （PC 入口声明，**设备侧零影响**）。
2. 命中打印改成**沿父链找第一个有名祖先**：`lv_indev_search_obj` 返回的多是匿名 part，
   原来只打 `wname_of(lv_obj_get_parent(hit))` 一律显示成 `net_net_list` 分不出点了哪行。
3. 两处排版（都是"逐元素居中 + 硬编码偏移"的老毛病，改成**整块居中**）：
   - 未连接卡（高 72）：两行 18+6+14=38 的块 `(72-38)/2=17` 起排。
     原来「未连接」`label_mid` 占满 72 高（行盒 `y2+27..45`）、第二行硬算 `y2+41..55`
     → **叠 4px**。
   - 搜索态：环 30 + 间距 10 + 文字 15 = 55 的块对齐 `scy`。
     原来环中心 `scy-20`、文字顶 `scy+10` → 整体重心 `scy-5`，**偏上 5px**。
   统一写法：`_top = 容器中心 - 块高/2`，再逐段往下排。

## 验证
- 流水线 `python design/all.py --sim` 门禁 **9.28% < 25%**，无缺屏。
- `--walk=net_states`：未连接卡两行分离居中、`正在搜索网络…` 环+文字居中；
  且 `state` 全程「密码面板=隐藏/未开」（= 还原后正确）。
- `--walk=click_speed`：点 AP 行命中 `net_net_slot1`（可见行），面板不弹 ✓。
- `--walk=wifi_ok` / `--walk=wifi` 回归通过（已保存直连拿到 IP；失败→重试链路正常）。
- 设备侧 `design/_device_syntax_check.py`：io_esp / native_actions / app_model /
  native_vars **4 文件 0 错 0 警**（本次只动 DSL + PC 入口）。

## 可复用原则
- ★ **"读到值"不等于"状态对了"**：仿真里判断界面状态一律用 `lv_obj_is_visible()`，
  别用"对象存不存在 / 文本读回什么"。
- ★ **看到"点不动"先分清是 bug 还是用户刻意**：先看这行代码最近是谁改的意图
  （`git diff` / 注释里的"用户特意定"），再决定改不改。
- ★ **编译在静态库上反复失败**：先 `tasklist` 查孤儿 make，再想重建的事。
- **多行/图文排版按整块居中**，别逐元素居中再硬编码偏移。
