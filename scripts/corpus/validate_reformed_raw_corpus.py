"""Valida os PDFs brutos do corpus reformado e cria o manifesto inicial."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "corpus" / "raw" / "reformed"
MANIFEST_PATH = ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json"
REPORT_PATH = ROOT_DIR / "corpus" / "reports" / "structure_analysis" / "reformed_raw_validation.md"


@dataclass(frozen=True)
class ExpectedDocument:
    """Representa um documento esperado no corpus reformado bruto."""

    document_id: str
    title: str
    document_type: str
    keywords: tuple[str, ...]


EXPECTED_DOCUMENTS: tuple[ExpectedDocument, ...] = (
    ExpectedDocument(
        document_id="confissao-fe-westminster",
        title="Confissão de Fé de Westminster",
        document_type="confession_of_faith",
        keywords=("westminster",),
    ),
    ExpectedDocument(
        document_id="canones-de-dort",
        title="Cânones de Dort",
        document_type="doctrinal_canons",
        keywords=("dort", "canones", "canons"),
    ),
    ExpectedDocument(
        document_id="catecismo-heidelberg",
        title="Catecismo de Heidelberg",
        document_type="catechism",
        keywords=("heidelberg",),
    ),
    ExpectedDocument(
        document_id="confissao-batista-londres-1689",
        title="Confissão Batista de Londres de 1689",
        document_type="confession_of_faith",
        keywords=("londres", "london", "1689", "batista"),
    ),
)


def normalize_for_match(value: str) -> str:
    """Normaliza nomes de arquivos para comparação por heurística simples."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def list_pdfs(raw_dir: Path) -> list[Path]:
    """Lista os PDFs presentes no diretório bruto do corpus reformado."""
    if not raw_dir.exists():
        return []
    return sorted(path for path in raw_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")


def score_pdf_for_document(pdf_path: Path, expected: ExpectedDocument) -> int:
    """Calcula uma pontuação simples de associação entre PDF e documento esperado."""
    normalized_name = normalize_for_match(pdf_path.stem)
    return sum(1 for keyword in expected.keywords if keyword in normalized_name)


def associate_pdfs(
    pdf_paths: list[Path],
) -> tuple[dict[str, Path], list[str], list[str], list[Path]]:
    """Associa PDFs aos documentos esperados, registrando ausências e ambiguidades."""
    matches: dict[str, Path] = {}
    missing: list[str] = []
    ambiguities: list[str] = []

    for expected in EXPECTED_DOCUMENTS:
        scored = [
            (pdf_path, score_pdf_for_document(pdf_path, expected))
            for pdf_path in pdf_paths
        ]
        candidates = [(pdf_path, score) for pdf_path, score in scored if score > 0]

        if not candidates:
            missing.append(expected.document_id)
            continue

        best_score = max(score for _, score in candidates)
        best_candidates = [pdf_path for pdf_path, score in candidates if score == best_score]

        if len(best_candidates) > 1:
            names = ", ".join(path.name for path in best_candidates)
            ambiguities.append(f"`{expected.document_id}` pode corresponder a: {names}")
            continue

        matches[expected.document_id] = best_candidates[0]

    reversed_matches: dict[Path, list[str]] = {}
    for document_id, pdf_path in matches.items():
        reversed_matches.setdefault(pdf_path, []).append(document_id)

    for pdf_path, document_ids in reversed_matches.items():
        if len(document_ids) > 1:
            joined_ids = ", ".join(f"`{document_id}`" for document_id in document_ids)
            ambiguities.append(f"`{pdf_path.name}` foi associado a mais de um documento: {joined_ids}")

    used_paths = set(matches.values())
    unassociated = [pdf_path for pdf_path in pdf_paths if pdf_path not in used_paths]
    return matches, missing, ambiguities, unassociated


def build_manifest(matches: dict[str, Path]) -> dict[str, object]:
    """Cria o manifesto do corpus reformado a partir dos PDFs validados."""
    documents: list[dict[str, object]] = []

    for expected in EXPECTED_DOCUMENTS:
        pdf_path = matches[expected.document_id]
        documents.append(
            {
                "document_id": expected.document_id,
                "title": expected.title,
                "tradition_family": "Protestant",
                "tradition_branch": "Reformed",
                "document_type": expected.document_type,
                "language": "pt",
                "raw_path": pdf_path.relative_to(ROOT_DIR).as_posix(),
                "status": "raw_validated",
                "notes": [],
            }
        )

    return {
        "corpus_id": "reformed",
        "corpus_name": "Corpus Confessional Reformado",
        "description": (
            "Corpus principal do SolaBot, composto por documentos confessionais "
            "da tradição reformada."
        ),
        "documents": documents,
    }


def write_manifest(manifest: dict[str, object], manifest_path: Path) -> None:
    """Persiste o manifesto em JSON com codificação UTF-8."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_validation_report(
    pdf_paths: list[Path],
    matches: dict[str, Path],
    missing: list[str],
    ambiguities: list[str],
    unassociated: list[Path],
    status: str,
) -> None:
    """Gera um relatório humano sobre a validação do corpus bruto."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Validação do corpus reformado bruto",
        "",
        f"## Status",
        "",
        status,
        "",
        "## O que foi analisado",
        "",
        (
            "A validação examinou os arquivos PDF presentes em "
            "`corpus/raw/reformed/` e tentou associá-los aos quatro documentos "
            "esperados do corpus reformado principal do SolaBot."
        ),
        "",
        "## PDFs encontrados",
        "",
    ]

    if pdf_paths:
        lines.extend(f"- `{path.name}`" for path in pdf_paths)
    else:
        lines.append("- Nenhum PDF foi encontrado no diretório bruto reformado.")

    lines.extend(["", "## Associações realizadas", ""])
    if matches:
        for expected in EXPECTED_DOCUMENTS:
            pdf_path = matches.get(expected.document_id)
            if pdf_path is not None:
                lines.append(f"- `{expected.document_id}` foi associado a `{pdf_path.name}`.")
    else:
        lines.append("- Nenhuma associação segura foi realizada.")

    lines.extend(["", "## Pendências e riscos", ""])
    if missing:
        lines.append("Os seguintes documentos esperados não foram localizados:")
        lines.extend(f"- `{document_id}`" for document_id in missing)
    if ambiguities:
        lines.append("Foram encontradas ambiguidades que exigem revisão manual:")
        lines.extend(f"- {message}" for message in ambiguities)
    if unassociated:
        lines.append("Também existem PDFs não associados a documentos esperados:")
        lines.extend(f"- `{path.name}`" for path in unassociated)
    if not missing and not ambiguities:
        lines.append(
            "A validação localizou os quatro documentos esperados e não encontrou "
            "ambiguidade nas associações por nome de arquivo."
        )

    lines.extend(["", "## Resultado da validação", ""])
    if status == "PASS":
        lines.append(
            "Os quatro documentos foram identificados. O manifesto "
            "`corpus/raw/reformed_manifest.json` foi criado ou atualizado com os "
            "caminhos reais dos PDFs."
        )
    else:
        lines.append(
            "A validação não ficou completa. As pendências acima permanecem "
            "registradas para acompanhamento."
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Executa a validação do corpus reformado bruto."""
    if not RAW_DIR.exists():
        print("O diretório corpus/raw/reformed/ não existe. Crie a pasta e adicione os PDFs esperados.")
        write_validation_report([], {}, [doc.document_id for doc in EXPECTED_DOCUMENTS], [], [], "FAIL")
        return 1

    pdf_paths = list_pdfs(RAW_DIR)
    matches, missing, ambiguities, unassociated = associate_pdfs(pdf_paths)
    status = "PASS" if not missing and not ambiguities else "FAIL"

    if status == "PASS":
        manifest = build_manifest(matches)
        write_manifest(manifest, MANIFEST_PATH)
        print("A validação localizou os quatro documentos esperados do corpus reformado.")
        for expected in EXPECTED_DOCUMENTS:
            pdf_path = matches[expected.document_id]
            print(f"- {expected.document_id}: {pdf_path.relative_to(ROOT_DIR).as_posix()}")
        print(f"O manifesto foi criado em {MANIFEST_PATH.relative_to(ROOT_DIR).as_posix()}.")
    else:
        print("A validação não conseguiu confirmar todos os documentos esperados.")
        if missing:
            print("Documentos faltantes:")
            for document_id in missing:
                print(f"- {document_id}")
        if ambiguities:
            print("Ambiguidades encontradas:")
            for message in ambiguities:
                print(f"- {message}")

    write_validation_report(pdf_paths, matches, missing, ambiguities, unassociated, status)
    print(f"O relatório de validação foi registrado em {REPORT_PATH.relative_to(ROOT_DIR).as_posix()}.")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
