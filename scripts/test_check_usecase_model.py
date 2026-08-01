import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from check_usecase_model import Report, check_uml, load_manifest


def base():
    """一份最小的合规 manifest。"""
    return {
        "subject": {"name": "S", "boundary": "b", "evidence": "m.go:1"},
        "evidence_path": "doc",
        "actors": [{"id": "a1", "name": "A1", "kind": "human",
                    "goal": "g", "confidence": "inferred_high",
                    "evidence": ["m.go:2"]}],
        "use_cases": [{"id": "UC-01", "name": "Ingest Data",
                       "level": "user_goal", "actors": ["a1"],
                       "completeness_check": "返回后可再次发起",
                       "goal_confidence": "inferred_high",
                       "evidence": ["m.go:3"], "includes": [], "extends": []}],
        "operational_modes": ["normal"],
        "user_classes": ["a1"],
    }


def run(data):
    rep = Report()
    check_uml(data, rep)
    return rep


def test_clean_manifest_has_no_errors():
    assert run(base()).errors == []


def test_must_have_name():
    d = base()
    d["use_cases"][0]["name"] = ""
    assert any("must_have_name" in e for e in run(d).errors)


def test_cannot_include_self_direct():
    d = base()
    d["use_cases"][0]["includes"] = ["UC-01"]
    assert any("cannot_include_self" in e for e in run(d).errors)


def test_cannot_include_self_indirect():
    d = base()
    d["use_cases"][0]["includes"] = ["UC-02"]
    d["use_cases"].append({"id": "UC-02", "name": "Sub Step",
                           "level": "subfunction", "actors": ["a1"],
                           "goal_confidence": "inferred_low",
                           "evidence": ["m.go:4"], "includes": ["UC-01"],
                           "extends": []})
    assert any("cannot_include_self" in e for e in run(d).errors)


def test_no_association_to_use_case():
    """UML §18.2.5.6：同一 subject 的用例之间不得有关联。"""
    d = base()
    d["use_cases"][0]["associations"] = ["UC-02"]
    d["use_cases"].append({"id": "UC-02", "name": "Query Data",
                           "level": "user_goal", "actors": ["a1"],
                           "completeness_check": "同上",
                           "goal_confidence": "inferred_high",
                           "evidence": ["m.go:5"], "includes": [], "extends": []})
    assert any("no_association_to_use_case" in e for e in run(d).errors)


def test_goal_confidence_must_not_be_fact():
    """核心纪律：用例目标恒为推断。"""
    d = base()
    d["use_cases"][0]["goal_confidence"] = "fact"
    assert any("goal_confidence" in e and "fact" in e for e in run(d).errors)


def test_actor_confidence_must_not_be_fact():
    d = base()
    d["actors"][0]["confidence"] = "fact"
    assert any("confidence" in e and "fact" in e for e in run(d).errors)


def test_user_goal_requires_completeness_check():
    """粒度判据：user_goal 级用例必须写出完整性判定理由。"""
    d = base()
    del d["use_cases"][0]["completeness_check"]
    assert any("completeness_check" in e for e in run(d).errors)


def test_unknown_actor_reference():
    d = base()
    d["use_cases"][0]["actors"] = ["ghost"]
    assert any("ghost" in e for e in run(d).errors)


def test_use_case_without_actor():
    d = base()
    d["use_cases"][0]["actors"] = []
    assert any("UC-01" in e and "actor" in e for e in run(d).errors)


def test_verb_first_naming_warns():
    """REQ-N03：用例名应动词开头。启发式只看首词后缀，故给警告而非错误。"""
    d = base()
    d["use_cases"][0]["name"] = "Ingestion Of Data"
    assert any("动词" in w for w in run(d).warnings)


def test_verb_first_naming_accepts_verb():
    d = base()
    d["use_cases"][0]["name"] = "Ingest Data"
    assert not any("动词" in w for w in run(d).warnings)


def test_load_manifest_json_top_level_list_exits_cleanly(tmp_path):
    """畸形 .json（顶层非映射）须干净地 sys.exit，而不是抛未捕获的 AttributeError。"""
    p = tmp_path / "uc-manifest.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        load_manifest(p)
    assert "顶层应是映射" in str(exc.value)


def test_load_manifest_yaml_top_level_list_exits_cleanly(tmp_path):
    """与 .json 分支平行的 .yaml 用例，确认两种格式行为一致。"""
    p = tmp_path / "uc-manifest.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        load_manifest(p)
    assert "顶层应是映射" in str(exc.value)
