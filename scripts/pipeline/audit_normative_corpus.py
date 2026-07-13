"""Audit generated congregational normative corpus artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from normative_corpus import (
    DEFAULT_CHUNKS_DIR,
    DEFAULT_EXTRACTED_DIR,
    DEFAULT_MANIFEST,
    DEFAULT_NORMALIZED_DIR,
    DEFAULT_REPORT_DIR,
    DEFAULT_TAXONOMY,
    run_audit,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Audita os artefatos do corpus normativo congregacional.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--extracted-dir", type=Path, default=DEFAULT_EXTRACTED_DIR)
    parser.add_argument("--normalized-dir", type=Path, default=DEFAULT_NORMALIZED_DIR)
    parser.add_argument("--chunks-dir", type=Path, default=DEFAULT_CHUNKS_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    return parser


def main() -> int:
    """Run audit."""
    args = build_parser().parse_args()
    try:
        report = run_audit(
            manifest_path=args.manifest,
            extracted_dir=args.extracted_dir,
            normalized_dir=args.normalized_dir,
            chunks_dir=args.chunks_dir,
            report_dir=args.report_dir,
            taxonomy_path=args.taxonomy,
        )
    except Exception as exc:
        print(f"A auditoria normativa falhou: {exc}", file=sys.stderr)
        return 1

    print(f"Auditoria normativa concluida com status {report['status']}.")
    for summary in report["documents"]:
        print(
            f"- {summary['document_id']}: {summary['chunks_count']} chunks, "
            f"{summary['articles_detected']} artigos, status {summary['status']}"
        )
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
