# -*- coding: utf-8 -*-
"""
run_gate.py —— UI 改完必跑的一键门禁（L1 层，纯 Python，秒级）

一次跑完所有闸门，任何一个 ERROR 就返回非 0（可直接接进 git pre-commit）。

闸门来源分两类，这样工具箱本身能保持"零工程痕迹"：

  · 内置闸门（工具箱自带，与框架无关）
      G1  audit_ui.py   回归断言集：把踩过的坑固化成断言（字体/边距/重叠/开关/链路）
      G4  tree_check.py 通用体检：几何越界 / 文本折行 / 字体缺失 / 死链 / 入口页

  · 工程侧闸门（由配置 checks.gates 挂载，脚本留在你自己的工程里）
      任意条，例如 G2 跳转体检、G3 命中仿真。脚本不存在就 SKIP，不阻断。

用法：
    python run_gate.py               # 全跑
    python run_gate.py --quick       # 只跑 G1 + 配置里标了 quick 的项
    python run_gate.py --skip-tree   # 跳过 G4（tree_check 需要 Pillow）
    python run_gate.py --gen-clicks out.txt  # 顺带生成 L2 真点击用例
退出码：0 = 全绿；1 = 有阻断项
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# 内置闸门：(编号, 标题, 脚本, 是否需要 Pillow)
BUILTIN = [
    ("G1", "回归断言", "audit_ui.py", False),
    ("G4", "通用体检", "tree_check.py", True),
]


def pick_python(cfg, need_pil):
    """选解释器：需要 Pillow 时优先用配置里的 venv（那里通常才装了依赖）。"""
    b = cfg.get("binaries", {}) or {}
    if need_pil:
        for key in ("python_venv", "python"):
            p = b.get(key)
            if p and os.path.exists(p):
                return p
    p = b.get("python")
    if p and os.path.exists(p):
        return p
    return sys.executable


def gates_of(cfg):
    """工程侧扩展闸门（配置 checks.gates）。"""
    out = []
    base = cfg["_abs"]["base"]
    for g in ((cfg.get("checks") or {}).get("gates") or []):
        if not isinstance(g, dict) or not g.get("script"):
            continue
        p = g["script"]
        if not os.path.isabs(p):
            p = os.path.normpath(os.path.join(base, p))
        out.append({"code": g.get("code", "GX"), "title": g.get("title", "自定义"),
                    "path": p, "quick": bool(g.get("quick")),
                    "need_pil": bool(g.get("need_pil"))})
    return out


def run_one(cfg, code, title, path, need_pil, cwd):
    if not os.path.isfile(path):
        return {"code": code, "title": title, "path": path,
                "status": "SKIP", "rc": None, "text": "脚本不存在: %s" % path}
    try:
        r = subprocess.run([pick_python(cfg, need_pil), path],
                           cwd=cwd, capture_output=True, timeout=300)
    except Exception as e:
        return {"code": code, "title": title, "path": path,
                "status": "FAIL", "rc": None, "text": "执行异常: %s" % e}
    out = (r.stdout or b"") + (r.stderr or b"")
    return {"code": code, "title": title, "path": path,
            "status": "PASS" if r.returncode == 0 else "FAIL",
            "rc": r.returncode, "text": out.decode("utf-8", errors="replace")}


def main():
    ap = argparse.ArgumentParser(description="UI 一键门禁")
    ap.add_argument("--quick", action="store_true", help="只跑 G1 + 配置里标 quick 的项")
    ap.add_argument("--skip-tree", action="store_true", help="跳过 G4")
    ap.add_argument("--config", help="指定配置文件")
    ap.add_argument("--gen-clicks", help="顺带生成 L2 真点击用例到该文件")
    args = ap.parse_args()

    cfg = kit.load_config(args.config)
    base = cfg["_abs"]["base"]

    plan = []
    for code, title, script, pil in BUILTIN:
        if args.skip_tree and code == "G4":
            continue
        if args.quick and code != "G1":
            continue
        plan.append((code, title, os.path.join(HERE, script), pil))
    for g in gates_of(cfg):
        if args.quick and not g["quick"]:
            continue
        plan.append((g["code"], g["title"], g["path"], g["need_pil"]))

    print("=" * 72)
    print("UI 门禁：%d 组   [%s]" % (len(plan), cfg["_abs"]["_config_path"]))
    print("=" * 72)

    results = []
    for code, title, path, pil in plan:
        r = run_one(cfg, code, title, path, pil, base)
        results.append(r)
        print("  %-3s %-8s %s" % (r["code"], r["title"], r["status"]))

    print("-" * 72)
    failed = [r for r in results if r["status"] == "FAIL"]
    for r in results:
        print("  %-3s %-8s %-10s %s" % (r["code"], r["title"], r["status"],
                                        os.path.basename(r["path"])))
    print("-" * 72)

    if args.gen_clicks:
        rc = subprocess.run([pick_python(cfg, False), os.path.join(HERE, "gen_clicks.py"),
                             "-o", args.gen_clicks, "--config", cfg["_abs"]["_config_path"]],
                            cwd=base, capture_output=True)
        for stream in (rc.stdout, rc.stderr):
            t = (stream or b"").decode("utf-8", errors="replace").strip()
            if t:
                print("  " + t)

    if failed:
        print("  阻断项：%s" % ", ".join(r["code"] for r in failed))
        print("  下面逐项打印失败详情：\n")
        for r in failed:
            print("#" * 72)
            print("# %s %s —— %s" % (r["code"], r["title"], r["path"]))
            print("#" * 72)
            print(r["text"])
        return 1

    print("  全部通过。可以进入 L2（仿真器真点击）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
