from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _labels(r):
    return [n["label"] for n in r["nodes"]]


def _relations(r):
    return {e["relation"] for e in r["edges"]}


def _edges_with_relation(r, *relations):
    return [e for e in r["edges"] if e["relation"] in relations]


def test_smali_no_error():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert "error" not in r


def test_smali_dispatch_registered():
    from graphify.extract import _DISPATCH
    assert ".smali" in _DISPATCH


def test_smali_detect_extension_registered():
    from graphify.detect import CODE_EXTENSIONS
    assert ".smali" in CODE_EXTENSIONS


def test_smali_finds_class():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert any("MainActivity" in lbl for lbl in _labels(r))


def test_smali_finds_methods():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    labels = _labels(r)
    assert any("onClick" in lbl for lbl in labels)
    assert any("getCount" in lbl for lbl in labels)
    assert any("logEvent" in lbl for lbl in labels)
    assert any("scheduleWork" in lbl for lbl in labels)


def test_smali_finds_fields():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    labels = _labels(r)
    assert any("count" in lbl for lbl in labels)
    assert any("TAG" in lbl for lbl in labels)


def test_smali_inherits_edge():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert "inherits" in _relations(r)


def test_smali_inherits_from_base():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    inherits = _edges_with_relation(r, "inherits")
    found = any("MainActivity" in node_by_id.get(e["source"], "") for e in inherits)
    assert found, "MainActivity should have an inherits edge"


def test_smali_implements_edge():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert "implements" in _relations(r)


def test_smali_calls_edge():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert "calls" in _relations(r)


def test_smali_reads_edge():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert "reads" in _relations(r)


def test_smali_writes_edge():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    assert "writes" in _relations(r)


def test_smali_all_edges_extracted():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    for e in r["edges"]:
        assert e.get("confidence") == "EXTRACTED", f"Expected EXTRACTED: {e}"


def test_smali_no_dangling_edges():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    node_ids = {n["id"] for n in r["nodes"]}
    within_file = {"contains", "method", "inherits", "implements", "calls", "reads", "writes"}
    for e in r["edges"]:
        assert e["source"] in node_ids, f"Dangling source: {e}"
        if e["relation"] in within_file:
            assert e["target"] in node_ids, f"Dangling target: {e}"


def test_smali_file_type_code():
    from graphify.extract import extract_smali
    r = extract_smali(FIXTURES / "sample.smali")
    for n in r["nodes"]:
        assert n.get("file_type") == "code", f"Expected file_type=code: {n}"
        kind = n.get("kind")
        assert kind in ("class", "method", "field"), f"Expected kind class|method|field: {n}"

    by_label = {n["label"]: n for n in r["nodes"]}
    assert by_label["com.example.MainActivity"]["kind"] == "class"
    assert by_label["com.example.MainActivity.onClick()"]["kind"] == "method"
    assert by_label["com.example.MainActivity.count"]["kind"] == "field"
    assert by_label["com.example.BaseActivity"]["kind"] == "class"
    assert by_label["com.example.WorkManager.enqueue()"]["kind"] == "method"
