# -*- coding: utf-8 -*-
"""软件交付数据统计（月度） → 软件N月份工时统计表：按人补录。

规则正文见 `yjt/delivery_stats/stats-to-timesheet-monthly-fill.md`（列映射、取数边界、
不代填项、门禁判据都在那里）。本文件只实现该口径。

用法（先干跑，确认后再落盘）：
  python stats_to_timesheet.py --stats {统计表.xlsx} --template {上月工时表.xlsx} \\
      --month 10 --out {新工时表.xlsx} [--plan {项目计划表.xlsx}] [--apply]

--stats / --template / --plan 都是 B 类机器路径，脚本不设默认值。
不加 --apply 只打印摘要与落点，不改任何文件；加 --apply 才写出 --out（先写临时文件再替换）。
"""

import argparse
import datetime
import os
import re
import sys
from copy import copy

import openpyxl

STATS_MAX_COL = 34          # 统计表 A..AH
TS_COLS = 20                # 工时表 A..T
TS_FIRST_ROW = 8            # 工时表第 7 行是列名，数据从第 8 行起

# 统计表列位（固定 34 列）
S = {'A': 1, 'B': 2, 'D': 4, 'G': 7, 'H': 8, 'I': 9, 'K': 11, 'L': 12,
     'M': 13, 'N': 14, 'P': 16, 'Q': 17, 'R': 18, 'AA': 27, 'AB': 28}
# 工时表列位（20 列）
T = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
     'J': 10, 'K': 11, 'L': 12, 'M': 13, 'N': 14, 'O': 15, 'P': 16, 'Q': 17,
     'R': 18, 'S': 19, 'T': 20}

DEPT_OK = {'公司', '公司(注册)', '国贸', '外贸', '客服', '渠道', '跨境', '家购',
           '国电', '研发', '创新一部', '创新发展一部', '注册', '工程'}
REG_SUBJECT = {'益健堂', '元良', '康特瑞', '普莱', '泽生康'}
CAT_TYPE = {'订单': '订单', '注册送检': '注册', '注册体考': '注册', '注册样机': '注册',
            '新产品送检': '注册', '体考（未出报告）': '注册'}
STAGE_TYPE = {'注册': '注册', '小批量': '订单', '试产验证': '订单',
              '小批量测试V3BUG修复': '订单', '中试跟进': '样机', '送样': '样机',
              '开发阶段': '全新', '测试V1BUG修复': '全新', '测试V3BUG修复': '全新'}
INTERNAL = [('协调管理', '协调管理重难点跟进'), ('软著', '研发验证'),
            ('技术探索', '研发验证'), ('测试用例', '研发验证'), ('模板', '研发验证')]
PLAN_LABELS = {'pm': ('项目经理', '项目/经理'), 'dept': ('业务部门',), 'subject': ('注册主体',),
               'code': ('项目编码',), 'name': ('项目名称',), 'cat': ('类别',),
               'owner': ('责任人', '关联责任人', '负责人')}
EXCEL_EPOCH = datetime.date(1899, 12, 30)


# ------------------------------ 基础工具 ------------------------------

def norm(v):
    return re.sub(r'\s+', '', str(v or ''))


def clean_code(v):
    c = re.sub(r'\([^)]*\)', '', re.sub(r'（[^）]*）', '', norm(v)))
    return c.strip('/').strip()


def code_tokens(code):
    return [t for t in re.split(r'[^0-9A-Za-z]+', code) if len(t) >= 6]


def num(v):
    """工时文本 → 数值：'0,5'→0.5、'4+0.5'→4.5、'0.75 +0.2'→0.95、'1.1/'→1.1。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(' ', '').rstrip('/')
    if not s:
        return None
    s = re.sub(r'(\d),(\d)', r'\1.\2', s)
    if '+' in s:
        try:
            return round(sum(float(p) for p in s.split('+') if p), 2)
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def progress(v):
    if v in (None, ''):
        return None
    try:
        return round(float(str(v).replace('%', '').strip()) / 100, 2)
    except ValueError:
        return None


def month_day(v):
    if isinstance(v, (int, float)) and 40000 < v < 60000:
        d = EXCEL_EPOCH + datetime.timedelta(days=int(v))
        return (d.month, d.day)
    m = re.match(r'(\d{1,2})月(\d{1,2})日', str(v or ''))
    return (int(m.group(1)), int(m.group(2))) if m else None


# ------------------------------ 统计表取数 ------------------------------

def month_bounds(ws, month):
    """统计表中 '<month>月份' 分组行 → 下一个 '<x>月份' 分组行之前。"""
    start = None
    for r in range(1, ws.max_row + 1):
        if re.fullmatch(r'\d{1,2}月份', norm(ws.cell(r, 1).value)):
            if start is not None:
                return start, r
            if norm(ws.cell(r, 1).value) == f'{month}月份':
                start = r
    return start, ws.max_row + 1


def stats_tasks(ws, month):
    lo, hi = month_bounds(ws, month)
    if lo is None:
        raise AssertionError(f'统计表里找不到「{month}月份」分组行')
    out = []
    for r in range(lo + 1, hi):
        person = ws.cell(r, S['D']).value
        if not person:
            continue
        demand = str(ws.cell(r, S['I']).value or '')
        result = str(ws.cell(r, S['K']).value or '')
        in_block = True
        if demand.startswith(('09月', '9月')) and not result.startswith(f'{month}月'):
            continue                      # 上月结转、本月无结果
        if demand.startswith(('11月', '12月')) and month not in (11, 12):
            continue                      # 下月计划
        out.append({
            'person': str(person).strip(), 'row': r,
            'code': clean_code(ws.cell(r, S['A']).value),
            'name': str(ws.cell(r, S['B']).value or '').strip(),
            'task': str(ws.cell(r, S['H']).value or '').strip(),
            'done': str(ws.cell(r, S['Q']).value or '').strip(),
            'demand': demand, 'result': result,
            'prog': progress(ws.cell(r, S['P']).value),
            'stage': norm(ws.cell(r, S['G']).value),
            'real': num(ws.cell(r, S['L']).value),
            'est': num(ws.cell(r, S['N']).value),
            'ext': num(ws.cell(r, S['M']).value),
            'pm': str(ws.cell(r, S['AA']).value or '').strip(),
            'biz': norm(ws.cell(r, S['AB']).value),
            'note': str(ws.cell(r, S['R']).value or '').strip(),
            'in_block': in_block,
        })
    # 本月块之后、日期却属于本月的记录（实测有记录被错放到后面的月份段下）。
    # 块之前的同日期行属于上月段的记录，上月已按同事项报过，不再收。
    for r in range(hi, ws.max_row + 1):
        if not ws.cell(r, S['D']).value:
            continue
        demand = str(ws.cell(r, S['I']).value or '')
        result = str(ws.cell(r, S['K']).value or '')
        if not (demand.startswith(f'{month}月') or result.startswith(f'{month}月')):
            continue
        out.append({
            'person': str(ws.cell(r, S['D']).value).strip(), 'row': r,
            'code': clean_code(ws.cell(r, S['A']).value),
            'name': str(ws.cell(r, S['B']).value or '').strip(),
            'task': str(ws.cell(r, S['H']).value or '').strip(),
            'done': str(ws.cell(r, S['Q']).value or '').strip(),
            'demand': demand, 'result': result,
            'prog': progress(ws.cell(r, S['P']).value),
            'stage': norm(ws.cell(r, S['G']).value),
            'real': num(ws.cell(r, S['L']).value),
            'est': num(ws.cell(r, S['N']).value),
            'ext': num(ws.cell(r, S['M']).value),
            'pm': str(ws.cell(r, S['AA']).value or '').strip(),
            'biz': norm(ws.cell(r, S['AB']).value),
            'note': str(ws.cell(r, S['R']).value or '').strip(),
            'in_block': False,
        })
    return out


# ------------------------------ 计划表映射 ------------------------------

def plan_maps(plan_path, month):
    """计划表里本月与下月两个月份的 项目经理/业务部门/类别 映射（按表头文字取列）。"""
    if not plan_path:
        return {}, {}
    wb = openpyxl.load_workbook(plan_path, data_only=True)
    cur, nxt = {}, {}
    PLAN_SHEETS = ('项目计划分解', '项目交付目标', '项目目标')
    for ws in wb.worksheets:
        if ws.sheet_state != 'visible':
            continue
        if not any(k in ws.title for k in PLAN_SHEETS):
            continue                      # 延误记录等表标题里也可能带月份，必须排除
        is_cur = re.search(rf'(?<!\d){month}月', ws.title) is not None
        is_nxt = re.search(rf'(?<!\d){month + 1}月', ws.title) is not None
        if not (is_cur or is_nxt):
            continue
        target = cur if is_cur else nxt
        header = None
        for row in ws.iter_rows():
            labels = {norm(c.value): c.column for c in row if c.value not in (None, '')}
            # 每段的表头行都重新取一次列位（各段列序不同，类别列只在一部分段出现）
            if norm(row[0].value) in ('序号', '优先级') and '项目名称' in labels:
                header = {}
                for key, names in PLAN_LABELS.items():
                    for lab, col in labels.items():
                        if any(n in lab for n in names):
                            header[key] = col
                            break
                continue
            if not header:
                continue
            code = clean_code(row[header['code'] - 1].value) if 'code' in header else ''
            name = norm(row[header['name'] - 1].value) if 'name' in header else ''
            if not (code or name):
                continue
            rec = {}
            for key in ('pm', 'dept', 'subject', 'cat'):
                if key in header:
                    v = norm(row[header[key] - 1].value)
                    if v:
                        rec[key] = v
            if not rec:
                continue
            for k in ('code:' + code if code else '', 'name:' + name if name else ''):
                if k:
                    target.setdefault(k, {}).update(rec)
    return cur, nxt


def hist_maps(wb, month, sheets):
    """上月/上上月工时表 → 编号/名称 → (项目经理, 部门, 类型)；名称包含匹配取一致值。"""
    exact, names = {}, {}
    for sh in sheets:
        if sh not in wb.sheetnames:
            continue
        ws = wb[sh]
        for r in range(TS_FIRST_ROW, ws.max_row + 1):
            if not ws.cell(r, T['E']).value:
                continue
            rec = {'pm': norm(ws.cell(r, T['C']).value),
                   'dept': norm(ws.cell(r, T['F']).value),
                   'type': norm(ws.cell(r, T['G']).value)}
            code = clean_code(ws.cell(r, T['H']).value)
            name = norm(ws.cell(r, T['I']).value)
            if code:
                exact.setdefault('code:' + code, rec)
            if name:
                names.setdefault(name, rec)
    return exact, names


def fuzzy(names, text, key):
    hits = {rec[key] for n, rec in names.items()
            if rec.get(key) and len(n) >= 4 and (n in text or text in n)}
    return hits.pop() if len(hits) == 1 else None


# ------------------------------ 行组装 ------------------------------

def build_row(t, exact, names, cur_plan, nxt_plan):
    code, name, plain = t['code'], t['name'], norm(t['name'])
    keys = ([code] if code else []) + [plain]

    def pick(table, key):
        for k in keys:
            for pre in ('code:', 'name:'):
                if pre + k in table:
                    return table[pre + k].get(key)
        return None

    # 项目经理：统计表 AA → 上月同项目 → 本月计划 → 下月计划 → 注册类兜底
    pm = t['pm'] or pick(exact, 'pm') or fuzzy(names, plain, 'pm') \
        or pick(cur_plan, 'pm') or pick(nxt_plan, 'pm')
    # 所属业务部门：项目名自带注册主体 → 上月同项目 → 本月计划 → 下月计划 → 统计表部门词
    m = re.search(r'（(' + '|'.join(REG_SUBJECT) + r')）$', name)
    dept = m.group(1) if m else ''
    # 本月计划 > 下月计划 > 上月同项目（计划表是本月口径，历史只作兜底）
    for _tab in (cur_plan, nxt_plan):
        if dept:
            break
        v = pick(_tab, 'dept') or pick(_tab, 'subject')
        dept = v if (v in DEPT_OK or v in REG_SUBJECT) else ''
    for _v in (pick(exact, 'dept'), fuzzy(names, plain, 'dept')):
        if dept:
            break
        dept = _v if (_v in DEPT_OK or _v in REG_SUBJECT) else ''
    if not dept:
        hits = {v['dept'] for k, v in cur_plan.items() if k.startswith('name:')
                and v.get('dept') and len(k) >= 9 and (k[5:] in plain or plain in k[5:])}
        hits = {h for h in hits if h in DEPT_OK or h in REG_SUBJECT}
        dept = hits.pop() if len(hits) == 1 else ''
    if not dept and t['biz'] in DEPT_OK:
        dept = t['biz']
    if dept == '创新发展一部':
        dept = '创新一部'

    # 项目类型：上月同项目 → 本月/下月类别 → 注册主体/PM → 统计表阶段 → 内部事务
    ptype = pick(exact, 'type') or fuzzy(names, plain, 'type')
    if not ptype:
        cat = (pick(cur_plan, 'cat') or pick(nxt_plan, 'cat') or '')
        if cat in CAT_TYPE:
            ptype = CAT_TYPE[cat]
    if not ptype and (dept in REG_SUBJECT or pm == '黄雅萍'):
        ptype = '注册'
    if not ptype:
        for kw, val in INTERNAL:
            if kw in plain or kw in norm(t['task']):
                ptype = val
                break
    if not ptype and t['stage'] in STAGE_TYPE:
        ptype = STAGE_TYPE[t['stage']]
    if not pm and ptype == '注册':
        pm = '黄雅萍'

    delayed = bool((month_day(t['result']) and month_day(t['demand'])
                    and month_day(t['result']) > month_day(t['demand']))
                   or (t['prog'] is not None and t['prog'] < 1))

    return {
        'B': '', 'C': pm, 'D': '软件', 'E': t['person'], 'F': dept, 'G': ptype,
        'H': code, 'I': name, 'J': t['task'], 'K': t['done'], 'L': t['prog'],
        'M': t['est'] if t['est'] is not None else t['ext'],
        'N': t['real'], 'P': '有' if delayed else '无',
        'Q': t['note'] if delayed and t['note'] else '',
    }


# ------------------------------ 写入 ------------------------------

def write_timesheet(template_path, out_path, month, rows, person_order, apply=False):
    wb = openpyxl.load_workbook(template_path)
    sheet = f'{month}月'
    assert sheet in wb.sheetnames, f'模板里没有 {sheet} 页'
    ws = wb[sheet]
    # 模板样式参照：首个数据行、首个"小计"行（N 列是 SUM 公式的行）
    style_row = TS_FIRST_ROW
    sub_style_row = next((r for r in range(TS_FIRST_ROW, ws.max_row + 1)
                          if isinstance(ws.cell(r, T['N']).value, str)
                          and str(ws.cell(r, T['N']).value).startswith('=')), style_row)

    plan = []
    cur = TS_FIRST_ROW
    for person in person_order:
        block = [x for x in rows if x['E'] == person]
        if not block:
            continue
        first = cur
        for x in block:
            for c in range(1, TS_COLS + 1):
                ws.cell(cur, c)._style = copy(ws.cell(style_row, c)._style)
            for c in range(2, TS_COLS + 1):   # 序号列(A)保留模板原编号
                ws.cell(cur, c).value = None
            for col, val in x.items():
                if col == 'B':
                    ws.cell(cur, T['B']).value = f'{month}月'
                elif val not in (None, ''):
                    ws.cell(cur, T[col]).value = val
            if isinstance(x.get('M'), (int, float)) and x['M'] > 0:
                ws.cell(cur, T['O']).value = f'=M{cur}/7'   # 单位1标准数量 = 计划工时/7
                ws.cell(cur, T['O']).number_format = '0.0'
            cur += 1
        # 小计行
        for c in range(1, TS_COLS + 1):
            ws.cell(cur, c)._style = copy(ws.cell(sub_style_row, c)._style)
            ws.cell(cur, c).value = None
        ws.cell(cur, T['N']).value = f'=SUM(N{first}:N{cur - 1})'
        plan.append((person, len(block), first, cur - 1, cur))
        cur += 1
    # 清掉余下模板桩（只清数据区，序号列保留）
    for r in range(cur, ws.max_row + 1):
        for c in range(2, TS_COLS + 1):
            ws.cell(r, c).value = None
    wb.calculation.fullCalcOnLoad = True
    if not apply:
        return plan, wb, ws
    tmp = out_path + '.tmp.xlsx'
    wb.save(tmp)
    try:
        os.replace(tmp, out_path)
    except PermissionError:
        alt = out_path.replace('.xlsx', '_待替换.xlsx')
        os.replace(tmp, alt)
        print('!! 目标文件被占用，已另存为:', alt)
    return plan, wb, ws


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--stats', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--plan', help='项目计划表（可选，用于补项目经理/部门/类型）')
    ap.add_argument('--month', type=int, required=True)
    ap.add_argument('--out', help='输出文件；不给则只干跑')
    ap.add_argument('--apply', action='store_true', help='真正写出 --out')
    ap.add_argument('--stats-sheet', default='软件组789月交付数据')
    a = ap.parse_args(argv)

    sws = openpyxl.load_workbook(a.stats, data_only=True)[a.stats_sheet]
    tasks = stats_tasks(sws, a.month)
    cur_plan, nxt_plan = plan_maps(a.plan, a.month)

    twb = openpyxl.load_workbook(a.template, data_only=True)
    tpl_sheet = f'{a.month}月'
    tws = twb[tpl_sheet]
    person_order = []
    for r in range(TS_FIRST_ROW, tws.max_row + 1):
        p = tws.cell(r, T['E']).value
        if p and str(p).strip() not in person_order:
            person_order.append(str(p).strip())
    for t in tasks:
        if t['person'] not in person_order:
            person_order.append(t['person'])

    prev = [f'{a.month - 1}月', f'{a.month - 1:02d}月', f'{a.month - 2}月', f'{a.month - 2:02d}月']
    exact, names = hist_maps(twb, a.month, prev)
    rows = [build_row(t, exact, names, cur_plan, nxt_plan) for t in tasks]
    plan, wb, ws = write_timesheet(a.template, a.out or '', a.month, rows, person_order,
                                   apply=bool(a.apply and a.out))
    print(f'{a.month} 月：{len(rows)} 行，{len(plan)} 个人员块')
    for p in plan:
        print(f'  {p[0]:<4} {p[1]:>3} 行  {p[2]}-{p[3]}  小计行 {p[4]}')
    print('计划工时合计', round(sum(r['M'] for r in rows if isinstance(r['M'], (int, float))), 2),
          '| 实际工时合计', round(sum(r['N'] for r in rows if isinstance(r['N'], (int, float))), 2))
    print('未填项目经理 %d 行、未填部门 %d 行、未填类型 %d 行' % (
        sum(1 for r in rows if not r['C']), sum(1 for r in rows if not r['F']),
        sum(1 for r in rows if not r['G'])))
    if a.apply and a.out:
        print('已写出:', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
