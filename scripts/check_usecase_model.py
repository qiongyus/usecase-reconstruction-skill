#!/usr/bin/env python3
"""核对用例模型的机械约束，分 UML 组与 29148 组。

用法:
    python3 check_usecase_model.py <uc-dir-or-manifest>

读取 <uc-dir>/uc-manifest.yaml（或 .json），核对下列可机械判定的约束：

UML 2.5.1 §18 组（规范性 OCL 约束，§18.2.5.6）：
  1. must_have_name              —— 用例必须有名字
  2. cannot_include_self         —— include 不得直接或间接成环
  3. no_association_to_use_case  —— 同一 subject 的用例之间不得有关联
  4. binary_associations         —— 用例只参与二元关联（须关联至少一个 actor）
  5. 粒度纪律                     —— user_goal 级用例必须写出完整性判定理由（§18.1.3.1）
  6. 证据纪律                     —— 用例目标与 actor 目标不得标为 fact

29148:2018 组（见 check_29148 组，Task 3 实现）。

违规时退出码非零，可直接用于 CI。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 用例目标与 actor 目标恒为推断，fact 不在合法取值内
VALID_CONFIDENCE = {"inferred_high", "inferred_medium", "inferred_low", "gap"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def emit(self) -> int:
        for m in self.notes:
            print(f"  \033[36m·\033[0m {m}")
        for m in self.warnings:
            print(f"  \033[33m⚠\033[0m {m}")
        for m in self.errors:
            print(f"  \033[31m✗\033[0m {m}")
        print()
        if self.errors:
            print(f"\033[31m不合规：{len(self.errors)} 项违规，"
                  f"{len(self.warnings)} 项警告\033[0m")
            return 1
        if self.warnings:
            print(f"\033[33m基本合规：0 项违规，{len(self.warnings)} 项警告\033[0m")
            return 0
        print("\033[32m合规：全部约束通过\033[0m")
        return 0


def load_manifest(target: Path) -> dict:
    if target.is_dir():
        candidates = [target / "uc-manifest.yaml", target / "uc-manifest.yml",
                      target / "uc-manifest.json"]
        found = [c for c in candidates if c.exists()]
        if not found:
            sys.exit(f"在 {target} 下未找到 uc-manifest.yaml / .json\n"
                     f"可从 assets/uc-skeleton/uc-manifest.yaml 复制一份作为起点。")
        path = found[0]
    else:
        path = target
        if not path.exists():
            sys.exit(f"文件不存在: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        sys.exit("读取 YAML 需要 pyyaml（pip install pyyaml），"
                 "或把 manifest 改写为 uc-manifest.json。")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        sys.exit(f"{path} 顶层应是映射（mapping），实际是 {type(data).__name__}")
    return data


def ids(items: list, kind: str, rep: Report) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i, item in enumerate(items or []):
        if not isinstance(item, dict):
            rep.error(f"{kind}[{i}] 应是映射，实际是 {type(item).__name__}")
            continue
        _id = item.get("id")
        if not _id:
            rep.error(f"{kind}[{i}] 缺少 id 字段")
            continue
        if _id in out:
            rep.error(f"{kind} id 重复: {_id}")
        out[_id] = item
    return out


def _reaches(start: str, graph: dict[str, list[str]]) -> set[str]:
    """从 start 出发经 include 边可达的全部用例（不含 start 自身除非成环）。"""
    seen: set[str] = set()
    stack = list(graph.get(start, []))
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(graph.get(n, []))
    return seen


def check_uml(data: dict, rep: Report) -> dict:
    actors = ids(data.get("actors"), "actors", rep)
    use_cases = ids(data.get("use_cases"), "use_cases", rep)

    if not use_cases:
        rep.error("未声明任何 use case —— 用例模型为空")
    rep.note(f"规模：{len(actors)} actor / {len(use_cases)} 用例 "
             f"（user_goal {sum(1 for u in use_cases.values() if u.get('level') == 'user_goal')} / "
             f"subfunction {sum(1 for u in use_cases.values() if u.get('level') == 'subfunction')}）")

    include_graph = {u: (item.get("includes") or []) for u, item in use_cases.items()}

    for uc_id, uc in use_cases.items():
        # 约束 1：must_have_name（UML §18.2.5.6）
        if not (uc.get("name") or "").strip():
            rep.error(f"用例 '{uc_id}' 缺少 name —— 违反 UML must_have_name")
        else:
            # REQ-N03：用例名应动词开头。词性无法可靠判定，这里只用名词后缀做
            # 启发式——只能抓住 "Ingestion Of Data" 这类首词即名词的情况，
            # 抓不住 "Data Ingestion"（首词 Data 不带名词后缀）。故只给警告。
            first = uc["name"].strip().split()[0].lower()
            if first.endswith(("tion", "sion", "ment", "ance", "ence", "ity", "ness")):
                rep.warn(f"用例 '{uc_id}' 名称 '{uc['name']}' 疑似名词开头 —— "
                         f"用例名应动词开头（如 Ingest Data 而非 Ingestion Of Data）")

        # 约束 2：cannot_include_self
        for inc in include_graph[uc_id]:
            if inc not in use_cases:
                rep.error(f"用例 '{uc_id}' include 了未声明的用例 '{inc}'")
        if uc_id in _reaches(uc_id, include_graph):
            rep.error(f"用例 '{uc_id}' 直接或间接 include 了自身 —— "
                      f"违反 UML cannot_include_self")

        # 约束 3：no_association_to_use_case
        for assoc in uc.get("associations") or []:
            if assoc in use_cases:
                rep.error(f"用例 '{uc_id}' 与同一 subject 的用例 '{assoc}' 建立了关联 —— "
                          f"违反 UML no_association_to_use_case（每个用例各自描述对 "
                          f"subject 的一次完整使用）")

        # 约束 4：binary_associations —— 用例须关联 actor
        uc_actors = uc.get("actors") or []
        if not uc_actors:
            rep.error(f"用例 '{uc_id}' 未关联任何 actor")
        for a in uc_actors:
            if a not in actors:
                rep.error(f"用例 '{uc_id}' 关联了未声明的 actor '{a}'")

        # 约束 5：粒度纪律（UML §18.1.3.1 完整性判据）
        if uc.get("level") == "user_goal" and not (uc.get("completeness_check") or "").strip():
            rep.error(f"用例 '{uc_id}' 是 user_goal 级但缺少 completeness_check —— "
                      f"须写出「执行后 subject 是否可重新发起」的判定理由")

        # 约束 6：证据纪律
        gc = uc.get("goal_confidence")
        if gc == "fact":
            rep.error(f"用例 '{uc_id}' 的 goal_confidence 为 fact —— "
                      f"用例目标恒为推断，代码里只有入口点与执行路径")
        elif gc and gc not in VALID_CONFIDENCE:
            rep.error(f"用例 '{uc_id}' 的 goal_confidence '{gc}' 非法"
                      f"（取值：{'/'.join(sorted(VALID_CONFIDENCE))}）")
        elif not gc:
            rep.warn(f"用例 '{uc_id}' 未标注 goal_confidence")

        # 事实断言须有 file:line
        for ev in uc.get("evidence") or []:
            if not re.search(r"[^\s:]+:\d+", str(ev)):
                rep.warn(f"用例 '{uc_id}' 的证据 '{ev}' 不是 file:line 形式")

    for a_id, a in actors.items():
        conf = a.get("confidence")
        if conf == "fact":
            rep.error(f"actor '{a_id}' 的 confidence 为 fact —— "
                      f"UML §18.1.3.1：actor 是 role 而非实体，"
                      f"代码里只有物理接口，角色映射恒为推断")
        elif conf and conf not in VALID_CONFIDENCE:
            rep.error(f"actor '{a_id}' 的 confidence '{conf}' 非法")
        elif not conf:
            rep.warn(f"actor '{a_id}' 未标注 confidence")

    return {"actors": actors, "use_cases": use_cases}


def main() -> int:
    ap = argparse.ArgumentParser(description="核对用例模型的机械约束")
    ap.add_argument("target", type=Path, help="用例产出目录或 manifest 文件路径")
    args = ap.parse_args()

    data = load_manifest(args.target)
    rep = Report()
    print(f"核对用例模型: {args.target}\n")
    print("\033[1m[UML 2.5.1 §18 约束]\033[0m")
    check_uml(data, rep)
    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
