#!/usr/bin/env bash
# 文档清点 —— 判定用例重建走哪条取证路径。
#
# 用法: bash inventory_docs.sh <repo-root>
#
# 为什么这一步不能省：用例的定义性要素是「对 Actor 有价值的可观察结果」
# （UML 2.5.1 §18.1.3.1），而 29148:2018 §6.3 说用例方法须识别 actor 的
# 「goals, purposes and needs」——价值与目标都不在代码里。
# 文档是目标层的唯一证据来源；档位由证据强度决定，不由文档有无决定
# （强证据 → 路径 A / 弱证据 → 路径 A− / 无证据 → 路径 B，见
# references/evidence-discipline.md 三）。

set -uo pipefail
ROOT="${1:-.}"
cd "$ROOT" 2>/dev/null || { echo "无法进入目录: $ROOT" >&2; exit 1; }

PRUNE_NAMES='node_modules target .git vendor dist build .venv __pycache__ .next .tox venv'
PRUNE=""
for n in $PRUNE_NAMES; do PRUNE="$PRUNE -name $n -o"; done
PRUNE="${PRUNE% -o}"

SECT_HIT=0

section() { SECT_HIT=0; printf '\n\033[1m%s\033[0m\n' "$1"; }

hit() { # hit <label> <maxdepth> <find-expr...>
  local label="$1"; shift
  local depth="$1"; shift
  local out
  out=$(find . -maxdepth "$depth" \( $PRUNE \) -prune -o \( "$@" \) -print 2>/dev/null \
        | head -8 | sed 's|^\./||' | paste -sd' ' -)
  if [ -n "$out" ]; then
    printf '  \033[32m✓\033[0m %-18s %s\n' "$label" "$out"
    SECT_HIT=1
  fi
}

fallback() {
  [ "$SECT_HIT" = 0 ] && printf '  \033[31m✗\033[0m %-18s %s\n' "$1" "$2"
  return 0
}

echo "════════════════════════════════════════════════════════════"
echo " 文档清点（目标层的唯一证据来源）: $(pwd)"
echo "════════════════════════════════════════════════════════════"

section "[1] 用户面文档 —— 目标的直接来源"
hit "README"         1 -iname 'readme*'
hit "用户手册"        3 -iname 'manual*' -o -iname 'user*guide*' -o -iname 'getting*started*' -o -iname 'tutorial*'
hit "docs 目录"       2 -name docs -type d -o -name doc -type d -o -name website -type d
fallback "用户面文档" "无 —— 用户目标无文字出处"
S1=$SECT_HIT

section "[2] 需求与用例痕迹 —— 最直接的证据"
hit "用例/需求文档"    4 -iname '*use*case*' -o -iname '*requirement*' -o -iname '*user*stor*' -o -iname '*spec*.md'
hit "UML/图"          4 -iname '*.puml' -o -iname '*.plantuml' -o -iname '*usecase*.svg' -o -iname '*usecase*.png'
hit "issue 模板"      3 -path '*.github/ISSUE_TEMPLATE*' -o -iname '*issue_template*'
fallback "需求痕迹"   "无"
S2=$SECT_HIT

section "[3] 行为契约 —— 场景的最硬证据"
# 29148 A.2.7 自陈场景「can serve as the basis for developing acceptance test plans」，此处反向使用
hit "BDD feature"    4 -name '*.feature' -o -name 'features' -type d
hit "e2e/验收测试"    3 -name 'e2e' -type d -o -name 'acceptance*' -type d -o -name 'integration*' -type d -o -name 'apptest' -type d
hit "API 契约"        4 -iname 'openapi*.y*ml' -o -iname 'swagger*.json' -o -name '*.proto' -o -name '*.graphql'
fallback "行为契约"   "无 —— 场景步骤只能从 happy path 代码反推"
S3=$SECT_HIT

section "[4] 变更叙述 —— 功能演进的旁证"
hit "CHANGELOG"      2 -iname 'changelog*' -o -iname 'CHANGES*' -o -iname 'NEWS*' -o -iname 'RELEASE*'
fallback "变更叙述"   "无"
S4=$SECT_HIT

section "[5] 判定"

CAT_HITS=$((S1 + S2 + S3 + S4))
printf '  命中文档类别: %s/4\n' "$CAT_HITS"

if [ "$S2" = 1 ] || [ "$S3" = 1 ]; then
  STRONG=""
  [ "$S2" = 1 ] && STRONG="section [2] 需求与用例痕迹"
  if [ "$S3" = 1 ]; then
    [ -n "$STRONG" ] && STRONG="$STRONG、section [3] 行为契约" || STRONG="section [3] 行为契约"
  fi
  printf '  \033[1m建议取证路径: 路径 A（强证据）\033[0m\n'
  printf '    → 从文档提取用户目标候选，再逐条用代码校验\n'
  printf '    → 代码不支持的剔除（尖锐发现 #1）；文档没记的补充（尖锐发现 #2）\n'
  printf '    → 目标层可标 inferred_high，须注明文字出处\n'
  printf '    → 强证据来自 %s\n' "$STRONG"
elif [ "$S1" = 1 ] || [ "$S4" = 1 ]; then
  printf '  \033[1m\033[36m建议取证路径: 路径 A−（弱证据）\033[0m\n'
  printf '    → 仅有用户面文档/变更叙述，无需求或行为契约证据\n'
  printf '    → 目标层只能标 inferred_medium\n'
  printf '    → 优先去找 e2e/BDD 测试与 API 契约来升档\n'
else
  printf '  \033[1m\033[33m建议取证路径: 路径 B（无证据）\033[0m\n'
  printf '    → 主证据换为公开 API 契约 + 测试用例\n'
  printf '    → 目标层只能标 inferred_low 或 gap\n'
  printf '    → \033[31m不要伪造目标层\033[0m\n'
fi

echo
echo "────────────────────────────────────────────────────────────"
echo " 下一步：把清点结果告知用户并请其补充仓库外材料"
echo " （内部 wiki、设计评审记录、产品文档）——"
echo " 这个确认点不能省：路径错了，目标层全是编的。"
echo "────────────────────────────────────────────────────────────"
