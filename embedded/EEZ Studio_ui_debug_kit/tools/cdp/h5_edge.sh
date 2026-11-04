#!/usr/bin/env bash
# h5_edge.sh —— 起/停一个无头 Edge，专门验纯 HTML 评审页（真实视口）
#
# 用法：
#   bash tools/cdp/h5_edge.sh <profile目录> [file:///页面.html] [--port 9333] [--size 1700,1050]
#   bash tools/cdp/h5_edge.sh <profile目录> --kill
#
# 为什么单独一个脚本（2026-11-04 w78 实测，PR-0442）：
#   - Desktop 内嵌 Browser 没有可见窗口时 innerWidth/innerHeight = 0，
#     所有几何断言（卡片宽、scrollLeft、浮层位置）都会量成假值。
#   - 关掉起它的那个 Bash 任务 ≠ 关掉浏览器：msedge 是独立进程树，
#     子进程仍锁着 profile，`rm -rf` 报一堆 "Device or resource busy"。
#     所以 --kill 按 profile 路径找根进程再递归杀整棵树，且只杀匹配这台 profile 的。
#   - profile 目录请放工程 tmp/ 下（过程件），别放工程外。

set -u
export PATH="/usr/bin:/bin:/usr/local/bin:/c/Windows/System32:/c/Windows:$PATH"

PROF="${1:-}"
[ -z "$PROF" ] && { echo "用法: bash h5_edge.sh <profile目录> [url] [--kill]"; exit 2; }
shift

PORT=9333
SIZE=1700,1050
URL=""
KILL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --kill) KILL=1 ;;
    --port) PORT="$2"; shift ;;
    --size) SIZE="$2"; shift ;;
    file://*) URL="$1" ;;
    *) [ -z "$URL" ] && URL="$1" ;;
  esac
  shift
done

EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
[ -f "$EDGE" ] || EDGE="/c/Program Files/Microsoft/Edge/Application/msedge.exe"
[ -f "$EDGE" ] || { echo "!! 找不到 msedge.exe（这台机器换浏览器就改这里）"; exit 2; }

# profile 的目录名，用来在命令行里认自己的进程（只杀这台，不碰用户浏览器）
TAG="$(basename "$(cd "$(dirname "$PROF")" 2>/dev/null && pwd -W 2>/dev/null || echo "$PROF")")/$(basename "$PROF")"

kill_tree() {
  cat > "$PROF/.kill.ps1" <<PS1
\$root = Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
         Where-Object { \$_.CommandLine -match [regex]::Escape('$TAG') } |
         Select-Object -ExpandProperty ProcessId
\$all = @(); \$queue = @(\$root)
while (\$queue.Count -gt 0) {
  \$p = \$queue[0]; \$queue = @(\$queue[1..(\$queue.Count - 1)]) | Where-Object { \$_ }
  if (\$all -contains \$p) { continue }
  \$all += \$p
  \$kids = Get-CimInstance Win32_Process -Filter "ParentProcessId=\$p" |
          Where-Object { \$_.Name -eq 'msedge.exe' } | Select-Object -ExpandProperty ProcessId
  \$queue += @(\$kids)
}
foreach (\$x in \$all) { try { Stop-Process -Id \$x -Force -ErrorAction Stop } catch {} }
Write-Output "tree_killed=\$(\$all.Count)"
PS1
  MSYS_NO_PATHCONV=1 powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PROF/.kill.ps1" 2>/dev/null || echo "$PROF/.kill.ps1")"
  rm -f "$PROF/.kill.ps1"
  sleep 2
  rm -rf "$PROF" 2>/dev/null && echo "profile 已清理: $PROF"
}

if [ "$KILL" = 1 ]; then kill_tree; exit 0; fi

mkdir -p "$PROF"
"$EDGE" --headless=new --disable-gpu --hide-scrollbars \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$(pwd -W)/$PROF" \
  --window-size="$SIZE" \
  "${URL:-about:blank}" >/dev/null 2>&1 &

for i in $(seq 1 15); do
  if curl -s --max-time 1 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "就绪(${i}s) http://127.0.0.1:$PORT  profile=$PROF"
    echo "验完收尾： bash tools/cdp/h5_edge.sh $PROF --kill"
    exit 0
  fi
  sleep 1
done
echo "!! 端口 $PORT 未就绪"; exit 3
