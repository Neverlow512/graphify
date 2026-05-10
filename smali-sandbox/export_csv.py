"""Export graph.json to nodes.csv + edges.csv for Cosmograph."""

import csv
import json
import sys
from pathlib import Path


def export(graph_path: Path) -> None:
    out_dir = graph_path.parent
    g = json.loads(graph_path.read_text())

    nodes_path = out_dir / "nodes.csv"
    edges_path = out_dir / "edges.csv"

    with nodes_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "label", "file_type", "community", "source_file", "source_location"])
        for n in g["nodes"]:
            w.writerow([
                n.get("id", ""),
                n.get("label", ""),
                n.get("file_type", ""),
                n.get("community", ""),
                n.get("source_file", ""),
                n.get("source_location", ""),
            ])

    with edges_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "relation", "source_file", "source_location"])
        for e in g["links"]:
            w.writerow([
                e.get("source", ""),
                e.get("target", ""),
                e.get("relation", ""),
                e.get("source_file", ""),
                e.get("source_location", ""),
            ])

    print(f"nodes : {nodes_path} ({len(g['nodes']):,})")
    print(f"edges : {edges_path} ({len(g['links']):,})")
    print()
    print("Cosmograph usage:")
    print("  1. Go to https://cosmograph.app")
    print("  2. Click 'Open file' and upload nodes.csv — set 'id' as the node ID column")
    print("  3. Upload edges.csv — set 'source' / 'target' as the link columns")
    print("  4. Colour by 'community', size by degree")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("graphify-out/graph.json")
    if not path.exists():
        print(f"error: {path} not found")
        sys.exit(1)
    export(path)
