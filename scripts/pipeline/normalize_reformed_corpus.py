"""Script-base para normalização mecânica do corpus reformado extraído."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT_DIR / "corpus" / "processed" / "extracted"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "corpus" / "processed" / "normalized"


def normalize_mechanical_text(text: str) -> str:
    """Aplica limpeza mecânica sem alterar conteúdo doutrinário."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normaliza o campo textual de um registro extraído."""
    normalized = dict(record)
    normalized["text"] = normalize_mechanical_text(record.get("text", ""))
    return normalized


def normalize_jsonl_file(input_path: Path, output_dir: Path) -> Path:
    """Normaliza um arquivo JSONL de páginas extraídas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / input_path.name.replace(".pages.jsonl", ".normalized_pages.jsonl")

    with input_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            target.write(json.dumps(normalize_record(record), ensure_ascii=False) + "\n")

    return output_path


def run_normalization(input_dir: Path, output_dir: Path, dry_run: bool) -> list[Path]:
    """Executa a normalização dos arquivos extraídos."""
    input_files = sorted(input_dir.glob("*.jsonl"))
    created_files: list[Path] = []

    for input_path in input_files:
        if dry_run:
            print(f"Normalização planejada para `{input_path.as_posix()}`.")
            continue
        created_files.append(normalize_jsonl_file(input_path, output_dir))

    return created_files


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de linha de comando."""
    parser = argparse.ArgumentParser(description="Normaliza mecanicamente textos extraídos do corpus reformado.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Mostra o plano de normalização sem gravar arquivos.")
    return parser


def main() -> int:
    """Ponto de entrada do script de normalização."""
    args = build_parser().parse_args()
    run_normalization(args.input_dir, args.output_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
