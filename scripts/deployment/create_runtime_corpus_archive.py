"""Cria um arquivo com os artefatos de corpus necessarios em producao."""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT_DIR / "runtime_artifacts" / "solabot-runtime-corpus.tar.gz"
REQUIRED_PATHS = [
    ROOT_DIR / "corpus" / "processed" / "chunks" / "alliance" / "all_chunks_for_embeddings.jsonl",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "alliance",
    ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json",
    ROOT_DIR / "corpus" / "raw" / "normative_manifest.json",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Empacota chunks, manifestos e indice Chroma para upload ao disco persistente."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path.relative_to(ROOT_DIR)}" for path in missing)
        raise SystemExit(f"Artefatos obrigatorios ausentes:\n{missing_list}")

    output = args.output if args.output.is_absolute() else ROOT_DIR / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(output, "w:gz") as archive:
        for path in REQUIRED_PATHS:
            archive.add(path, arcname=path.relative_to(ROOT_DIR))

    print(output)


if __name__ == "__main__":
    main()
