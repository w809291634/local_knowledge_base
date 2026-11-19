# -*- coding: utf-8 -*-
"""人员清单门禁：内容性人员表必填，签署类字段按文档状态校验。

用法：
    python check_personnel.py <目录或文件> [更多文件...] [--status 草稿|受控发布]

判据（注册人 2026-11-19）：
1. 内容性人员表（表头含「姓名」）逐行非空；RD-052 必须存在该表，且职责列覆盖
   需求与设计／软件编程／黑盒测试／白盒测试／风险管理五类。
2. 签署类（「确认人员／测试人员／测试人」列、封面「编制／审核／批准」行、
   068/069/026 首行合并签署格、032「测试组：」段落）：草稿态允许留空，
   受控发布态必须填写；填了人员没填日期视为半填。
3. 跨文档同一测试角色姓名不一致 → 失败。

人员清单属 S1 开工前置事实（authoring-workflow-and-experience-index.md），
未取得名单时先索取，不得用「见受控的项目人员记录」配空白表交付。

状态取值：命令行 --status 优先；否则读目录 manifest.json 的 status/document_status；
都没有按「草稿」处理。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document

RELEASE = ("受控发布", "已发布", "released", "final")
SIGN_COLS = ("确认人员", "测试人员", "测试人")
AUDIT_COLS = ("审核", "作者", "批准")
COVER_LABELS = ("编制", "审核", "批准")
SIGN_LABELS = ("测试人员", "测试人")
ROLE_KEYS = (
    ("需求", "需求与设计"),
    ("设计", "需求与设计"),
    ("编程", "软件编程"),
    ("黑盒", "黑盒测试"),
    ("白盒", "白盒测试"),
    ("风险", "风险管理"),
)
ROLES = ("需求与设计", "软件编程", "黑盒测试", "白盒测试", "风险管理")


def parse_labels(text: str) -> dict:
    """把「标签：值」逐行拆开，兼容换行与 / 分隔。"""
    out = {}
    for part in re.split(r"[\n\r/／]+", text):
        for sep in ("：", ":"):
            if sep in part:
                key, val = part.split(sep, 1)
                out.setdefault(key.strip(), val.strip())
                break
    return out


def pick_name(text: str) -> str:
    """从「测试组：测试工程师 张三」取姓名（末尾非空词，去掉句末标点）。"""
    words = text.replace("：", " ").replace(":", " ").split()
    return words[-1].strip("。．.；;，,、（）() ") if words else ""


def row_text(row) -> list:
    return [c.text.strip() for c in row.cells]


def check_doc(path: Path, status: str):
    doc = Document(str(path))
    released = status in RELEASE
    errors, roles, names = [], {}, set()
    content_tables = 0

    for ti, table in enumerate(doc.tables):
        rows = table.rows
        if not rows:
            continue
        first = row_text(rows[0])

        # 1) 首行合并签署格（026 / 068 / 069）：测试人员／测试人 + 测试时间
        merged = first[0] if len(set(first)) == 1 else ""
        labels = parse_labels(merged) if merged else {}
        if any(k in labels for k in SIGN_LABELS):
            person = labels.get("测试人员") or labels.get("测试人") or ""
            when = labels.get("测试时间", "")
            if person:
                names.add(pick_name(person))
            if released and not person:
                errors.append("%s 表%d 首行「测试人员」为空" % (path.name, ti))
            if person and not when:
                errors.append("%s 表%d 首行填了测试人员但「测试时间」为空" % (path.name, ti))
            continue

        heads = first

        # 2) 内容性人员表（052 人员与职责表）：姓名逐行必填
        if "姓名" in heads:
            content_tables += 1
            j = heads.index("姓名")
            duty_j = next((i for i, h in enumerate(heads) if "职责" in h), None)
            for ri, row in enumerate(rows[1:], start=1):
                cells = row_text(row)
                if not any(cells):
                    continue
                # 职责阶段独立记录：姓名未填时也要能判「五类是否齐全」
                if duty_j is not None:
                    for key, role in ROLE_KEYS:
                        if key in cells[duty_j]:
                            roles[role] = cells[j]
                if not cells[j]:
                    errors.append("%s 表%d 行%d「姓名」为空" % (path.name, ti, ri))

        # 3) 签署类列（确认人员／测试人员／测试人）
        for col in SIGN_COLS:
            if col not in heads:
                continue
            j = heads.index(col)
            for ri, row in enumerate(rows[1:], start=1):
                cells = row_text(row)
                if any(cells) and released and not cells[j]:
                    errors.append("%s 表%d 行%d「%s」为空" % (path.name, ti, ri, col))

        # 4) 审计类列（030 修订记录）：只查有内容的行
        if any(c in heads for c in AUDIT_COLS):
            valid_j = next((i for i, h in enumerate(heads) if h in ("版次", "描述")), None)
            for ri, row in enumerate(rows[1:], start=1):
                cells = row_text(row)
                if not any(cells):
                    continue
                if valid_j is not None and not cells[valid_j]:
                    continue
                for col in AUDIT_COLS:
                    if col in heads and released and not cells[heads.index(col)]:
                        errors.append("%s 表%d 行%d「%s」为空" % (path.name, ti, ri, col))

        # 5) 封面签署行：编制／审核／批准 | 值 | 日期 | 值
        for ri, row in enumerate(rows):
            cells = row_text(row)
            if len(cells) >= 4 and cells[0] in COVER_LABELS and "日期" in cells[2]:
                if cells[1]:
                    names.add(pick_name(cells[1]))
                if released and not cells[1]:
                    errors.append("%s 表%d 行%d「%s」为空" % (path.name, ti, ri, cells[0]))
                if cells[1] and not cells[3]:
                    errors.append("%s 表%d 行%d「%s」填了签名但日期为空" % (path.name, ti, ri, cells[0]))

    # 6) 段落式人员（032「测试组：测试工程师 张三」）
    for i, para in enumerate(doc.paragraphs):
        m = re.match(r"^测试组[：:]\s*(.*)$", para.text.strip())
        if not m:
            continue
        person = m.group(1).strip()
        if person:
            names.add(pick_name(person))
            roles.setdefault("黑盒测试", pick_name(person))
        elif released:
            errors.append("%s 段落%d「测试组」为空" % (path.name, i))

    if path.name.startswith("RD-052"):
        if not content_tables:
            errors.append("%s 缺人员与职责表（表头需含「姓名」）" % path.name)
        else:
            missing = [r for r in ROLES if r not in roles]
            if missing:
                errors.append("%s 人员职责缺阶段：%s" % (path.name, "、".join(missing)))

    # 052 黑盒测试姓名参与跨文档一致性
    if roles.get("黑盒测试"):
        names.add(roles["黑盒测试"])
    return errors, names


def read_status(folder: Path, cli_status: str) -> str:
    if cli_status:
        return cli_status
    manifest = folder / "manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            return data.get("status") or data.get("document_status") or "草稿"
        except (OSError, ValueError):
            pass
    return "草稿"


def main(argv):
    cli_status, targets = "", []
    i = 0
    while i < len(argv):
        if argv[i] == "--status" and i + 1 < len(argv):
            cli_status = argv[i + 1]
            i += 2
            continue
        targets.append(argv[i])
        i += 1

    docs, folders = [], []
    for raw in targets:
        p = Path(raw)
        if p.is_dir():
            folders.append(p)
            docs += sorted(x for x in p.iterdir()
                           if x.suffix.lower() == ".docx" and x.name.startswith("RD-"))
        else:
            docs.append(p)
    if not docs:
        print("未找到待检文档")
        return 1

    status = read_status(folders[0], cli_status) if folders else (cli_status or "草稿")
    errors, all_names = [], set()
    for path in docs:
        try:
            errs, names = check_doc(path, status)
        except Exception as exc:  # 损坏/加密文件也按失败处理
            errors.append("%s 读取失败：%s" % (path.name, exc))
            continue
        errors += errs
        all_names |= names

    if len(all_names) > 1:
        errors.append("跨文档测试人员不一致：%s" % "、".join(sorted(all_names)))

    if errors:
        print("人员清单检查失败（状态：%s）：" % status)
        for e in errors:
            print("  -", e)
        return 1
    print("人员清单检查通过：%d 份（状态：%s）" % (len(docs), status))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
