# P-0091 · 长按「忘记」连带触发「点击连接」：内核 CLICKED 发在 long_pr_sent 判断之外

- **工程**：小艺·智能屏 8（eez-test）/ LVGL 9.4（内核 lv_indev + src/native + PC 仿真走路器）
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：long_pr_sent,CLICKED在if之外,抑制窗口,长按双事件,longpress第二参,cat -A自查
- **关联提示词**：PR-0112

> 补档说明（2026-10-03）：正文按 `index.md` 的 P-0091 行 +
> 工程日志 `.workbuddy/memory/2026-10-02.md`「第 108 轮（22:50-23:05）长按行不许连带触发短按连接（P-0091）」回填。

## 现象（看到什么）

用户原话（PR-0112 逐字）：
> 「wifi长按触发时候，就不要触发 点击连接 了 ，长按触发了，就不要触发短按」

表现：WiFi 列表行**长按**弹「忘记网络」确认卡（P-0085 的功能）时，**同时**又发出了一次
「点击连接」命令 —— 一次手势跑了两条动作。

## 复现（怎么稳定重现）

★ 关键：**原来的走路器复现不出来**。走路器 `longpress <obj>` 只发 `LONG_PRESSED`，
等于绕过了内核行为。本轮给它**新增第二参 `1` = LONG_PRESSED 之后紧跟 CLICKED**（复现内核长按松手），
并新增走路脚本 **`lpsuppress`**：长按带 CLICKED → 期望只出忘记卡；1.2s 后普通点击同一行 →
期望正常弹密码面板（证明短按没被误伤）。修复前的表现 = 两个动作都发出去。

## 根因（真正的原因）

**在内核，不是 LVGL 的 bug 也不是 EEZ 的 bug**（`lv_indev.c:869-884`，RELEASED 分支）：

```c
if (i->long_pr_sent == 0) { indev_proc_short_click(...); }   // 长按时跳过 short click
send_event(LV_EVENT_CLICKED, indev_act);                      // ← 但这句在 if 之外！
```

长按松手时 `long_pr_sent == 1`，只跳过了 `indev_proc_short_click`，
**CLICKED 照发**。而本案的行热区**同时绑了** CLICKED(`wifi_pick_N`) 与
LONG_PRESSED(`wifi_forget_N`)（P-0085 的形态）⇒ 同一次手势两条命令都出去。
为什么以前没发现：① P-0085 刚把长按接上，之前没有"同控件双事件"的场景；
② 走路器原来不发这个组合（见「复现」段），仿真验不出来。

## 修复（做了什么）

**native 侧做抑制窗口**（`src/native/native_actions.cpp`）：

1. 新增 `static uint32_t s_lp_guard_ms;` + `#define WIFI_LP_GUARD_MS 800`；
2. `WIFI_FORGET_ACTION` 里记 `s_lp_guard_ms = lv_tick_get()`；
3. `WIFI_PICK_ACTION` 里若 `lv_tick_get() - s_lp_guard_ms < 800` 就 `return`（**不输出命令**）。
   **800ms 的依据**：松手后 CLICKED 在几十 ms 内就到（窗口够宽），
   又不会吞掉用户紧接着的正常点击。
4. 该文件没有 `TAG` / `esp_log.h` ⇒ 日志用 `printf`（真机串口同样可见）。
5. 仿真侧配套：`longpress` 第二参 `1`、新脚本 `lpsuppress`、`forget` 脚本的长按**全部带 `1`**。

## 证据（数字 / 命令输出）

- 真机侧：`native_actions` **真编译 exit 0、零警告**（手法见 P-0090：照抄
  `compile_commands.json` 的原命令，只换 `-o` 产物路径）。
- 日志实证（抑制生效的那一行）：
  ```
  [action] pick slot 1 suppressed: long-press owns this gesture
  ```
- 截图实证：`lpsuppress` 长按后**只见忘记卡**（无密码面板）；1.2s 后普通点击同一行
  正常弹密码面板 ⇒ 短按未被误伤。
- 回归：`forget` 两条长按同样 suppressed；`wifi` 回归绿；`all.py --sim` **PASS**。

## 沉淀（新增断言 / 案例 / 文档）

- ★ **凡"同一控件绑两个事件（短按 + 长按）"都要想到这条 CLICKED**：内核长按松手必然补发
  CLICKED，业务侧要么加抑制窗口，要么别把两个语义放在同一个对象上。
- ★ **仿真器必须复现内核的事件序列才验得住**：走路器命令若比内核"更干净"（只发 LONG_PRESSED），
  就会系统性漏掉这类 bug —— 与 P-0079/P-0057 的"假绿"同一方法论。
- 工具坑：Python heredoc 写 C 的 `\\n` 会落成**字面反斜杠 + n**（printf 打印出 `\n` 两个字符）；
  用 raw string 或单反斜杠，写完 `sed -n 'Np' | cat -A` 自查。
- 与 P-0085 互为因果：P-0085 建立了"同控件双事件"形态，本条补上它的代价与解法。
- 可加断言（本次未加）：走路脚本里"长按后同帧收到 pick 命令"直接判 FAIL。
