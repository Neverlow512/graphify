"""Regex-based smali extractor — produces nodes+edges matching the graphify schema."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_CLASS_RE: re.Pattern[str] = re.compile(
    r"^\.class\s+(?:(?:public|private|protected|abstract|final|interface|"
    r"enum|annotation|synthetic|bridge)\s+)*"
    r"(L[^;]+;)"
)
_SUPER_RE: re.Pattern[str] = re.compile(r"^\.super\s+(L[^;]+;)")
_IMPLEMENTS_RE: re.Pattern[str] = re.compile(r"^\.implements\s+(L[^;]+;)")
_FIELD_RE: re.Pattern[str] = re.compile(
    r"^\.field\s+(?:(?:public|private|protected|static|final|volatile|transient|synthetic|enum)\s+)*([\w$<>\-]+):(.*)"
)
# Matches any number of modifier tokens before the method name (last token before '(')
_METHOD_START_RE: re.Pattern[str] = re.compile(
    r"^\.method(?:\s+(?:public|private|protected|static|final|synchronized|"
    r"bridge|synthetic|abstract|native|strictfp|varargs|constructor|declared-synchronized))*"
    r"\s+([\w$<>\-]+)\(([^)]*)\)(.*)"
)
_METHOD_END_RE: re.Pattern[str] = re.compile(r"^\.end\s+method")

_INVOKE_RE: re.Pattern[str] = re.compile(
    r"^invoke-(?:virtual|direct|static|interface|super)"
    r"(?:/range)?\s+\{[^}]*\},\s*(\[+[BCDFIJSZ]|\[*L[^;]+;)->([\w$<>\-]+)\(([^)]*)\)(.*)"
)
_INVOKE_POLY_RE: re.Pattern[str] = re.compile(
    r"^invoke-polymorphic(?:/range)?\s+\{[^}]*\},\s*(\[+[BCDFIJSZ]|\[*L[^;]+;)->([\w$<>\-]+)\(([^)]*)\)(.*?),\s*\("
)
_INVOKE_CUSTOM_RE: re.Pattern[str] = re.compile(r"^invoke-custom\s+\{[^}]*\},\s*(\S+),\s*\(")

_IGET_RE: re.Pattern[str] = re.compile(
    r"^iget(?:-wide|-object|-boolean|-byte|-char|-short)?\s+\S+,\s*\S+,\s*(\[*L[^;]+;)->([\w$<>\-]+):(.*)"
)
_IPUT_RE: re.Pattern[str] = re.compile(
    r"^iput(?:-wide|-object|-boolean|-byte|-char|-short)?\s+\S+,\s*\S+,\s*(\[*L[^;]+;)->([\w$<>\-]+):(.*)"
)
_SGET_RE: re.Pattern[str] = re.compile(
    r"^sget(?:-wide|-object|-boolean|-byte|-char|-short)?\s+\S+,\s*(\[*L[^;]+;)->([\w$<>\-]+):(.*)"
)
_SPUT_RE: re.Pattern[str] = re.compile(
    r"^sput(?:-wide|-object|-boolean|-byte|-char|-short)?\s+\S+,\s*(\[*L[^;]+;)->([\w$<>\-]+):(.*)"
)

_EdgeFn = Callable[[str, str, str, int, str | None], None]
_StubFn = Callable[[str, str, str], None]


def _make_id(*parts: str) -> str:
    combined = "_".join(p.strip("_.") for p in parts if p)
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", combined)
    return cleaned.strip("_").lower()


def _descriptor_to_label(descriptor: str) -> str:
    s = descriptor.strip()
    if s.startswith("L") and s.endswith(";"):
        return s[1:-1].replace("/", ".")
    return s


def _outer_descriptor(descriptor: str) -> str | None:
    """Return the outer class descriptor if descriptor contains '$', else None."""
    label = _descriptor_to_label(descriptor)
    if "$" not in label:
        return None
    outer_label = label.rsplit("$", 1)[0]
    return "L" + outer_label.replace(".", "/") + ";"


def extract_smali(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc), "input_tokens": 0, "output_tokens": 0}

    str_path = str(path)
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()
    seen_edges: set[tuple[str, str, str, int]] = set()

    def _add_node(
        nid: str,
        label: str,
        line: int,
        kind: str,
        source_file: str = str_path,
    ) -> None:
        if nid not in seen_ids:
            seen_ids.add(nid)
            nodes.append({
                "id": nid,
                "label": label,
                "kind": kind,
                "file_type": "code",
                "source_file": source_file,
                "source_location": f"L{line}",
            })

    def _stub_node(nid: str, label: str, kind: str) -> None:
        if nid not in seen_ids:
            seen_ids.add(nid)
            nodes.append({
                "id": nid,
                "label": label,
                "kind": kind,
                "file_type": "code",
                "source_file": "",
                "source_location": "",
            })

    def _add_edge(
        src: str,
        tgt: str,
        relation: str,
        line: int,
        context: str | None = None,
    ) -> None:
        # smali deduplicates by (source, target, relation, line) rather than
        # (source, target, relation) because repeated calls at distinct bytecode
        # offsets are distinct runtime operations — unlike other graphify extractors
        # where duplicate call edges carry no additional structural information.
        key = (src, tgt, relation, line)
        if key in seen_edges:
            return
        seen_edges.add(key)
        edge: dict = {
            "source": src,
            "target": tgt,
            "relation": relation,
            "confidence": "EXTRACTED",
            "source_file": str_path,
            "source_location": f"L{line}",
            "weight": 1.0,
        }
        if context is not None:
            edge["context"] = context
        edges.append(edge)

    lines = raw.splitlines()

    method_bodies: list[tuple[str, str, list[tuple[int, str]]]] = []

    current_class_nid: str | None = None
    current_class_descriptor: str | None = None
    current_method_nid: str | None = None
    collecting_body: list[tuple[int, str]] = []
    in_method = False

    for lineno, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if stripped.startswith("#"):
            continue

        line = stripped.split("#", 1)[0].rstrip()
        if not line:
            continue

        if in_method:
            if _METHOD_END_RE.match(line):
                if current_method_nid and current_class_nid:
                    method_bodies.append((current_method_nid, current_class_nid, collecting_body))
                current_method_nid = None
                collecting_body = []
                in_method = False
            else:
                collecting_body.append((lineno, line))
            continue

        m = _CLASS_RE.match(line)
        if m:
            descriptor = m.group(1)
            current_class_descriptor = descriptor
            label = _descriptor_to_label(descriptor)
            nid = _make_id(label)
            current_class_nid = nid
            _add_node(nid, label, lineno, "class")

            outer_desc = _outer_descriptor(descriptor)
            if outer_desc:
                outer_label = _descriptor_to_label(outer_desc)
                outer_nid = _make_id(outer_label)
                _stub_node(outer_nid, outer_label, "class")
                _add_edge(outer_nid, nid, "contains", lineno)
            continue

        m = _SUPER_RE.match(line)
        if m and current_class_nid:
            descriptor = m.group(1)
            label = _descriptor_to_label(descriptor)
            tgt_nid = _make_id(label)
            _stub_node(tgt_nid, label, "class")
            _add_edge(current_class_nid, tgt_nid, "inherits", lineno)
            continue

        m = _IMPLEMENTS_RE.match(line)
        if m and current_class_nid:
            descriptor = m.group(1)
            label = _descriptor_to_label(descriptor)
            tgt_nid = _make_id(label)
            _stub_node(tgt_nid, label, "class")
            _add_edge(current_class_nid, tgt_nid, "implements", lineno)
            continue

        m = _FIELD_RE.match(line)
        if m and current_class_nid and current_class_descriptor:
            field_name = m.group(1)
            class_label = _descriptor_to_label(current_class_descriptor)
            field_label = f"{class_label}.{field_name}"
            field_nid = _make_id(class_label, field_name)
            _add_node(field_nid, field_label, lineno, "field")
            _add_edge(current_class_nid, field_nid, "contains", lineno)
            continue

        m = _METHOD_START_RE.match(line)
        if m and current_class_nid and current_class_descriptor:
            method_name = m.group(1)
            class_label = _descriptor_to_label(current_class_descriptor)
            method_label = f"{class_label}.{method_name}()"
            ns = "b" if "<" in method_name and ">" in method_name else "m"
            method_nid = _make_id(class_label, ns, method_name)
            _add_node(method_nid, method_label, lineno, "method")
            _add_edge(current_class_nid, method_nid, "contains", lineno)
            current_method_nid = method_nid
            collecting_body = []
            in_method = True
            continue

    for method_nid, class_nid, body_lines in method_bodies:
        for lineno, line in body_lines:
            _process_invoke(line, lineno, method_nid, _add_edge, _stub_node)
            _process_field_access(line, lineno, method_nid, _add_edge, _stub_node)

    return {"nodes": nodes, "edges": edges, "input_tokens": 0, "output_tokens": 0}


def _process_invoke(
    line: str,
    lineno: int,
    method_nid: str,
    add_edge: _EdgeFn,
    stub_node: _StubFn,
) -> None:
    m = _INVOKE_RE.match(line)
    if m:
        class_desc = m.group(1)
        mname = m.group(2)
        class_label = _descriptor_to_label(class_desc)
        ns = "b" if "<" in mname and ">" in mname else "m"
        tgt_nid = _make_id(class_label, ns, mname)
        method_label = f"{class_label}.{mname}()"
        stub_node(tgt_nid, method_label, "method")
        add_edge(method_nid, tgt_nid, "calls", lineno, "call")
        return

    m = _INVOKE_POLY_RE.match(line)
    if m:
        class_desc = m.group(1)
        mname = m.group(2)
        class_label = _descriptor_to_label(class_desc)
        ns = "b" if "<" in mname and ">" in mname else "m"
        tgt_nid = _make_id(class_label, ns, mname)
        method_label = f"{class_label}.{mname}()"
        stub_node(tgt_nid, method_label, "method")
        add_edge(method_nid, tgt_nid, "calls", lineno, "call")
        return

    # invoke-custom: target is a call site reference, not a resolved class->method
    m = _INVOKE_CUSTOM_RE.match(line)
    if m:
        call_site_ref = m.group(1)
        tgt_nid = _make_id("call_site", call_site_ref)
        stub_node(tgt_nid, call_site_ref, "method")
        add_edge(method_nid, tgt_nid, "calls", lineno, "call")


def _process_field_access(
    line: str,
    lineno: int,
    method_nid: str,
    add_edge: _EdgeFn,
    stub_node: _StubFn,
) -> None:
    m = _IGET_RE.match(line)
    if m:
        class_desc = m.group(1)
        field_name = m.group(2)
        class_label = _descriptor_to_label(class_desc)
        field_nid = _make_id(class_label, field_name)
        stub_node(field_nid, f"{class_label}.{field_name}", "field")
        add_edge(method_nid, field_nid, "reads", lineno, "read")
        return

    m = _SGET_RE.match(line)
    if m:
        class_desc = m.group(1)
        field_name = m.group(2)
        class_label = _descriptor_to_label(class_desc)
        field_nid = _make_id(class_label, field_name)
        stub_node(field_nid, f"{class_label}.{field_name}", "field")
        add_edge(method_nid, field_nid, "reads", lineno, "read")
        return

    m = _IPUT_RE.match(line)
    if m:
        class_desc = m.group(1)
        field_name = m.group(2)
        class_label = _descriptor_to_label(class_desc)
        field_nid = _make_id(class_label, field_name)
        stub_node(field_nid, f"{class_label}.{field_name}", "field")
        add_edge(method_nid, field_nid, "writes", lineno, "write")
        return

    m = _SPUT_RE.match(line)
    if m:
        class_desc = m.group(1)
        field_name = m.group(2)
        class_label = _descriptor_to_label(class_desc)
        field_nid = _make_id(class_label, field_name)
        stub_node(field_nid, f"{class_label}.{field_name}", "field")
        add_edge(method_nid, field_nid, "writes", lineno, "write")
