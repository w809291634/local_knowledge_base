# -*- coding: utf-8 -*-
"""月度项目计划表 → 软件交付数据统计：按人补录工具。

规则正文（列映射口径、不代填的列、门禁判据）见
`yjt/delivery_stats/plan-to-stats-monthly-transfer.md`，本文件只实现该口径，不改判据。

--plan / --stats 是 B 类机器路径（每台电脑位置不同），脚本**不设默认值、不猜路径**，每轮由用户给真值。
`find` / `preview` / `audit` 全程只读；只有 `write` 改文件，且改前先自动备份。
"""

import argparse
import datetime
import re
import shutil
import sys
from copy import copy
from pathlib import Path

import openpyxl

MARKER = "ai在如下位置进行新增"
EXCEL_EPOCH = datetime.date(1899, 12, 30)
STATS_MAX_COL = 34  # A..AH

# 统计表列位（第 1 行表头固定）
COL = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "I": 9, "J": 10, "K": 11, "L": 12, "M": 13, "N": 14, "O": 15, "P": 16,
    "Q": 17, "R": 18, "S": 19, "T": 20, "U": 21, "V": 22, "W": 23, "X": 24,
    "Y": 25, "Z": 26, "AA": 27, "AB": 28, "AC": 29, "AD": 30, "AE": 31,
    "AF": 32, "AG": 33, "AH": 34,
}

# 计划表表头文字 → 本工具用的键；表头各月列位会变，所以按文字找，不按列号
PLAN_FIELD_KEYS = {
    "编码": ("项目编码",),
    "名称": ("项目名称",),
    "目标": ("交付任务目标", "需求交付目标"),
    "计划时间": ("需求计划时间", "计划完成时间", "计划时间"),
    "实际时间": ("实际时间",),
    "责任人": ("关联责任人", "负责人"),
    "进度说明": ("进度状态说明",),
    "类别": ("类别",),
    "项目经理": ("项目经理",),
    "业务部门": ("业务部门",),
    "注册主体": ("注册主体",),
}


def norm(value):
    """表头与单元格文字统一：压掉换行与多余空格，便于比对。"""
    if value is None:
        return ""
    return re.sub(r"\s+", "", str(value))


def clean_multiline(value):
    if value is None:
        return ""
    lines = [ln.strip() for ln in str(value).splitlines() if ln.strip()]
    return "\n".join(lines)


def as_demand_time(value):
    """计划表时间列 → 统计表口径：真日期/序列号 → '11月13日'；文本原样保留。"""
    if value is None:
        return ""
    if isinstance(value, (int, float)) and 40000 < value < 60000:
        d = EXCEL_EPOCH + datetime.timedelta(days=int(value))
        return f"{d.month}月{d.day:02d}日"
    if isinstance(value, (datetime.datetime, datetime.date)):
        return f"{value.month}月{value.day:02d}日"
    text = str(value).strip()
    iso = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:\s.*)?", text)
    if iso:
        return f"{int(iso.group(2))}月{int(iso.group(3))}日"
    return text


def clean_code(value):
    """编码格清洗：去括号后缀（如"（订单）"）、压空格；含'/'的双编码保留并另行告警。"""
    code = norm(value)
    code = re.sub(r"\([^)]*\)", "", re.sub(r"（[^）]*）", "", code))
    return code.strip("/").strip()


def code_tokens(code):
    """抽出去掉括号后仍可比对的编码片段，用于查重（双编码 A/B 会出两个）。"""
    return [t for t in re.split(r"[^0-9A-Za-z]+", code) if len(t) >= 6]


def _plan_header_map(row_cells):
    """判断该行是否是某分段的表头行，是则返回 字段名→列号。"""
    labels = {norm(c.value): c.column for c in row_cells if c.value not in (None, "")}
    if not labels:
        return None
    if not (labels.get("优先级") or labels.get("序号")):
        return None
    if labels.get("项目名称") != 5:  # 项目名称固定在 E 列，否则不是本表的分段表头
        return None
    mapping = {}
    for field, needles in PLAN_FIELD_KEYS.items():
        for label, col in labels.items():
            if any(n in label for n in needles):
                mapping.setdefault(field, col)
                break
    return mapping if "名称" in mapping and "责任人" in mapping else None


def find_person_tasks(plan_path, person, sheets=None):
    """扫计划表，回传该人名下全部任务行（含分段重复项，不去重）。"""
    wb = openpyxl.load_workbook(plan_path, data_only=True)
    out = []
    for ws in wb.worksheets:
        if ws.sheet_state != "visible":
            continue
        if sheets and ws.title not in sheets:
            continue
        header = None
        for row in ws.iter_rows():
            cells = list(row)
            if all(c.value in (None, "") for c in cells[: min(15, len(cells))]):
                continue
            hm = _plan_header_map(cells)
            if hm:
                header = hm
                continue
            if not header:
                continue
            owner_col = header.get("责任人")
            owner = str(cells[owner_col - 1].value or "") if owner_col else ""
            hit_in = "责任人列" if person in owner else None
            if hit_in is None:
                for c in cells:
                    if isinstance(c.value, str) and person in c.value:
                        hit_in = f"第{c.column}列"
                        break
            if hit_in is None:
                continue
            rec = {
                "sheet": ws.title,
                "row": cells[0].row,
                "hit_in": hit_in,
                "编码": _cell(cells, header, "编码"),
                "名称": clean_multiline(_cell(cells, header, "名称")),
                "目标": clean_multiline(_cell(cells, header, "目标")),
                "计划时间": as_demand_time(_cell(cells, header, "计划时间")),
                "责任人": owner,
                "进度说明": clean_multiline(_cell(cells, header, "进度说明")),
                "类别": norm(_cell(cells, header, "类别")),
                "项目经理": norm(_cell(cells, header, "项目经理")),
                "业务部门": norm(_cell(cells, header, "业务部门")),
                "注册主体": norm(_cell(cells, header, "注册主体")),
            }
            out.append(rec)
    return out


def _cell(cells, header, field):
    col = header.get(field)
    if not col:
        return None
    return cells[col - 1].value if col - 1 < len(cells) else None


def stage_from_category(task):
    """计划表"类别/目标" → 统计表 G 列（项目阶段软件）。认不出返回 ''，由调用方记告警。"""
    cat, goal = task["类别"], task["目标"]
    if any(k in cat for k in ("注册", "体考", "送检")):
        return "注册"
    if "中试" in goal or "中试" in cat:
        return "中试跟进"
    if cat in ("模具样机", "手板样机", "样机", "模具物料回厂"):
        return "开发阶段"
    return ""


def map_to_stats_row(task, person, name_style="sector"):
    """按正文第 4 节口径生成一行；返回 (列名→值, 告警列表)。"""
    warn = []
    subject = task["注册主体"] or task["业务部门"]
    name = re.sub(r"\s+", " ", task["名称"]).strip()
    if name_style == "register":
        b = f"注册 -- {name}"
    elif name_style == "plain":
        b = name
    else:
        b = f"{subject} -- {name}" if subject else name

    goal_lines = [ln for ln in task["目标"].split("\n") if ln.strip()]
    change = [ln for ln in goal_lines if "需求变更" in ln]
    goal = [ln for ln in goal_lines if "需求变更" not in ln]
    stage = stage_from_category(task)
    if not stage:
        warn.append(f"G 列留空：类别原文「{task['类别'] or '无'}」推不出阶段")
    code = clean_code(task["编码"])
    if "/" in norm(task["编码"]):
        warn.append(f"A 列是双编码「{norm(task['编码'])}」，统计表历史上通常只落第一段")

    row = {
        "A": code,
        "B": b,
        "D": person,
        "G": stage,
        "H": "\n".join(goal) if goal else task["目标"],
        "I": task["计划时间"],
        "AA": task["项目经理"],
        "AB": subject,
    }
    if task["进度说明"]:
        row["R"] = task["进度说明"]
        if task["进度说明"] in ("联网",):
            warn.append(f'R 列原文「{task["进度说明"]}」疑为计划表串列，照搬待人工核')
    if change:
        row["U"] = "\n".join(dict.fromkeys(change))
    if not row["I"]:
        warn.append("I 列留空：计划表该格无时间")
    return {k: v for k, v in row.items() if v}, warn


# ------------------------- 统计表侧 -------------------------

def _find_marker_row(ws):
    for r in range(1, ws.max_row + 1):
        if norm(ws.cell(r, 1).value) == MARKER:
            return r
    raise AssertionError(f"找不到标记行「{MARKER}」（{ws.title}）")


def _find_style_row(ws, person):
    for r in range(ws.max_row, 1, -1):
        if norm(ws.cell(r, COL["D"]).value) == person:
            return r
    return ws.max_row


def _find_month_header_row(ws):
    for r in range(ws.max_row, 1, -1):
        v = norm(ws.cell(r, 1).value)
        if re.fullmatch(r"\d{1,2}月份", v or ""):
            return r
    raise AssertionError("表内找不到月份分组行，无法取分组行样式")


def month_block_bounds(ws, month):
    """本月区块 = 最后一个「<month>月份」分组行 → 标记行之前。"""
    start = None
    for r in range(1, ws.max_row + 1):
        if norm(ws.cell(r, COL["A"]).value) == f"{month}月份":
            start = r
    marker = _find_marker_row(ws)
    return (start or 1), marker - 1


def find_existing_codes(stats_path, sheet, tasks, month=None):
    """查重（第 6 节判据 1 与 4）：按编码片段匹配，分"本月区块内=真重复"和"历史行=参考"。"""
    wb = openpyxl.load_workbook(stats_path, data_only=True)
    ws = wb[sheet]
    lo, hi = month_block_bounds(ws, month) if month else (1, ws.max_row)
    tokens = {}
    for t in tasks:
        for tk in code_tokens(clean_code(t["编码"])):
            tokens.setdefault(tk, []).append(t)
    in_block, history = {}, {}
    for r in range(2, ws.max_row + 1):
        cell = norm(ws.cell(r, COL["A"]).value)
        matched = [t for tk, ts in tokens.items() if tk in cell for t in ts]
        if not matched:
            continue
        info = {"row": r, "B": re.sub(r"\s+", " ", str(ws.cell(r, COL["B"]).value or "")).strip(),
                "D": ws.cell(r, COL["D"]).value, "AB": ws.cell(r, COL["AB"]).value,
                "codes": [clean_code(t["编码"]) for t in matched]}
        (in_block if lo <= r <= hi else history).setdefault(cell, []).append(info)
    return {"month_block": (lo, hi), "同月区块内_真重复": in_block, "区块外_历史与补录区": history}


def preview_rows(tasks, person, name_style="sector"):
    rows, warnings = [], []
    for t in tasks:
        row, warn = map_to_stats_row(t, person, name_style)
        rows.append((t, row))
        for w in warn:
            warnings.append(f"[{t['sheet']} 第{t['row']}行 {row.get('A','')}] {w}")
    return rows, warnings


def write_rows(stats_path, sheet, rows, person, month, backup=True, apply=False):
    """备份 → 锚点断言 → 写入标记行之下。apply=False 只算落点不落盘。"""
    wb = openpyxl.load_workbook(stats_path)
    ws = wb[sheet]
    marker = _find_marker_row(ws)
    need = len(rows) + 1  # 分组行 + 数据行
    occupied = [
        (r, c) for r in range(marker + 1, marker + 1 + need) for c in range(1, STATS_MAX_COL + 1)
        if ws.cell(r, c).value not in (None, "")
    ]
    assert not occupied, f"标记行下方 {need} 行非空，先人工确认落点：{occupied[:5]}"
    style_row = _find_style_row(ws, person)
    head_row = _find_month_header_row(ws)
    plan = {
        "marker_row": marker,
        "group_row": marker + 1,
        "first_data_row": marker + 2,
        "rows": need,
        "style_row": style_row,
        "month_header_row": head_row,
    }
    if not apply:
        return plan
    if backup:
        tmp = Path(stats_path).parent / "tmp"
        tmp.mkdir(exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = tmp / f"{Path(stats_path).stem}_备份前_{stamp}.xlsx"
        shutil.copy2(stats_path, bak)
        plan["backup"] = str(bak)

    r = marker + 1
    for c in range(1, STATS_MAX_COL + 1):
        ws.cell(r, c)._style = copy(ws.cell(head_row, c)._style)
    ws.cell(r, COL["A"]).value = f"{month}月份（{person}·从{month}月项目计划表补录）"
    ws.cell(r, COL["B"]).value = "*" * 20
    ws.cell(r, COL["B"]).font = copy(ws.cell(head_row, COL["B"]).font)
    ws.cell(r, COL["B"]).alignment = copy(ws.cell(head_row, COL["B"]).alignment)

    for _, row in rows:
        r += 1
        for c in range(1, STATS_MAX_COL + 1):
            cell = ws.cell(r, c)
            cell._style = copy(ws.cell(style_row, c)._style)
            cell.value = None
        for key, value in row.items():
            ws.cell(r, COL[key]).value = value
    wb.save(stats_path)
    plan["last_data_row"] = r
    return plan


def audit(stats_path, backup_path, from_row, sheet="软件组789月交付数据"):
    """第 8 节第 5 步四条对账。空白规范化不计入差异，公式必须逐格一致。"""
    new = openpyxl.load_workbook(stats_path)
    old = openpyxl.load_workbook(backup_path)
    res = {"real_diff": [], "lost_formula": [], "new_formula": [], "blank_norm": 0,
           "sheets_same": new.sheetnames == old.sheetnames, "structure": []}
    for name in old.sheetnames:
        a, o = new[name], old[name]
        res["structure"].append(
            (name, len(o.merged_cells.ranges), len(a.merged_cells.ranges),
             o.auto_filter.ref, a.auto_filter.ref, str(o.dimensions), str(a.dimensions))
        )
        for row in o.iter_rows():
            for cell in row:
                if name == sheet and cell.row >= from_row:
                    continue
                nv = a[cell.coordinate].value
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    if not (isinstance(nv, str) and nv.startswith("=")):
                        res["lost_formula"].append((name, cell.coordinate))
                    elif nv != cell.value:
                        res["real_diff"].append((name, cell.coordinate, cell.value, nv))
                    continue
                if cell.value not in (None, "") and nv not in (None, "") and nv != cell.value:
                    res["real_diff"].append((name, cell.coordinate, cell.value, nv))
                elif cell.value == "" and nv is None:
                    res["blank_norm"] += 1
        for row in a.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    if not str(old[name][cell.coordinate].value or "").startswith("="):
                        res["new_formula"].append((name, cell.coordinate))
    res["pass"] = (not res["real_diff"] and not res["lost_formula"]
                   and res["sheets_same"])
    return res


# ------------------------------ CLI ------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["find", "preview", "write", "audit"])
    ap.add_argument("--plan", help="项目计划表 xlsx（B 类机器路径，每轮由用户给）")
    ap.add_argument("--stats", help="软件交付数据统计 xlsx（B 类机器路径）")
    ap.add_argument("--sheet", default="软件组789月交付数据", help="统计表工作表名")
    ap.add_argument("--person", help="补录的软件工程师姓名")
    ap.add_argument("--month", type=int, help="月份数字，用于分组行文字")
    ap.add_argument("--name-style", default="sector", choices=["sector", "register", "plain"])
    ap.add_argument("--sheets", help="限定计划表工作表，逗号分隔")
    ap.add_argument("--apply", action="store_true", help="真正落盘（默认只算落点）")
    ap.add_argument("--backup", help="audit 用的备份文件路径")
    ap.add_argument("--from-row", type=int, help="audit 新增区起始行")
    a = ap.parse_args(argv)

    if a.cmd in ("find", "preview", "write") and not (a.plan and a.person):
        ap.error("find/preview/write 需要 --plan 与 --person")

    if a.cmd == "find":
        only = a.sheets.split(",") if a.sheets else None
        for t in find_person_tasks(a.plan, a.person, only):
            print(f"{t['sheet']} 第{t['row']}行 [{t['hit_in']}] {t['编码']} | {t['名称'].replace(chr(10), ' / ')} | "
                  f"计划{t['计划时间']} | 类别{t['类别']} | PM{t['项目经理']} | {t['注册主体'] or t['业务部门']}")
        return 0

    only = a.sheets.split(",") if a.sheets else None
    if a.cmd == "audit":
        if not (a.stats and a.backup and a.from_row):
            ap.error("audit 需要 --stats --backup --from-row")
        res = audit(a.stats, a.backup, a.from_row, a.sheet)
        print("新增区以外真实内容差异:", len(res["real_diff"]), res["real_diff"][:5])
        print("公式丢失:", len(res["lost_formula"]), "公式新增:", len(res["new_formula"]))
        print("空白规范化(可忽略):", res["blank_norm"], "| 工作表清单一致:", res["sheets_same"])
        print("结构(表名|合并旧新|筛选旧新|维度旧新):")
        for s in res["structure"]:
            print("  ", s)
        print("判据:", "PASS" if res["pass"] else "FAIL")
        return 0 if res["pass"] else 1

    tasks = find_person_tasks(a.plan, a.person, only)
    rows, warns = preview_rows(tasks, a.person, a.name_style)
    print(f"共 {len(rows)} 行（{a.person}）")
    for t, row in rows:
        print(" -", row.get("A"), "|", row.get("B"), "|", row.get("G"), "|",
              row.get("I"), "|", (row.get("H") or "").replace("\n", " / ")[:60])
    for w in warns:
        print("  !", w)
    if a.cmd == "preview":
        if a.stats and a.sheet:
            hits = find_existing_codes(a.stats, a.sheet, tasks, a.month) if a.month else None
            if hits is None:
                print("查重：未给 --month，跳过（需要 --month <数字> 才能框出本月区块）")
                return 0
            dup = hits["同月区块内_真重复"]
            print("查重区间:", hits["month_block"])
            print("  同月区块内已有同编码行（=真重复，须裁决）:")
            for k, v in (dup or {}).items():
                for x in v:
                    print(f"    计划表编码 {x['codes']} → 统计表第{x['row']}行 D={x['D']} | {x['B']}")
            print("  区块外命中（历史月/本轮补录区，只作参考）:",
                  {k: [x['row'] for x in v] for k, v in hits["区块外_历史与补录区"].items()} or "无")
        return 0

    if not (a.stats and a.month):
        ap.error("write 需要 --stats 与 --month")
    plan = write_rows(a.stats, a.sheet, rows, a.person, a.month, apply=a.apply)
    print(("已写入 " if a.apply else "落点预演：") , plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
