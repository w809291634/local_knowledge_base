#!/usr/bin/env bash
# launch.sh —— 按配置启动目标 Electron/Chromium 应用，并等待 CDP 调试端口就绪
#
# 用法：
#   bash launch.sh            # 启动（后台）+ 等端口
#   bash launch.sh --kill     # 只杀进程
#   bash launch.sh --status   # 只检查端口
#
# 参数全部取自配置文件的 runtime 段（exe / args / debug_port / unset_env / open_project_as_arg）。
# 配置文件查找顺序同 tools/kit.py：环境变量 UI_DEBUG_KIT_CONFIG → 向上找
# ui_debug_kit.config.json → 向上找 config.json。
#
# 关键坑（详见 PLAYBOOK §3.2）：
#   - 必须 --enable-unsafe-swiftshader（无 GPU 时软件渲染兜底）
#   - 绝不能加 --disable-software-rasterizer / --in-process-gpu
#   - 必须清掉 ELECTRON_RUN_AS_NODE，否则 Electron 退化为纯 Node

set -u
export PATH="/usr/bin:/bin:/usr/local/bin:/c/Windows/System32:/c/Windows:$PATH"

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="${PY:-python3}"

read_cfg() {
  "$PY" - "$@" <<'PYEOF'
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".", "x"))
try:
    import kit
    cfg = kit.load_config()
except Exception as e:
    sys.stderr.write("配置读取失败: %s\n" % e)
    sys.exit(2)
base = cfg["_abs"]["base"]
rt = cfg.get("runtime", {}) or {}
proj = cfg.get("project", {}) or {}
for k in sys.argv[1:]:
    if k == "exe":
        print(rt.get("exe", ""))
    elif k == "port":
        print(rt.get("debug_port", 9222))
    elif k == "unset":
        print(",".join(rt.get("unset_env", []) or []))
    elif k == "args":
        print("\x1f".join(rt.get("args", []) or []))
    elif k == "proj":
        pf = cfg["_abs"].get("project.project_file", "")
        print(pf if rt.get("open_project_as_arg") else "")
PYEOF
}

# 让 python 能找到 kit.py
export PYTHONPATH="$KIT/tools:${PYTHONPATH:-}"

kill_app() {
  local exe name
  exe="$(read_cfg exe)"; name="$(basename "$exe")"
  [ -z "$name" ] && return 0
  taskkill //F //IM "$name" >/dev/null 2>&1 || pkill -f "$name" >/dev/null 2>&1 || true
  sleep 1
}

case "${1:-}" in
  --kill)   kill_app; echo "killed"; exit 0 ;;
  --status)
    port="$(read_cfg port)"
    if curl -s --max-time 2 "http://127.0.0.1:$port/json/version" >/dev/null 2>&1; then
      echo "ready: http://127.0.0.1:$port"; exit 0
    fi
    echo "not ready"; exit 1 ;;
esac

EXE="$(read_cfg exe)"
PORT="$(read_cfg port)"
ARGS_RAW="$(read_cfg args)"
PROJ="$(read_cfg proj)"
UNSET="$(read_cfg unset)"

if [ -z "$EXE" ]; then
  echo "!! 配置里 runtime.exe 为空（见 CONFIG.md）"; exit 2
fi
if [ ! -f "$EXE" ] && [ ! -x "$EXE" ]; then
  echo "!! 找不到可执行文件: $EXE"; exit 2
fi

kill_app

CMD=(env)
IFS=',' read -ra _unset <<< "$UNSET"
for v in "${_unset[@]}"; do [ -n "$v" ] && CMD+=("-u" "$v"); done
CMD+=("$EXE" "--remote-debugging-port=$PORT")
IFS=$'\x1f' read -ra _args <<< "$ARGS_RAW"
for a in "${_args[@]}"; do [ -n "$a" ] && CMD+=("$a"); done
[ -n "$PROJ" ] && CMD+=("$PROJ")

echo "启动: ${CMD[*]}"
"${CMD[@]}" >/dev/null 2>&1 &

for i in $(seq 1 20); do
  if curl -s --max-time 1 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "端口就绪(${i}s)  http://127.0.0.1:$PORT"
    exit 0
  fi
  sleep 1
done
echo "!! 端口 $PORT 未就绪（进程可能已崩溃；见 PLAYBOOK §3.2 参数避坑表）"; exit 3
