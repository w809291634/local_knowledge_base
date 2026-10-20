# P-0141 · EEZ Run 预览的输入通道不产生 LVGL GESTURE 事件——手势验证必须走仿真/真机

- **工程**：watch (Design Watch)
- **日期**：2026-10-17
- **工具**：Qoder
- **状态**：known-limitation
- **标签**：cdp,run-preview,gesture,lv_indev,验证面,仿真
- **关联提示词**：PR-0236

## 现象（看到什么）

纯 EEZ 手势导航（工程模型 GESTURE 事件 + flow，屏根/控件级绑定、codegen 回调与连线全部在位、
构建 0 错 0 警）在 **Run 预览里左右滑无任何反应**；同工程在 PC_SIM（SDL 鼠标注入合成
LV_MOUSEMOTION 快扫）里 6/6 全 PASS（Dial 左滑→AppList、右滑回、行点击进详情、详情右滑回、
反方向不误触发）。

## 根因（真正的原因）

Run 预览的输入不是标准 lv_indev 指针管线：控件 CLICKED 是预览层**合成派发**的（所以点击导航可用），
LVGL 核心的 indev_gesture()（需要连续 read 节拍里的位移矢量累计 >50px）拿不到真实运动序列
⇒ GESTURE 永远不产生；屏根级 eventHandlers 在预览里也收不到 CLICKED（探针实证）。

## 修复（做了什么）

不改实现（实现是对的，真机/仿真的 indev 管线完整）；改**验证面分工**：
手势类交互的验收从 Run 预览移到 PC_SIM（verify/gesturetest_main.c 夹具：替换沙箱
design/sim_cmake/main.c 重建，跑 `main.exe gesturetest`，逐断言打印 PASS/FAIL）。
Run 预览继续负责点击/滚动/动效。

## 证据（数字 / 命令输出）

同一 main.exe：T1..T5 六断言全 PASS；期间 Run 预览同样接线滑动零反应（burst 连拍留档）。

## 沉淀（新增断言 / 案例 / 文档）

skills §11.41（手势绑定配方+验证面分工）；AGENTS.md 铁律⑤补手势口径；报告 §35。

---

【更正 2026-10-20（P-0149 后续实证）】本条“Run 预览永远不产生 GESTURE”的**绝对结论不成立**。
后续在同一 watch 工程中，EEZ Run 预览可正常触发右滑；asar 取证显示预览运行真 LVGL 9.4
WASM，DOM mousemove 的按帧合并会改变读点粒度。故本条的“零反应”仅适用于当时的运行时/窗口
形态，不能泛化为预览机制限制。保留不变的结论只有：**预览的手势结果不能替代 PC_SIM/真机验收**；
预览能触发或不能触发，都不足以单独裁决实现正确性。详见 P-0149 与 cases/B13。
