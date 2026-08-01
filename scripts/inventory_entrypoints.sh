#!/usr/bin/env bash
# 入口点提取 —— Step 3 系统操作清单（事实层）的机械基础。
#
# 用法: bash inventory_entrypoints.sh <repo-root>
#
# 设计要点：本步只产出「可 file:line 指认的对外入口」，不做任何用例判断。
# 聚合成用例是 Step 4 的事，且必须用 UML §18.1.3.1 的完整性判据来做——
# 先事实后假说，这是对治粒度失控的结构性设计。

set -uo pipefail
ROOT="${1:-.}"
cd "$ROOT" 2>/dev/null || { echo "无法进入目录: $ROOT" >&2; exit 1; }

PRUNE_NAMES='node_modules target .git vendor dist build .venv __pycache__ .next .tox venv'
PRUNE=""
for n in $PRUNE_NAMES; do PRUNE="$PRUNE -name $n -o"; done
PRUNE="${PRUNE% -o}"

# grep --exclude-dir 列表由 PRUNE_NAMES 统一生成，避免和上面的 find 剪枝各写一份、
# 后续漏改其一（曾出现 grepct 独立硬编码、少了 .venv/__pycache__ 等导致噪音）。
EXCLUDE_DIRS=""
for n in $PRUNE_NAMES; do EXCLUDE_DIRS="$EXCLUDE_DIRS --exclude-dir=$n"; done

TOTAL=0

section() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# grepct <label> <pattern> <零命中提示> —— 统计并展示前若干命中，带 file:line；
# 零命中时打印 ✗ + 提示，不静默——沉默会让「工具漏了」和「确实没有」无法区分。
grepct() {
  local label="$1"; shift
  local pat="$1"; shift
  local note="$1"; shift
  local out n
  out=$(grep -rnE "$pat" --include='*.go' --include='*.py' --include='*.js' \
        --include='*.ts' --include='*.java' --include='*.rb' --include='*.rs' \
        --include='*.kt' --include='*.cs' --include='*.php' --include='*.proto' \
        $EXCLUDE_DIRS \
        . 2>/dev/null | head -200)
  n=$(printf '%s' "$out" | grep -c . || true)
  if [ "$n" -gt 0 ]; then
    printf '  \033[32m✓\033[0m %-16s %s 处\n' "$label" "$n"
    printf '%s' "$out" | head -3 | sed 's|^\./||' | sed 's|^|      |'
    TOTAL=$((TOTAL + n))
  else
    printf '  \033[31m✗\033[0m %-16s %s\n' "$label" "$note"
  fi
}

echo "════════════════════════════════════════════════════════════"
echo " 入口点清点（事实层）: $(pwd)"
echo "════════════════════════════════════════════════════════════"

section "[1] HTTP 路由 —— 最可靠的入口点证据"
grepct "路由注册" '\.(Get|Post|Put|Delete|Patch|Handle|HandleFunc|route|Route)\(|@(Get|Post|Put|Delete|Request)Mapping|app\.(get|post|put|delete)\(|@app\.route|router\.(get|post|put|delete)|case "/[A-Za-z0-9_/.:-]+":' \
  "无 —— 未发现 HTTP 路由注册"

section "[2] CLI 子命令"
grepct "子命令" 'cobra\.Command|argparse|clap::|@click\.command|commander|ArgumentParser|flag\.(String|Int|Bool)\(' \
  "无 —— 未发现 CLI 子命令入口"

section "[3] 消息消费者与定时任务"
grepct "消费者/定时" 'Subscribe\(|Consume\(|@KafkaListener|@Scheduled|cron\.|NewTicker\(|celery\.task|@task' \
  "无 —— 未发现消息消费者或定时任务"

section "[4] RPC / gRPC 服务方法"
grepct "RPC 方法" 'rpc [A-Z][A-Za-z]*\(|service [A-Z][A-Za-z]* \{' \
  "无 —— 未发现 RPC/gRPC 服务定义（已扫 .proto）"

section "[5] 库类项目的导出符号"
printf '  若上述各节均为空，本项目多半是库/工具类，走 B 档。\n'
printf '  \033[33m注意\033[0m：此处会退化为「列出所有导出符号」，噪音极大。\n'
printf '  必须用 UML §18.1.3.1 完整性判据筛：\n'
printf '    调用后 subject 是否处于「无待续输入、可重新发起」或错误态？\n'
printf '    是 → 候选入口；否（构造器 / getter / 纯工具函数）→ 不是。\n'
EXPORTED=$(grep -rnE '^func [A-Z]|^pub fn |^export (function|const|class)|^def [a-z_]+\(|^public [A-Za-z<>]+ [a-z]' \
  --include='*.go' --include='*.rs' --include='*.ts' --include='*.js' \
  --include='*.py' --include='*.java' \
  --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=target \
  --exclude-dir=.git --exclude-dir=test --exclude-dir=tests \
  . 2>/dev/null | wc -l | tr -d ' ')
printf '  导出符号总数: %s（未经筛选，不可直接当作用例）\n' "$EXPORTED"

section "[6] 规模评估"
SRC=$(find . \( $PRUNE \) -prune -o -type f \( \
  -name '*.go' -o -name '*.rs' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' \
  -o -name '*.py' -o -name '*.java' -o -name '*.kt' -o -name '*.rb' -o -name '*.php' \
  -o -name '*.cpp' -o -name '*.cc' -o -name '*.c' -o -name '*.h' -o -name '*.hpp' \
  -o -name '*.cs' -o -name '*.swift' -o -name '*.scala' -o -name '*.vue' -o -name '*.svelte' \
  \) -print 2>/dev/null | wc -l | tr -d ' ')
printf '  源文件数（已排除 vendor/生成目录）: %s\n' "$SRC"
printf '  可定位入口点数: %s\n' "$TOTAL"

if   [ "$SRC" -lt 150 ];  then TIER="速览档（单文件 USE-CASES.md）"
elif [ "$SRC" -lt 1500 ]; then TIER="标准档（UC-xx 系列 + uc-manifest.yaml）"
else                            TIER="完整档（标准档 + 追溯矩阵 + CI 检查）"
fi
printf '  \033[1m建议产出档位: %s\033[0m\n' "$TIER"

if [ "$SRC" -ge 1500 ]; then
  printf '\n  \033[33m⚠ 规模警戒\033[0m\n'
  printf '    大型多模块项目上用例遗漏是系统性的，不是偶发。\n'
  printf '    必须分模块推进，并强制声明覆盖率与未覆盖区域——\n'
  printf '    不允许对整个仓库笼统宣称「重建了用例模型」。\n'
fi

echo
echo "────────────────────────────────────────────────────────────"
echo " 下一步：本清单是 Step 3 的事实层产出，每条都要能 file:line 指认。"
echo " 不要在此步做用例判断——聚合是 Step 4 的事。"
echo "────────────────────────────────────────────────────────────"
