"""Extract text from congregational normative PDFs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from normative_corpus import DEFAULT_EXTRACTED_DIR, DEFAULT_MANIFEST, DEFAULT_REPORT_DIR, run_extraction


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Extrai texto por pagina dos PDFs normativos congregacionais.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXTRACTED_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Mostra o plano sem gravar arquivos.")
    return parser


def main() -> int:
    """Run extraction."""
    args = build_parser().parse_args()
    try:
        report = run_extraction(args.manifest, args.output_dir, args.report_dir, args.dry_run)
    except Exception as exc:
        print(f"A extracao normativa falhou: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"A extracao normativa processou {report['documents_processed']} documentos.")
        print(f"Status da extracao normativa: {report['status']}.")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
