# P-0098 · 唤醒词没有点亮屏幕：接语音交互态（SetCallbacks 外部接管是陷阱）

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：息屏,唤醒词,DeviceState,SetCallbacks,桥接,GetDeviceState
- **关联提示词**：PR-0132 / PR-0133

## 现象（看到什么）

喊「你好小智」后屏幕仍黑着（息屏只是背光为 0，LVGL 与 AFE 都在跑），息屏判定完全没接音频侧。

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

唤醒链路整个在小智内部：AudioServiceCallbacks.on_wake_word_detected 到 application.cc 置事件位到 HandleWakeWordDetectedEvent，工程侧零接入。看似最正统的 GetAudioService().SetCallbacks 追加回调是陷阱 —— SetCallbacks 是整体替换（application.cc:75-84 就是用它装自己那三个回调），覆盖后 WAKE_WORD_DETECTED、SEND_AUDIO、VAD_CHANGE 全丢，唤醒后不再进 listening。

## 修复（做了什么）

H3 轮询方案，零框架改动：main/board_p4_audio.cc 加 extern C 桥 app_voice_interaction_active 判 connecting/listening/speaking 三态（native 组件不 include 小智 C++ 头，沿用 app_audio_set_output_volume 的套路）；io_esp 工作任务每 200ms 调 voice_activity_tick，交互中续期、息屏态恢复背光并打 screen wake by voice interaction。依据是 public 的 GetDeviceState 为 atomic 读，零阻塞。

## 证据（数字 / 命令输出）

真机判据：息屏中喊唤醒词出现 screen: wake by voice interaction 且屏亮；对话期间不熄。_device_syntax_check.py 支持传文件名，把 main/board_p4_audio.cc 也纳入真编译（板级桥以前是盲区）。

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md：禁止用 SetCallbacks 从外部接小智回调；桥文件也要跑真编译
