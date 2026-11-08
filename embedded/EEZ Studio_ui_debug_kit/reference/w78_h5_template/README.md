# w78 H5 评审参考模板

本目录保存 w78 智能家居 H5 评审页的**参考实例**，用于复用分层总览、跳转演练、高清控件标注和右键批注。`designer_simple/overview_pro.html` 是来源工程的原始示例，可直接浏览器打开。它展示的是智能家居示例数据，不是新工程的设计。

## 文件

- `design/overview_pro.py`：三视图、标注、热区、跳转演练及批注导出。
- `design/simple_control.py`、`pages.py`、`values.py`：设计帧、几何、控件语义及动态读数。
- `design/nav_map.py`：页面跳转关系；`export_ui.py`：页面数据导出与确认门。
- `design/control_table.py`、`nav_audit.py`：生成控件清单和验证导航闭环。
- `assets/ui_bg.png`：示例帧引用的背景图；`designer_simple/overview_pro.html`：来源工程现成评审页。
- `design/flow_state.json`：**来源示例的历史状态，仅用于重现示例**。其中确认、冻结与时间只属于 w78，绝不代表新工程已确认或已冻结；新工程应建立自己的状态和确认流程。

## 复用方法

1. 将本目录复制到新的工作目录或工程的隔离目录，避免在经验库模板原件上运行或直接修改。
2. 示例可在复制后的目录中执行：先创建 `designer_simple` 与 `designer_annotated` 目录，再运行 `python design/overview_pro.py`、`python design/control_table.py`、`python design/nav_audit.py`。H5 生成器使用 Python；可选用 Node 检查生成页面脚本语法。生成的 HTML 是离线单文件。
3. 新工程按自身设计替换 `simple_control.py`、`pages.py`、`values.py` 和 `nav_map.py` 中的数据，适配 `export_ui.py` 和 `overview_pro.py` 的导入、分层、品牌、颜色、动态区与浏览器存储键。不得将 w78 房间、硬件状态或确认记录当作新工程的真实数据。
4. 在第一步设计经用户确认后，按用户要求在同一 H5 上核对控件类型、标注、页面关系、真实控件跳转及右键批注。修改只回设计源并重新生成，不手改生成的 HTML。逐项检查真实鼠标点击、返回、标注开关和批注导出。
5. H5 只能辅助设计与交互评审；实际页面、动态效果和硬件行为仍按流程在 EEZ、仿真和真机验证。

通用可移植生成器仍是 `../../tools/h5_overview_template.py`；本目录为更完整的 w78 参考实例，复制后必须适配，不能无修改地当作其他工程的成品。

## 差异与验证

本目录中的 H5 生成器和设计数据按来源工程复制。`nav_audit.py` 与 `control_table.py` 的模板副本增加了对 H5 专用开机预览页的排除：该页不属于业务页数据，原脚本直接查询会抛出 `KeyError`。w78 原工程未修改。其余原始示例图片、页面数据和状态均为示例，切勿作为新工程真实状态。

在隔离副本中已验证：H5 生成器产生 25 个画面并通过 Node 脚本语法检查；业务清单生成成功；导航审计通过（24 个业务页、57 条跳转和 21 条手势边）。这不代表已对所有浏览器交互或新工程完成验收。
