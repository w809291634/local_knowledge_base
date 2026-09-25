# P-0001 · 缺 Pillow 时脚本裸崩（与文档承诺不符）

- **工程**：spilcd_spiopt_eez_lv_port_pc_tem_atks3 / main/test（ui_debug_kit 工具链）
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：工具缺陷,Pillow,降级
- **关联提示词**：PR-0018

## 现象（看到什么）

用**不含 Pillow** 的解释器跑 `tools/tree_check.py`，抛：

```
AttributeError: 'NoneType' object has no attribute 'truetype'
  File "tools/kit.py", line 337, in _font
    self._cache[px] = ImageFont.truetype(self.ttf, int(px))
```

而 `README.md` / `tools/README.md` 都写着「Pillow 按需依赖，缺了会给安装提示，不会崩」。

## 复现（怎么稳定重现）

```bash
<python 不含 Pillow> tools/tree_check.py
```

本机 `python`(base) 无 Pillow、venv `.../envs/default` 有 Pillow 12.3.0 —— 所以
`run_gate.py`（会自动挑 venv）不会暴露它，只有**直接跑**才暴露。

## 根因（真正的原因）

「按需依赖 Pillow」只在 `kit.open_gray()`（即 `ink_check.py` 那条路径）真正落实了。
`TextMeasurer._font / _icon_font` 与 `kit.diff_report()` 直接用了模块级的 `ImageFont` / `Image`，
而 Pillow 缺失时它们已被置为 `None` → 报 `NoneType`。

## 修复（做了什么）

- `tools/kit.py`：`TextMeasurer._font / _icon_font` 与 `diff_report()` 开头加 `require_pil()`
- `tools/tree_check.py`：缺 Pillow 时**优雅降级** —— 打印提示、跳过文本度量与按墨迹的越界检查，
  仍完成 字体名 / 跳转 / 入口页 / 纯几何框 检查（而不是整体失败）

## 证据（数字 / 命令输出）

- 修复前：无 Pillow 跑 tree_check → `AttributeError`，进程非正常退出
- 修复后：无 Pillow 跑 tree_check → `⚠️ 未安装 Pillow → 跳过文本度量…` 后正常完成，`rc=0`
- 含 Pillow（venv）跑 `run_gate.py` → `G4 PASS` 不受影响

## 沉淀（新增断言 / 案例 / 文档）

- 文档同步：`README.md` / `PLAYBOOK.md` / `tools/README.md` 补齐工具与文件清单
- `CHANGELOG.md` 记 v0.4.1
- 未设为断言（属工具自身健壮性，非工程 UI 断言）
