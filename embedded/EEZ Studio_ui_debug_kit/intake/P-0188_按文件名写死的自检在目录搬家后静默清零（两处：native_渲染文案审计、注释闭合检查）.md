# P-0188 · 按文件名写死的自检在目录搬家后静默清零（两处：native 渲染文案审计、注释闭合检查）

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：门禁,静默失效,目录搬家,递归
- **关联提示词**：PR-0360

## 现象（看到什么）

native 从平铺改成 app/·navigation/·widgets/·platform/pc/ 分层后，check_project.py 照样全绿；实际上它扫的 wifi_ui_sync.cpp / native_actions.cpp / app_model.h 已经不存在，`if not os.path.exists(p): continue` 把两项检查直接跳过。

## 复现（怎么稳定重现）

把任一 native 文件改名或搬进子目录，再跑 design/check_project.py：仍然 rc=0。

## 根因（真正的原因）

同一族老毛病（B6/B7：覆盖面写死 + 找不到就跳过 = 假绿）。本工程还叠加了一次：新写的 [分层] 门禁首版 srcs() 只扫一层目录、include 匹配串带了收尾引号（`#include "app/model"` 永远匹配不到 `#include "app/model/wifi_model.h"`），四条规则全是假门禁，反向测试当场抓到。

## 修复（做了什么）

① 覆盖面一律递归遍历 src/native（.c/.cpp/.h），并加「找到的文件数 < 3 就 FAIL」的兜底断言，让覆盖面消失本身成为失败；② include 匹配改成前缀形式 `#include "<路径片段>`；③ 新门禁必须逐条反向测试（四条依赖规则各注入一次违例）。

## 证据（数字 / 命令输出）

反向测试：向 widgets 注入 lv_label_set_text(btn,"☃") → check_project rc=1 且点名 U+2603；复原 rc=0。[分层] 四条规则各注入一次违例 → 每次 rc=1 且打印违例文件；全部复原后 rc=0。preflight --with-sim 全链 PASS、六屏图逐字节一致。

## 沉淀（新增断言 / 案例 / 文档）

reference/12 迁移纪律补一条 + 本工程 preflight [分层] 门禁
