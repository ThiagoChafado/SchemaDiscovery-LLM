import os
import json
import csv
from collections.abc import Mapping, Sequence

DATASET_DIR = "processed"
MANIFEST_FILE = "manifest.csv"

"""
Analisa a complexidade dos arquivos JSON em um diretório e gera um manifesto CSV.
Métricas de complexidade:
- Número de chaves
- Profundidade máxima
- Número de arrays
- Tamanho em bytes
- Complexidade geral (baixa/alta) baseada em thresholds 

"""


def analyze_json(obj):
    """Analisa métricas de complexidade de um JSON."""

    def walk(o, depth=1):
        if isinstance(o, Mapping):
            nested = [walk(v, depth+1) for v in o.values()]
            return {
                "keys": len(o) + sum(n["keys"] for n in nested),
                "depth": max([depth] + [n["depth"] for n in nested]),
                "arrays": sum(n["arrays"] for n in nested),
                "array_len": sum(n["array_len"] for n in nested),
            }
        elif isinstance(o, Sequence) and not isinstance(o, str):
            nested = [walk(v, depth+1) for v in o]
            return {
                "keys": sum(n["keys"] for n in nested),
                "depth": max([depth] + [n["depth"] for n in nested]),
                "arrays": 1 + sum(n["arrays"] for n in nested),
                "array_len": len(o) + sum(n["array_len"] for n in nested),
            }
        else:
            return {"keys": 0, "depth": depth, "arrays": 0, "array_len": 0}

    stats = walk(obj)
    size_bytes = len(json.dumps(obj, ensure_ascii=False))

    # thresholds de complexidade
    if stats["depth"] > 3 or stats["keys"] > 100 or size_bytes > 30_000:
        level = "high"
    else:
        level = "low"

    return {
        "complexity": level,
        "keys": stats["keys"],
        "depth": stats["depth"],
        "arrays": stats["arrays"],
        "array_len": stats["array_len"],
        "size_bytes": size_bytes,
    }


def build_manifest():
    rows = []

    for root, _, files in os.walk(DATASET_DIR):
        for fname in files:
            if fname.endswith(".json"):
                fpath = os.path.join(root, fname)
                object_type = os.path.basename(root)  # pega nome do diretório pai

                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        obj = json.load(f)
                    stats = analyze_json(obj)
                except Exception as e:
                    print(f"[ERRO] Não consegui processar {fpath}: {e}")
                    continue

                row = {
                    "file": fpath,
                    "object_type": object_type,
                    **stats,
                    "schema_generated": False
                }
                rows.append(row)

    # grava CSV
    with open(MANIFEST_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "file",
            "object_type",
            "complexity",
            "keys",
            "depth",
            "arrays",
            "array_len",
            "size_bytes",
            "schema_generated"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Manifesto criado em: {MANIFEST_FILE}")


if __name__ == "__main__":
    build_manifest()
