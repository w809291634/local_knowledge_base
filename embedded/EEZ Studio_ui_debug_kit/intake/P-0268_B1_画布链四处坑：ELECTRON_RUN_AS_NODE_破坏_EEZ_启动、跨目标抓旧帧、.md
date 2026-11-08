# P-0268 · B1 画布链四处坑：ELECTRON_RUN_AS_NODE 破坏 EEZ 启动、跨目标抓旧帧、最佳匹配判据偏置、对照图右半裁切

- **工程**：redblue_p4
- **日期**：2026-11-08
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：B1,CDP,EEZ画布,判据,目检
- **关联提示词**：PR-0614

## 现象（看到什么）

① EEZ Studio 启动报 bad option: --remote-debugging-port，CDP 9222 起不来；② grab.js 批量 --click 抓到多张相同帧；③ D5 用『最佳匹配』判切页，22 张全指向 wifi_pwd；④ 生成的 B1 对照长图右半空白。

## 复现（怎么稳定重现）

在设置了 ELECTRON_RUN_AS_NODE 的 shell 里直接起 EEZ；用抓图器跨目标不校验画布像素是否真变化；统一版式 UI 用差异像素数取最佳匹配；对照图右图 paste 到 x=1608 超出 1624 宽画布。

## 根因（真正的原因）

① CF/runtime.unset_env 明写必须清 ELECTRON_RUN_AS_NODE，否则 Electron 退化纯 Node 把所有开关当非法选项；② 画布异步重绘，选中态/光标闪烁也会让 toDataURL 变化，不足以证明切页；③ 差异像素计数受文字密度影响，文字最少的页天然最优；④ 拼图坐标算错。

## 修复（做了什么）

① 用 env -u ELECTRON_RUN_AS_NODE 启动，CDP 9222 正常；② 自写 design/b1_capture.js：每页等到画布与上一页真不同才落盘，点击取子元素最少的精确匹配；③ 改用『22 张 B1 图主数值区两两差异 > 0.005』+ 抽样目检证明切页；④ 右图 x 改 816。

## 证据（数字 / 命令输出）

B1 22/22 页抓到新帧；231 对两两差异最小 0.0168；目检 standby/main 身份正确；D5 平均相似度 96.16%；对照图 1624x2080 左右两栏完整。

## 沉淀（新增断言 / 案例 / 文档）

固化断言：起 Electron 应用先 unset ELECTRON_RUN_AS_NODE；批量抓画布必须跨目标校验像素变化；统一版式不做全局最佳匹配；拼图坐标必须断言落在画布内。
