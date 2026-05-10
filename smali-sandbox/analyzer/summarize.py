"""Post-run analyzer: aggregates per-file parser results into summary.json and summary.md."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

_STUB_THRESHOLD = 0.80
_HIGH_CALL_THRESHOLD = 50


def _is_stub(node: dict) -> bool:
    return node.get("source_file") == "" and node.get("source_location") == ""


def _node_kind(node: dict) -> str:
    label: str = node.get("label", "")
    if label.endswith("()"):
        return "method"
    # Field labels are always "{class_label}.{field_name}" where field_name has no dots
    # or parens. Class labels may contain dots from package separators.
    # Known limitation: single-char obfuscated class names (e.g. "a.b") may be
    # misclassified as fields since their tail also starts lowercase.
    # Known limitation: PascalCase field names (e.g. Handler, Builder, Creator) cannot
    # be distinguished from class names by label alone. Only CONSTANT_CASE (TAG, MAX_SIZE)
    # and lowercase/special-start names are reliably classified as fields.
    # Field/class counts in summary.json are approximate for PascalCase member names.
    if "." in label:
        tail = label.rsplit(".", 1)[1]
        if "." not in tail and "(" not in tail:
            is_lower_start = tail and tail[0].islower()
            is_special_start = tail and tail[0] in ("$", "_", "<")
            is_constant_case = bool(re.match(r"^[A-Z][A-Z0-9_]*$", tail))
            if is_lower_start or is_special_start or is_constant_case:
                return "field"
    return "class"


def analyze(results: list[tuple[Path, dict]]) -> dict:
    """
    Aggregate parser results into a structured summary dict.

    Args:
        results: list of (smali_path, extract_smali_result) tuples.

    Returns:
        A dict with keys: totals, edge_distribution, flags.
    """
    totals: dict[str, int] = {
        "files": len(results),
        "errors": 0,
        "nodes_class": 0,
        "nodes_method": 0,
        "nodes_field": 0,
        "nodes_stub": 0,
        "nodes_total": 0,
        "edges_total": 0,
    }
    edge_dist: dict[str, int] = defaultdict(int)

    flags: dict[str, list] = {
        "errored_files": [],
        "zero_node_files": [],
        "silent_methods": [],
        "high_stub_ratio_files": [],
        "high_call_count_methods": [],
        "id_collisions": [],
    }

    for path, result in results:
        rel = str(path)

        if "error" in result:
            totals["errors"] += 1
            flags["errored_files"].append({"file": rel, "error": result["error"]})
            continue

        nodes: list[dict] = result.get("nodes", [])
        edges: list[dict] = result.get("edges", [])

        if not nodes:
            flags["zero_node_files"].append(rel)
            continue

        # detect ID collisions within a single file
        seen_ids: dict[str, str] = {}
        for node in nodes:
            nid = node["id"]
            label = node.get("label", "")
            if nid in seen_ids and seen_ids[nid] != label:
                flags["id_collisions"].append({
                    "file": rel,
                    "id": nid,
                    "labels": [seen_ids[nid], label],
                })
            seen_ids[nid] = label

        stub_count = sum(1 for n in nodes if _is_stub(n))
        defined_count = len(nodes) - stub_count

        totals["nodes_stub"] += stub_count
        totals["nodes_total"] += len(nodes)
        totals["edges_total"] += len(edges)

        for node in nodes:
            if _is_stub(node):
                continue
            kind = _node_kind(node)
            if kind == "class":
                totals["nodes_class"] += 1
            elif kind == "method":
                totals["nodes_method"] += 1
            elif kind == "field":
                totals["nodes_field"] += 1

        for edge in edges:
            edge_dist[edge.get("relation", "unknown")] += 1

        if defined_count > 0 and stub_count / len(nodes) > _STUB_THRESHOLD:
            flags["high_stub_ratio_files"].append({
                "file": rel,
                "stubs": stub_count,
                "defined": defined_count,
                "ratio": round(stub_count / len(nodes), 2),
            })

        # build outgoing edge count per method node
        method_ids = {n["id"] for n in nodes if not _is_stub(n) and _node_kind(n) == "method"}
        outgoing: dict[str, int] = defaultdict(int)
        for edge in edges:
            if edge.get("relation") in ("calls", "reads", "writes"):
                src = edge.get("source", "")
                if src in method_ids:
                    outgoing[src] += 1

        id_to_label = {n["id"]: n.get("label", n["id"]) for n in nodes}
        for mid in method_ids:
            count = outgoing.get(mid, 0)
            if count == 0:
                flags["silent_methods"].append({"file": rel, "method": id_to_label.get(mid, mid)})
            elif count > _HIGH_CALL_THRESHOLD:
                flags["high_call_count_methods"].append({
                    "file": rel,
                    "method": id_to_label.get(mid, mid),
                    "outgoing_edges": count,
                })

    totals["edges_calls"] = edge_dist.get("calls", 0)
    totals["edges_reads"] = edge_dist.get("reads", 0)
    totals["edges_writes"] = edge_dist.get("writes", 0)
    totals["edges_inherits"] = edge_dist.get("inherits", 0)
    totals["edges_implements"] = edge_dist.get("implements", 0)
    totals["edges_contains"] = edge_dist.get("contains", 0)

    return {
        "totals": totals,
        "edge_distribution": dict(edge_dist),
        "flags": flags,
    }


def _render_md(summary: dict, run_dir: Path) -> str:
    t = summary["totals"]
    flags = summary["flags"]

    lines: list[str] = []
    lines.append("# Parser Run Summary\n")
    lines.append(f"Output directory: `{run_dir}`\n")

    lines.append("## Overview\n")
    lines.append("| Metric | Count |")
    lines.append("| --- | --- |")
    lines.append(f"| Files processed | {t['files']} |")
    lines.append(f"| Errors | {t['errors']} |")
    lines.append(f"| Total nodes | {t['nodes_total']} |")
    lines.append(f"| &nbsp;&nbsp;Classes | {t['nodes_class']} |")
    lines.append(f"| &nbsp;&nbsp;Methods | {t['nodes_method']} |")
    lines.append(f"| &nbsp;&nbsp;Fields | {t['nodes_field']} |")
    lines.append(f"| &nbsp;&nbsp;Stubs (external) | {t['nodes_stub']} |")
    lines.append(f"| Total edges | {t['edges_total']} |")
    lines.append("")

    lines.append("## Edge Distribution\n")
    lines.append("| Relation | Count |")
    lines.append("| --- | --- |")
    for rel, count in sorted(summary["edge_distribution"].items(), key=lambda x: -x[1]):
        lines.append(f"| {rel} | {count} |")
    lines.append("")

    lines.append("## Flags\n")
    lines.append(
        "_Flagged items are candidates for manual review — not confirmed errors._\n"
    )

    def _section(title: str, items: list, renderer: object) -> None:
        lines.append(f"### {title} ({len(items)})\n")
        if not items:
            lines.append("None.\n")
            return
        if callable(renderer):
            for item in items:
                lines.append(renderer(item))
        lines.append("")

    _section(
        "Errored Files",
        flags["errored_files"],
        lambda x: f"- `{x['file']}` — {x['error']}",
    )
    _section(
        "Zero-Node Files",
        flags["zero_node_files"],
        lambda x: f"- `{x}`",
    )
    _section(
        "ID Collisions",
        flags["id_collisions"],
        lambda x: (
            f"- `{x['file']}` — id `{x['id']}` maps to both"
            f" `{x['labels'][0]}` and `{x['labels'][1]}`"
        ),
    )
    _section(
        f"High Stub Ratio Files (>{int(_STUB_THRESHOLD * 100)}% stubs)",
        flags["high_stub_ratio_files"],
        lambda x: (
            f"- `{x['file']}` — {x['stubs']} stubs / {x['defined']} defined"
            f" ({int(x['ratio']*100)}%)"
        ),
    )
    _section(
        f"High Call Count Methods (>{_HIGH_CALL_THRESHOLD} outgoing edges)",
        flags["high_call_count_methods"],
        lambda x: f"- `{x['method']}` in `{x['file']}` — {x['outgoing_edges']} edges",
    )
    _section(
        "Silent Methods (0 outgoing call/read/write edges)",
        flags["silent_methods"],
        lambda x: f"- `{x['method']}` in `{x['file']}`",
    )

    return "\n".join(lines) + "\n"


def write_summary(results: list[tuple[Path, dict]], run_dir: Path) -> None:
    """Write summary.json and summary.md into run_dir."""
    summary = analyze(results)

    json_path = run_dir / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_path = run_dir / "summary.md"
    md_path.write_text(_render_md(summary, run_dir), encoding="utf-8")

    errors = summary["totals"]["errors"]
    collisions = len(summary["flags"]["id_collisions"])
    print(
        f"Summary written to {run_dir} "
        f"(errors: {errors}, id_collisions: {collisions})"
    )
