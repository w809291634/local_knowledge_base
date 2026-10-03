# P-0085 · 长按 WiFi 列表项「忘记网络」：EEZ 原生 LONG_PRESSED 与 CLICKED 并存

- **工程**：小艺·智能屏 8（eez-test）/ LVGL 9.4 · 800×480（PC 仿真 + 真机两侧）
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：LONG_PRESSED,onLongPress,eventHandlers数组,忘记网络,确认卡,WARN钮,saved可变副本,rescan先断开,链接期错,tapchild
- **关联提示词**：PR-0109

> 补档说明（2026-10-03）：正文按 `index.md` 的 P-0085 行 +
> 工程日志 `.workbuddy/memory/2026-10-02.md`「第 100 轮（19:19-19:55）」（P-0085 本体）与
> 「第 101 轮（20:37）真机『点了忘记还是能自动连』的修（P-0085 续）」回填。

## 现象（看到什么）

用户两条点单（PR-0109 逐字）：
> 「我要求增加 长按 对应wifi 列表中的 wifi ,支持忘记密码」
> 「（上一条）点击重新扫描的时候 要主动断开wifi 不然扫描不到」

当时的界面现状：长按没有任何通道（行热区只绑了 CLICKED）、没有"忘记网络"的确认卡、
重新扫描不会先断开。

## 复现（怎么稳定重现）

`python design/sim.py --walk=forget`：长按 slot0（已连接的网络）→ 出确认卡 → 点「忘记」→
该行「· 已保存」消失 + 断开；长按 slot1 → 点「取消」→ 收卡。
（PC 仿真本来就能重现"没有长按入口"这件事 —— 走路器发 LONG_PRESSED 时对象上没有对应 handler。）

## 根因（真正的原因）

不是 bug，而是**能力缺口 + 三条容易踩的实现约束**：

1. EEZ **原生支持 LONG_PRESSED**（事件枚举 code 7，asar 实证），但工程侧 `json2eez.py`
   没有 `onLongPress` 这条映射，所以 DSL 里根本发不出长按动作链。
2. `eventHandlers` 是**数组**，CLICKED 与 LONG_PRESSED 可以在同一控件上并存
   （短按=连接 / 长按=忘记，各一条 User Action）——不知道这点就会以为要二选一。
3. 「已保存」态在 PC 侧没法直接改：`AP_LIST` 是 `const`，必须另建可变副本才能记住忘记结果。
4. ★ 续（第 101 轮）：真机上"点了忘记还是能自动连"—— io_esp 的 `forget_confirm`
   第一版只投了 `WCMD_DISCONNECT`，**只停自动重连，保存的密码与 esp_wifi 的 STA 配置原封不动**
   ⇒ ① SsidManager 列表里仍有该 SSID → `wifi_ap_is_saved()` 仍 true → UI 还写「· 已保存」、
   点它走"已保存直连"；② esp-wifi 自己把上次 STA 配置存进 wifi namespace，重启/掉线照旧自动连。

## 修复（做了什么）

**UI / 生成链**
1. `json2eez.py` 新增 `onLongPress`：往 `eventHandlers` **数组**追加 `LONG_PRESSED`
   （`handlerType:"action"`），与 `onAction(CLICKED)` 并存。
2. 忘记确认卡：遮罩 + 居中 **400×178** 卡（**WARN 橙**「忘记」钮），挂在 `wifi_pop` 内容区**最后**
   （= z 最高）；显隐变量 `wifi_forget_shown`，回显 `wifi_target_ssid`。

**native 全链路**
3. 三条命令 `APP_OUT_WIFI_FORGET`（带槽位 = 弹卡）/ `WIFI_FORGET_CONFIRM`（真忘）/
   `WIFI_FORGET_CANCEL`，入口变量 `APP_IN_WIFI_FORGET_SHOWN`。
4. `io_pc`：`s_saved[]` + `s_slot_sub[][]` **可变副本**（`AP_LIST` const 改不动）+
   `wifi_rebuild_sub` 重拼 `sub`；`s_connected_slot` 记录当前连接槽（tick 2→3 与
   `apply_env_state` 钉态两处）；忘的是当前连接 → 断开回未连接。
5. `io_esp`：forget 落框架（弹卡回显 + confirm 断连）。
6. **重新扫描先主动断开**：`io_pc` / `io_esp` 的 `io_wifi_scan` 入口先 `disconnect`。
7. 第 101 轮把"真忘记"补全为三步（全部在 WiFi 工作任务里，`esp_wifi_set_config` 阻塞 ~100ms，
   **LVGL 线程零阻塞** —— P4 铁律）：
   ① `SsidManager::GetInstance().RemoveSsid(idx)`（按 SSID 找下标，组件内部 `SaveToNvs` 持久化）；
   ② `esp_wifi_get_config(WIFI_IF_STA)` → 清 ssid/password/threshold → `esp_wifi_set_config`
   （精准只清 sta、不动 ap，比 `esp_wifi_restore_config` 全清温和）；
   ③ 忘的是当前连接 → `s_user_disconnected = true` + `wifi.StopStation()`；末尾重扫一遍，
   让 UI 的「已保存」标记立刻消失。LVGL 侧 `io_wifi_forget` 锁存 `s_forget_ssid`（文件级 static），
   confirm 只投 `WCMD_FORGET + ssid` + 收卡（删掉原来"只投 DISCONNECT + TODO"的假实现）。

## 证据（数字 / 命令输出）

- `all.py --sim` **PASS**；设备侧 `_device_syntax_check.py` **4 文件 0 错 0 警**。
- `--walk=forget` 全链路绿：长按 slot0 已连接网络 → 确认卡 → 忘记 → 「· 已保存」消失 + 断开；
  长按 slot1 → 取消 → 收卡。
- 第 101 轮真机侧结论（记录原话）：忘完再点该网络 → `wifi_ap_is_saved()=false` →
  弹密码面板，不再直连；回归 `forget` / `wifi` / `wifi_ok` 全绿；用户需 `idf.py build` 重烧。

## 沉淀（新增断言 / 案例 / 文档）

- ★ 同一控件绑「短按 + 长按」两条事件是**合法形态**（`eventHandlers` 数组），但由此引出
  **P-0091**：内核长按松手会**连带再发一次 CLICKED**，必须 native 侧做抑制窗口。
- ★ 「忘记」不是"断开"：真忘记要同时清 **SsidManager 列表** + **esp_wifi 的 STA 配置**
  （两处独立持久化），只 `StopStation` 是假忘记。
- 本轮记到的工具坑：① walk 的对象名 = `screens.h` 字段**全串**（带 `m_` 前缀，
  如 `m_net_net_slot0_hit` / `m_net_forget_panel`），手工短名表只覆盖旧对象；
  ② `button()` 不传 id 就没有名字 → walk 用 `tapchild <面板> <子序号>`；
  ③ **新 action 缺 native 实现是"链接期"才报的错**（EEZ 只生成 `extern` 声明），
  必须同步 `native_actions.cpp`；④ Python heredoc 会吃掉宏的 `\` 续行符（变成单行宏，合法但要留意）。
- PC 与真机文案继续逐字对齐（「· 已保存」这类标记两边同一串）。
