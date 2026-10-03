# P-0109 · 聊天气泡头像方块是空的：注释写着 sparkle/person 却没放图标，而 audit 只查文字查不到

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：聊天,头像,图标,FontAwesome,glyphs_seed,审计盲区
- **关联提示词**：PR-0165

## 现象（看到什么）

用户报「气泡左右那个头像方块是空的」：30×30 圆角色块里没有图标。页头那颗星是好的，只有运行期建的行是空的

## 复现（怎么稳定重现）

--walk=chataudit 后看 build/sim_shots/walk_chataudit/*.png；或 --walk=audit_all 看 m_ai_chat_scroll 子树。★ 注意走路截图只在跑 --walk 时更新，all.py --sim 不重生成它 —— 目检前先看 mtime，否则会拿旧图下结论（本轮就差点这么错）

## 根因（真正的原因）

native_actions.cpp chat_make_row() 建头像时只设了 bg_color/radius，注释写着「AI=主色 sparkle，用户=灰 person」但**从没创建图标 label** —— 注释是设计意图，不是实现。为什么门禁抓不住：design/sim.py 的文字体检只查「该有文字却没有文字」的 label，图标缺失时那个位置**根本没有对象**，所以 vis/空文字两条判据都不触发 ⇒ 这是审计器的已知盲区（图标类缺失一律查不到）

## 修复（做了什么）

chat_make_row 里给徽章加一个 label：码位 = 私有区 F005(sparkle)/F007(person)，用运行期 UTF-8 编码（3 字节，不写字面量以免源码里出现不可打印字符），字体取 16px 档、AI 白色 / 用户 0xc7cede、lv_obj_center 居中；名字表沿用 design/build_ui.py 的 SYM/CH。同时在 glyphs_seed["..._16"] 补 CH["sparkle"]+CH["person"] —— 16px 原先没有 person，不补就是徽章里一个豆腐块

## 证据（数字 / 命令输出）

烘完用 design/_glyph_probe.py 反解产物自证：16px 含 F005=True、F007=True；13px 7413 码位、语气词零缺。--walk=chataudit 4 步全 [ok]，audit 输出里徽章 label 实测 18x19（AI）/ 14x19（用户）可见且非空；截图 12_c2_long_reply.png 目检：AI 侧白星、用户侧浅灰人形。门禁 all.py --sim = 9 屏 9.90% 无缺屏；native_actions.cpp 真编译 0 错 0 警

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md/本条记下：audit 只查文字不查图标 —— 以后凡是「运行期建的装饰/图标」必须靠截图目检或给它加断言；以及「注释写了什么不等于实现了什么」
