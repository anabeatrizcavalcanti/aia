"""Create structural JSONL chunks for congregational normative documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from normative_corpus import (
    DEFAULT_CHUNKS_DIR,
    DEFAULT_MANIFEST,
    DEFAULT_NORMALIZED_DIR,
    DEFAULT_REPORT_DIR,
    DEFAULT_TOPIC_MAP,
    EXPECTED_DOCUMENT_IDS,
    run_chunking,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Gera chunks estruturais do corpus normativo congregacional.")
    parser.add_argument("--documents", nargs="+", choices=sorted(EXPECTED_DOCUMENT_IDS))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--normalized-dir", type=Path, default=DEFAULT_NORMALIZED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_CHUNKS_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--topic-map", type=Path, default=DEFAULT_TOPIC_MAP)
    return parser


def main() -> int:
    """Run chunking."""
    args = build_parser().parse_args()
    try:
        report = run_chunking(
            manifest_path=args.manifest,
            normalized_dir=args.normalized_dir,
            output_dir=args.output_dir,
            report_dir=args.report_dir,
            topic_map_path=args.topic_map,
            documents=args.documents,
        )
    except Exception as exc:
        print(f"O chunking normativo falhou: {exc}", file=sys.stderr)
        return 1

    print(f"Chunking normativo concluido com status {report['status']}.")
    for summary in report["summaries"]:
        print(f"- {summary['document_id']}: {summary['chunk_count']} chunks em {summary['jsonl_path']}")
    consolidation = report["consolidation"]
    print(f"- consolidado: {consolidation['chunk_count']} chunks em {consolidation['jsonl_path']}")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
