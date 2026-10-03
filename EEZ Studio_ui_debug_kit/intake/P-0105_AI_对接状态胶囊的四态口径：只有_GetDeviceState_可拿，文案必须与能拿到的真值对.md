# P-0105 · AI 对接状态胶囊的四态口径：只有 GetDeviceState 可拿，文案必须与能拿到的真值对齐

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：AI状态,胶囊,DeviceState,桥接,文案与真值,io_pc镜像,aiaudit
- **关联提示词**：PR-0147（「还是不用网络正常表示，还是使用 在线表示」）/ PR-0149（接 WorkBuddy 半成品）

## 现象（看到什么）

状态栏/对话页那枚 AI 胶囊一直硬编码显示 0（休眠中），喊话、播放时都不变；工程注释里这批改动被误写成 P-0099（库里 P-0099 是「6 个开关全是装饰」）

## 复现（怎么稳定重现）

真机：待机/对话页看胶囊文案是否随 唤醒-聆听-TTS播放 变化；PC：EEZ_SIM_AI=0..3 钉态 + 走路 --walk=aiaudit audit m_status 四枚胶囊

## 根因（真正的原因）

APP_IN_AI_STATE 从没被 io_sample_inputs 发布（写死 0）。可用真值只有 xiaozhi 的 GetDeviceState()（application.h:67-68）与 WiFi 是否拿到 IP，native 组件不 include 小智 C++ 头 ⇒ 需要板级 extern C 桥；而原设计第 3 态文案「等待回复…」描述的「已发送等云端回包」这个信号我们根本拿不到（说完话到首个音频包之间小智仍停在 Listening）

## 修复（做了什么）

main/board_p4_audio.cc 加 app_ai_device_phase() 返回 APP_AI_PHASE_{OTHER,IDLE,LISTENING,SPEAKING}；io_esp ai_state_tick()（工作任务 200ms）算 st=!wifi_up?0:(listening?2:(speaking?3:1)) 写 volatile uint8_t s_ai_state，LVGL 线程只读那一个字节（RV32 上 uint8 读写原子）；io_sample_inputs 发布 app_set_input_i(APP_IN_AI_STATE,...) 取代写死 0；文案「等待回复…」改「回复中…」（只删字不加字，烘焙零风险）；io_pc 同语义镜像 + build_ui.py 4 枚胶囊表两边措辞逐字一致

## 证据（数字 / 命令输出）

走路 --walk=aiaudit：EEZ_SIM_AI 钉 4 态、audit m_status 命中文案与态值一致；_device_syntax_check.py（io_esp/app_model/native_vars/native_vars/board_p4_audio）0 错 0 警；all.py --sim = 9 屏平均差异 9.87%（阈值 25%）。边界如实写进注释：P-0092 的 MQTT 8883 设备上仍不通，「在线」只代表网络与会话态在线，不等于云对话此刻一定通

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md：胶囊文案只能描述拿得到的信号；P-0098 追加 ai_state_tick 合并说明；本条补齐 11 处工程注释 P-0099 撞号的正确归属
