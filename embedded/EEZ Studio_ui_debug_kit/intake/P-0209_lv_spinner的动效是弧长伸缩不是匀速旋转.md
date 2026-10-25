# P-0209 · lv_spinner 的动效是"弧长伸缩"，不是匀速旋转

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-25
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,spinner,动效,观感
- **关联提示词**：PR-0383

## 现象（看到什么）

用户看"连接中"的转圈说"感觉不对"。截图里是一个**很粗的环 + 一小截蓝弧**，
而且转起来蓝弧的长度在**一伸一缩**，不像常见的匀速旋转。

## 复现（怎么稳定重现）

`lv_spinner_create` + `lv_spinner_set_anim_params(obj, 1000, 120)`：弧长在 120°~210° 之间反复抻；
把第三个参数改小即可看出差别。

## 根因（真正的原因）

LVGL 9 的 spinner 由两条不同步的动画叠出来：`end_angle` 从 `angle` 跑到 `360+angle`，
`start_angle` 从 0 跑到 360（自定义贝塞尔），所以**弧长本身在变**；`angle` 越大伸缩越夸张。
另外它只是 `lv_arc` 的子类，**线宽走主题默认**（本机 64px 时约 10px），看着更"坨"。

## 修复（做了什么）

按用户口径：`angle=30`（保留伸缩、幅度减小）+ `arc_width=6`（轨道与指示器同宽）+ 64px、1000ms。
显式 `lv_obj_set_style_arc_width(..., 6, LV_PART_MAIN|LV_PART_INDICATOR)`，不依赖主题。

## 证据（数字 / 命令输出）

改前 `tmp/spin_A_120_def.png`（粗环 + 120~210° 伸缩）；改后 `build/sim_shots/busy.png`
（细环 + 30~120° 呼吸）；`[NAV] 60/0`、`PREFLIGHT PASS`。

## 沉淀（新增断言 / 案例 / 文档）

用 `lv_spinner` 前先确认要的是"伸缩"还是"匀速转"：要匀速转就自己用 `lv_arc` 动画 `rotation`；
要 `lv_spinner` 就接受它的伸缩，并把 `angle` 调小、线宽显式给值（别吃主题默认）。
过程截图（A/B/C 三版对比）用完即删，交付图只留最终 `busy.png`。
