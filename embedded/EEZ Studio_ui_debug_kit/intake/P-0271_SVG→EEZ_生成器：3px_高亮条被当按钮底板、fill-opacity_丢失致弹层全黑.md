# P-0271 · SVG→EEZ 生成器：3px 高亮条被当按钮底板、fill-opacity 丢失致弹层全黑

- **工程**：多参数监护仪 UI（multipara_monitor_ui）
- **日期**：2026-11-08
- **工具**：Trae
- **状态**：fixed
- **标签**：生成器,按钮底板,fill-opacity,遮罩
- **关联提示词**：PR-0622

## 现象（看到什么）

底部 tab 的 3px 激活条被选为按钮背景，渲染成整块青色；Wi-Fi 密码/关机确认的暗化遮罩变不透明黑，背景页看不见。

## 复现（怎么稳定重现）

设计 SVG 里按钮盒内除底板外还有一条 3px 高装饰 rect（激活条），且弹层背景 rect 用 `fill-opacity`；生成器取盒内首个 rect 当按钮底板、忽略 `fill-opacity`，打开工程即复现。

## 根因（真正的原因）

控件盒内任意 rect 都当按钮底板；rect 的 fill-opacity 未映射到 bg_opa。

## 修复（做了什么）

按钮底板只取 >=8x8 的 rect，细装饰条保留为静态容器；rect 的 fill-opacity 映射到容器 bg_opa。

## 证据（数字 / 命令输出）

main 底部 tab 恢复正常文字+细激活线；wifi_pwd/shutdown B1 显示暗化背景，平均相似度 95.34%。

## 沉淀（新增断言 / 案例 / 文档）

- 生成器取按钮底板时只接受 `>=8x8` 的 rect；更细的装饰条降级为静态容器。
- rect 的 `fill-opacity` 必须映射到 `bg_opa`（255 × opacity），否则遮罩不透明。
- 文档：NO_FLOW §2.2 生成器规则、CHANGELOG v0.9.187。
