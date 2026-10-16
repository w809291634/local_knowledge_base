# P-0132 · EEZ 动作里引用控件要写『规范化源码标识符』（row_SportMode → row_sport_mode）而非原始 identifier

- **工程**：watch (Design Watch)
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：eez-codegen,标识符规范化,getWidgetObjectIndexByName,动作参数,Widget index not found
- **关联提示词**：PR-0218,P-0131

## 现象（看到什么）

LVGLActionComponent 的 objGetDisplayY/objStyleSetProperty 里 object 参数写 row_SportMode（工程 JSON 里真实的 identifier 字段值）→ 构建输出 110 条 'Widget index not found for "row_SportMode"'

## 复现（怎么稳定重现）

生成器直出动作 JSON：object="row_SportMode"（原样 identifier）→ python design/eez_build.py → 110 errors

## 根因（真正的原因）

codegen 的控件查表 getWidgetObjectIndexByName(this,o) 在 lvglObjectIdentifiers.fromPage.identifiers 里 indexOf(o)；该列表存的是 getName('', identifier, UnderscoreLowerCase) 规范化后的名字（row_sport_mode），不是 JSON 里的原始 identifier

## 修复（做了什么）

生成器加 c_ident()：re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', s).lower()，动作 object 一律用规范化名；与 screens.c 的 objects.row_sport_mode 对齐

## 证据（数字 / 命令输出）

修复后 eez_build 输出 'No error and no warning detected'（110→0）；生成代码 objects.row_sport_mode 等索引全部解析成功

## 沉淀（新增断言 / 案例 / 文档）

reference/07 序列化语法速查补一条；P-0131 同族
