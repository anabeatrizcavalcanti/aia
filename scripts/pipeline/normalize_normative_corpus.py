"""Normalize extracted congregational normative texts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from normative_corpus import DEFAULT_EXTRACTED_DIR, DEFAULT_NORMALIZED_DIR, DEFAULT_REPORT_DIR, run_normalization


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Normaliza textos extraidos dos documentos normativos.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_EXTRACTED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_NORMALIZED_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Mostra o plano sem gravar arquivos.")
    return parser


def main() -> int:
    """Run normalization."""
    args = build_parser().parse_args()
    try:
        report = run_normalization(args.input_dir, args.output_dir, args.report_dir, args.dry_run)
    except Exception as exc:
        print(f"A normalizacao normativa falhou: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"A normalizacao normativa processou {report['documents_processed']} documentos.")
        print(f"Status da normalizacao normativa: {report['status']}.")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
