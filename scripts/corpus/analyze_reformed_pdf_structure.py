"""Analisa a estrutura dos PDFs validados no manifesto reformado."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json"
OUTPUT_DIR = ROOT_DIR / "corpus" / "reports" / "structure_analysis"


CHAPTER_RE = re.compile(
    r"^\s*(?:(?:primeiro|segundo|terceiro|quarto|quinto)\s+cap[ií]tulo|"
    r"terceiro\s+e\s+quarto\s+cap[ií]tulos|cap[ií]tulo|cap\.?)"
    r"\b",
    re.IGNORECASE,
)
ARTICLE_RE = re.compile(r"^\s*(?:artigo|art\.?)\s+([0-9ivxlcdm]+)\b", re.IGNORECASE)
QUESTION_RE = re.compile(r"^\s*(?:p\.|pergunta)\s*\.?\s*[0-9]+\b", re.IGNORECASE)
ANSWER_RE = re.compile(r"^\s*(?:[0-9]+\s+)?(?:r\.|resposta)\s*", re.IGNORECASE)
REJECTION_RE = re.compile(
    r"^\s*(?:rejei[cç][aã]o de erros|erro\s+[0-9ivxlcdm]+|refuta[cç][aã]o)\b",
    re.IGNORECASE,
)
LORDS_DAY_RE = re.compile(r"^\s*dia do senhor\s+[0-9ivxlcdm]+\b", re.IGNORECASE)
PART_RE = re.compile(r"^\s*parte\s+[ivxlcdm0-9]+\b", re.IGNORECASE)
CONCLUSION_RE = re.compile(r"^\s*conclus[aã]o\s*$", re.IGNORECASE)
DORT_ERROR_RE = re.compile(r"^\s*erro\s+([0-9ivxlcdm]+)\b", re.IGNORECASE)
DORT_REFUTATION_RE = re.compile(r"^\s*refuta[cç][aã]o\s*$", re.IGNORECASE)
LONDON_CHAPTER_RE = re.compile(r"^\s*CAP[ÍI]TULO\s+([0-9]+)\b(?:\s*(.*))?$", re.IGNORECASE)
LONDON_PARAGRAPH_RE = re.compile(r"^\s*([0-9]+)\.\s*(.*)$")
WESTMINSTER_CHAPTER_RE = re.compile(r"^\s*CAP[ÍI]TULO\s+([IVXLCDM]+)\b(?:\s*(.*))?$", re.IGNORECASE)
WESTMINSTER_SECTION_RE = re.compile(r"^\s*([IVXLCDM]+)\.\s+(.*)$")
WESTMINSTER_OLD_TESTAMENT_BOOKS = [
    "Gênesis (Gn)",
    "Êxodo (Ex)",
    "Levítico (Lv)",
    "Números (Nm)",
    "Deuteronômio (Dt)",
    "Josué (Js)",
    "Juízes (Jz)",
    "Rute (Rt)",
    "I Samuel (1Sm)",
    "II Samuel (2Sm)",
    "I Reis (1Rs)",
    "II Reis (2Rs)",
    "I Crônicas (1Cr)",
    "II Crônicas (2Cr)",
    "Esdras (Ed)",
    "Neemias (Ne)",
    "Ester (Et)",
    "Jó (Jó)",
    "Salmos (Sl)",
    "Provérbios (Pv)",
    "Eclesiastes (Ec)",
    "Cântico dos Cânticos (Ct)",
    "Isaías (Is)",
    "Jeremias (Jr)",
    "Lamentações (Lm)",
    "Ezequiel (Ez)",
    "Daniel (Dn)",
    "Oséias (Os)",
    "Joel (Jl)",
    "Amós (Am)",
    "Obadias (Ob)",
    "Jonas (Jn)",
    "Miquéias (Mq)",
    "Naum (Na)",
    "Habacuque (Hc)",
    "Sofonias (Sf)",
    "Ageu (Ag)",
    "Zacarias (Zc)",
    "Malaquias (Ml)",
]
WESTMINSTER_NEW_TESTAMENT_BOOKS = [
    "Mateus (Mt)",
    "Marcos (Mc)",
    "Lucas (Lc)",
    "João (Jo)",
    "Atos (At)",
    "Romanos (Rm)",
    "I Coríntios (1Co)",
    "II Coríntios (2Co)",
    "Gálatas (Gl)",
    "Efésios (Ef)",
    "Filipenses (Fp)",
    "Colossenses (Cl)",
    "I Tessalonicenses (1Ts)",
    "II Tessalonicenses (2Ts)",
    "I Timóteo (1Tm)",
    "II Timóteo (2Tm)",
    "Tito (Tt)",
    "Filemom (Fm)",
    "Hebreus (Hb)",
    "Tiago (Tg)",
    "I Pedro (1Pe)",
    "II Pedro (2Pe)",
    "I João (1Jo)",
    "II João (2Jo)",
    "III João (3Jo)",
    "Judas (Jd)",
    "Apocalipse (Ap)",
]
CATECHISM_SECTION_TITLES = {
    "catecismo de heidelberg",
    "nossos pecados e miseria",
    "nossos pecados e miséria",
    "nossa salvacao",
    "nossa salvação",
    "a nossa gratidao",
    "a nossa gratidão",
    "deus pai e a nossa criacao",
    "deus pai e a nossa criação",
    "deus filho e a nossa redencao",
    "deus filho e a nossa redenção",
    "deus espirito santo e a nossa santificacao",
    "deus espírito santo e a nossa santificação",
    "a nossa justificacao",
    "a nossa justificação",
    "a palavra e os sacramentos",
    "o santo batismo",
    "a santa ceia",
    "os dez mandamentos",
    "a oracao",
    "a oração",
}
IGNORED_CATECHISM_HEADERS = {
    "o catecismo de heidelberg",
}
BIBLE_BOOK_PATTERN = (
    r"(?:[1-3]\s*)?(?:gn|g[eê]nesis|ex|[eê]x|[eê]xodo|lv|lev[ií]tico|nm|"
    r"n[uú]meros|dt|js|jz|rt|sm|rs|reis|cr|ed|ne|et|j[oó]|sl|pv|ec|ct|is|"
    r"jr|lm|ez|dn|os|jl|am|ob|jn|mq|na|hc|sf|ag|zc|ml|mt|mateus|mc|"
    r"marcos|lc|lucas|jo|jo[aã]o|at|atos|rm|romanos|co|cor[ií]ntios|"
    r"gl|g[aá]latas|ef|ef[eé]sios|fl|fp|filipenses|cl|colossenses|ts|"
    r"tessalonicenses|tm|tim[oó]teo|tt|tito|fm|filemom|hb|hebreus|"
    r"tg|tiago|pe|pedro|jd|judas|ap|apocalipse)"
)
UNNUMBERED_BIBLE_BOOK_PATTERN = (
    r"(?:gn|g[eê]nesis|ex|[eê]x|[eê]xodo|lv|lev[ií]tico|nm|"
    r"n[uú]meros|dt|js|jz|rt|ed|ne|et|sl|pv|ec|ct|is|"
    r"jr|lm|ez|dn|os|jl|am|ob|jn|mq|na|hc|sf|ag|zc|ml|mt|mateus|mc|"
    r"marcos|lc|lucas|at|atos|rm|romanos|gl|g[aá]latas|ef|ef[eé]sios|"
    r"fl|fp|filipenses|cl|colossenses|tt|tito|fm|filemom|hb|hebreus|"
    r"tg|tiago|jd|judas|ap|apocalipse)"
)
STRUCTURAL_START_RE = re.compile(
    r"^\s*(?:"
    r"(?:primeiro|segundo|terceiro|quarto|quinto)\s+cap[ií]tulo|"
    r"terceiro\s+e\s+quarto\s+cap[ií]tulos|"
    r"cap[ií]tulo|cap\.?|artigo|art\.?|p\.|pergunta|r\.|resposta|"
    r"dia do senhor|parte|rejei[cç][aã]o de erros|erro\s+[0-9ivxlcdm]+|"
    r"refuta[cç][aã]o|[ivxlcdm]+\.\s+|[0-9]+\.\s+"
    r")",
    re.IGNORECASE,
)
BIBLE_REF_RE = re.compile(
    rf"\b{BIBLE_BOOK_PATTERN}\.?\s*[0-9]+[:.][0-9]+",
    re.IGNORECASE,
)
REFERENCE_MARKER_RE = re.compile(
    rf"(?:^|\s)([0-9]+)\.\s*(?={BIBLE_BOOK_PATTERN}\.?\s*[0-9])",
    re.IGNORECASE,
)
SPACED_REFERENCE_MARKER_RE = re.compile(
    rf"(?:^|\s)([0-9]+)\s+(?={UNNUMBERED_BIBLE_BOOK_PATTERN}\.?\s*[0-9])",
    re.IGNORECASE,
)
INCOMPLETE_REFERENCE_MARKER_RE = re.compile(r"(?<!\S)([0-9]{1,2})\.\s+(?=[0-9]+[.:][0-9])")
REFERENCE_TEXT_STARTS_WITH_BOOK_RE = re.compile(
    rf"^\s*{BIBLE_BOOK_PATTERN}\.?\s*[0-9]",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PatternMatch:
    """Representa um padrão estrutural encontrado em uma página."""

    page: int
    text: str


@dataclass(frozen=True)
class TextLine:
    """Representa uma linha textual extraída de uma página."""

    page: int
    line_number: int
    text: str


def load_manifest(path: Path) -> dict[str, Any]:
    """Carrega o manifesto do corpus reformado."""
    return json.loads(path.read_text(encoding="utf-8"))


def line_is_probable_title(line: str) -> bool:
    """Indica se uma linha parece ser título estrutural, sem usar palavras soltas."""
    stripped = line.strip()
    if len(stripped) < 6 or len(stripped) > 120:
        return False
    if CHAPTER_RE.match(stripped) or LORDS_DAY_RE.match(stripped) or PART_RE.match(stripped):
        return True
    letters = [char for char in stripped if char.isalpha()]
    return bool(letters) and stripped.isupper() and len(letters) >= 5


def should_merge_continuation(current_line: str, next_line: str) -> bool:
    """Indica se uma linha seguinte parece continuar um título quebrado no PDF."""
    clean_next = next_line.strip()
    if not clean_next or len(clean_next) > 120:
        return False
    if STRUCTURAL_START_RE.match(clean_next):
        return False
    if re.search(r"[.!?…]$", current_line.strip()):
        return False
    return True


def merge_structural_continuations(lines: list[str], start_index: int, max_extra_lines: int = 2) -> str:
    """Reconstrói títulos estruturais que o PDF extraiu em mais de uma linha."""
    merged = lines[start_index].strip()
    consumed = 0
    while consumed < max_extra_lines:
        next_index = start_index + consumed + 1
        if next_index >= len(lines):
            break
        next_line = lines[next_index].strip()
        if not should_merge_continuation(merged, next_line):
            break
        merged = f"{merged} {next_line}"
        consumed += 1
    return merged


def collect_matches(
    lines_by_page: list[tuple[int, list[str]]],
    pattern: re.Pattern[str],
    merge_continuations: bool = False,
) -> list[dict[str, Any]]:
    """Coleta linhas que correspondem a um padrão no início da linha."""
    matches: list[dict[str, Any]] = []
    for page_number, lines in lines_by_page:
        for index, line in enumerate(lines):
            clean_line = line.strip()
            if pattern.match(clean_line):
                if merge_continuations:
                    clean_line = merge_structural_continuations(lines, index)
                matches.append({"page": page_number, "text": clean_line})
    return matches


def collect_titles(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Coleta possíveis títulos estruturais."""
    titles: list[dict[str, Any]] = []
    for page_number, lines in lines_by_page:
        for index, line in enumerate(lines):
            clean_line = line.strip()
            if line_is_probable_title(clean_line):
                clean_line = merge_structural_continuations(lines, index)
                titles.append({"page": page_number, "text": clean_line})
    return titles[:80]


def merge_catechism_part_line(lines: list[str], index: int) -> str:
    """Recompõe uma Parte do catecismo quando título e subtítulo vêm em linhas separadas."""
    line = lines[index].strip()
    match = re.match(r"^(Parte\s+[IVXLCDM0-9]+)\s*(.*)$", line, re.IGNORECASE)
    if not match:
        return line

    part_label = match.group(1).strip()
    inline_title = match.group(2).strip()
    if inline_title:
        return f"{part_label} {inline_title}"

    next_index = index + 1
    if next_index >= len(lines):
        return part_label

    next_line = lines[next_index].strip()
    normalized_next = normalize_label(next_line)
    if (
        normalized_next in CATECHISM_SECTION_TITLES
        and normalized_next not in IGNORED_CATECHISM_HEADERS
        and not LORDS_DAY_RE.match(next_line)
    ):
        return f"{part_label} {next_line}"

    return part_label


def collect_catechism_parts(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Coleta Partes do Catecismo de Heidelberg com título completo."""
    parts: list[dict[str, Any]] = []
    for page_number, lines in lines_by_page:
        for index, line in enumerate(lines):
            if PART_RE.match(line.strip()):
                parts.append({"page": page_number, "text": merge_catechism_part_line(lines, index)})
    return parts


def collect_catechism_introductory_contexts(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Coleta o material introdutório histórico antes do corpo catequético."""
    contexts: list[dict[str, Any]] = []
    for page_number, lines in lines_by_page:
        if page_number != 1:
            continue

        intro_lines: list[str] = []
        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            normalized = normalize_label(clean_line)
            if normalized == "catecismo de heidelberg" and intro_lines:
                break
            if LORDS_DAY_RE.match(clean_line) or QUESTION_RE.match(clean_line):
                break

            intro_lines.append(clean_line)

        text = "\n".join(intro_lines).strip()
        if text:
            contexts.append(
                {
                    "page_start": page_number,
                    "page_end": page_number,
                    "chunk_type": "introductory_context",
                    "content_role": "contextual",
                    "is_doctrinal": False,
                    "section_title": "Material introdutório",
                    "section_reference": "Página 1",
                    "text": text,
                }
            )
    return contexts


def collect_catechism_titles(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Coleta títulos estruturais próprios do Catecismo de Heidelberg."""
    titles: list[dict[str, Any]] = []
    document_title_seen = False
    skipped_indexes: set[tuple[int, int]] = set()

    for page_number, lines in lines_by_page:
        for index, line in enumerate(lines):
            if (page_number, index) in skipped_indexes:
                continue

            clean_line = line.strip()
            normalized = normalize_label(clean_line)

            if normalized == "o catecismo de heidelberg" and not document_title_seen:
                titles.append({"page": page_number, "text": clean_line})
                document_title_seen = True
                continue

            if PART_RE.match(clean_line):
                merged_part = merge_catechism_part_line(lines, index)
                titles.append({"page": page_number, "text": merged_part})
                if merged_part != clean_line:
                    skipped_indexes.add((page_number, index + 1))
                continue

            if LORDS_DAY_RE.match(clean_line):
                titles.append({"page": page_number, "text": clean_line})

    return titles


def split_dort_article_heading(line: str) -> tuple[str, str]:
    """Extrai número e título de um cabeçalho de artigo dos Cânones de Dort."""
    match = re.match(r"^\s*Artigo\s+([0-9ivxlcdm]+)\s*[—-]\s*(.*)$", line, re.IGNORECASE)
    if not match:
        raise ValueError(f"Line is not a Dort article heading: {line}")
    return match.group(1), match.group(2).strip()


def clean_dort_reference_line(line: str) -> str:
    """Limpa uma linha de referências finais dos Cânones de Dort."""
    clean_line = line.strip().lstrip("•").strip()
    return re.sub(r"(?<=[.!?])\s+[0-9]{2,4}$", "", clean_line).strip()


def is_dort_reference_line(line: str) -> bool:
    """Indica se uma linha final de artigo é formada por referências bíblicas."""
    clean_line = clean_dort_reference_line(line)
    if not clean_line:
        return False
    if STRUCTURAL_START_RE.match(clean_line) or clean_line.startswith("—"):
        return False
    if not BIBLE_REF_RE.search(clean_line):
        return False

    without_book_refs = BIBLE_REF_RE.sub("", clean_line)
    without_chapter_refs = re.sub(
        r"\b[0-9]+[:.][0-9]+(?:[-–][0-9]+)?(?:,\s*[0-9]+(?:[-–][0-9]+)?)*\b",
        "",
        without_book_refs,
    )
    without_numeric_refs = re.sub(
        r"\b[0-9]+(?:[-–][0-9]+)?(?:,\s*[0-9]+(?:[-–][0-9]+)?)*\b",
        "",
        without_chapter_refs,
    )
    remaining_words = re.findall(r"[A-Za-zÀ-ÿ]+", without_numeric_refs)
    return not [word for word in remaining_words if word.lower() not in {"e", "cf"}]


def split_trailing_dort_references(lines: list[TextLine]) -> tuple[list[TextLine], list[TextLine]]:
    """Separa referências bíblicas finais do corpo de um artigo positivo."""
    body_lines = list(lines)
    reference_lines: list[TextLine] = []

    while body_lines and is_dort_reference_line(body_lines[-1].text):
        reference_lines.insert(0, body_lines.pop())

    return body_lines, reference_lines


def join_text_lines(lines: list[TextLine]) -> str:
    """Une linhas extraídas preservando o texto em forma legível para análise."""
    return " ".join(line.text.strip() for line in lines if line.text.strip()).strip()


def extract_parenthetical_references(text: str) -> list[str]:
    """Extrai referências bíblicas entre parênteses de uma refutação."""
    references: list[str] = []
    for match in re.finditer(r"\(([^)]*)\)", text):
        content = match.group(1).strip()
        if BIBLE_REF_RE.search(content):
            references.append(content)
    return references


def extract_parenthetical_reference_markers(text: str) -> list[str]:
    """Extrai marcadores de referência bíblica que aparecem dentro do texto."""
    references: list[str] = []
    for match in re.finditer(r"\(([^)]*)\)", text):
        if BIBLE_REF_RE.search(match.group(1)):
            references.append(match.group(0).strip())
    return references


def classify_dort_line(line: str) -> str | None:
    """Classifica uma linha estrutural dos Cânones de Dort."""
    clean_line = line.strip()
    if CHAPTER_RE.match(clean_line):
        return "chapter"
    if ARTICLE_RE.match(clean_line):
        return "article"
    if re.match(r"^\s*rejei[cç][aã]o de erros\s*$", clean_line, re.IGNORECASE):
        return "rejection"
    if DORT_ERROR_RE.match(clean_line):
        return "error"
    if DORT_REFUTATION_RE.match(clean_line):
        return "refutation"
    if CONCLUSION_RE.match(clean_line):
        return "conclusion"
    return None


def build_dort_events(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Coleta eventos estruturais principais dos Cânones de Dort."""
    flattened = flatten_lines(lines_by_page)
    events: list[dict[str, Any]] = []

    for index, line in enumerate(flattened):
        kind = classify_dort_line(line.text)
        if kind is None:
            continue

        text = line.text.strip()
        if kind == "chapter":
            page_lines = next(lines for page, lines in lines_by_page if page == line.page)
            page_index = line.line_number - 1
            text = merge_structural_continuations(page_lines, page_index)

        events.append(
            {
                "kind": kind,
                "index": index,
                "page": line.page,
                "line_number": line.line_number,
                "text": text,
            }
        )

    return events


def build_dort_article(
    article_event: dict[str, Any],
    segment: list[TextLine],
    chapter_title: str,
) -> dict[str, Any]:
    """Monta uma unidade de artigo positivo dos Cânones de Dort."""
    article_number, article_title = split_dort_article_heading(article_event["text"])
    body_lines, reference_lines = split_trailing_dort_references(segment)

    page_end = article_event["page"]
    if reference_lines:
        page_end = reference_lines[-1].page
    elif body_lines:
        page_end = body_lines[-1].page

    article_text = join_text_lines(body_lines)
    cleaned_reference_lines = [clean_dort_reference_line(line.text) for line in reference_lines]
    cleaned_reference_lines = [line for line in cleaned_reference_lines if line]

    return {
        "chunk_type": "doctrinal_article",
        "chapter_title": chapter_title,
        "article_number": article_number,
        "article_heading": article_event["text"],
        "article_title": article_title,
        "page_start": article_event["page"],
        "page_end": page_end,
        "article_text": article_text,
        "reference_in_text": extract_parenthetical_reference_markers(article_text),
        "article_references": " ".join(cleaned_reference_lines).strip(),
    }


def build_dort_rejection(
    rejection_event: dict[str, Any],
    chapter_events: list[dict[str, Any]],
    flattened: list[TextLine],
    chapter_end_index: int,
    chapter_title: str,
) -> dict[str, Any]:
    """Monta a seção de rejeição de erros de um capítulo de Dort."""
    first_error = next(
        (event for event in chapter_events if event["kind"] == "error" and event["index"] > rejection_event["index"]),
        None,
    )
    intro_end = first_error["index"] if first_error is not None else chapter_end_index
    intro_lines = flattened[rejection_event["index"] + 1 : intro_end]
    pairs: list[dict[str, Any]] = []
    error_events = [
        event for event in chapter_events if event["kind"] == "error" and event["index"] > rejection_event["index"]
    ]

    for error_event in error_events:
        next_refutation = next(
            (
                event
                for event in chapter_events
                if event["kind"] == "refutation" and event["index"] > error_event["index"]
            ),
            None,
        )
        if next_refutation is None:
            continue

        next_error_or_end = next(
            (
                event
                for event in chapter_events
                if event["kind"] == "error" and event["index"] > next_refutation["index"]
            ),
            None,
        )
        pair_end = next_error_or_end["index"] if next_error_or_end is not None else chapter_end_index
        error_lines = flattened[error_event["index"] + 1 : next_refutation["index"]]
        refutation_lines = flattened[next_refutation["index"] + 1 : pair_end]
        refutation_text = join_text_lines(refutation_lines)
        error_number_match = DORT_ERROR_RE.match(error_event["text"])
        error_number = error_number_match.group(1) if error_number_match else None

        page_end = next_refutation["page"]
        if refutation_lines:
            page_end = refutation_lines[-1].page
        elif error_lines:
            page_end = error_lines[-1].page

        pairs.append(
            {
                "chunk_type": "error_refutation",
                "chapter_title": chapter_title,
                "error_number": error_number,
                "error_heading": error_event["text"],
                "page_start": error_event["page"],
                "page_end": page_end,
                "error_text": join_text_lines(error_lines),
                "refutation_text": refutation_text,
                "refutation_references": extract_parenthetical_references(refutation_text),
            }
        )

    page_end = pairs[-1]["page_end"] if pairs else rejection_event["page"]
    return {
        "title": rejection_event["text"],
        "page_start": rejection_event["page"],
        "page_end": page_end,
        "intro_text": join_text_lines(intro_lines),
        "pairs": pairs,
    }


def build_dort_conclusion(
    conclusion_event: dict[str, Any],
    flattened: list[TextLine],
) -> dict[str, Any]:
    """Monta a conclusão dos Cânones de Dort."""
    raw_lines = [
        line
        for line in flattened[conclusion_event["index"] + 1 :]
        if line.text.strip() and "Projeto Refo500" not in line.text
    ]
    paragraphs: list[dict[str, Any]] = []
    current: list[TextLine] = []

    def flush_current() -> None:
        if current:
            text = join_text_lines(current)
            number_match = re.match(r"^([0-9]+)\.\s+", text)
            paragraphs.append(
                {
                    "paragraph_type": "numbered_claim" if number_match else "paragraph",
                    "number": number_match.group(1) if number_match else None,
                    "page_start": current[0].page,
                    "page_end": current[-1].page,
                    "text": text,
                }
            )
            current.clear()

    for line in raw_lines:
        starts_new = bool(
            re.match(r"^[0-9]+\.\s+", line.text)
            or re.match(r"^(E ainda|Este Sínodo|Além disso|Finalmente|Que o Senhor)\b", line.text)
        )
        if starts_new:
            flush_current()
        current.append(line)
    flush_current()

    return {
        "title": conclusion_event["text"],
        "page_start": conclusion_event["page"],
        "page_end": raw_lines[-1].page if raw_lines else conclusion_event["page"],
        "paragraphs": paragraphs,
    }


def build_dort_structure(lines_by_page: list[tuple[int, list[str]]]) -> dict[str, Any]:
    """Constrói uma estrutura documental para os Cânones de Dort."""
    flattened = flatten_lines(lines_by_page)
    events = build_dort_events(lines_by_page)
    chapter_events = [event for event in events if event["kind"] == "chapter"]
    conclusion_event = next((event for event in events if event["kind"] == "conclusion"), None)
    doctrinal_chapters: list[dict[str, Any]] = []

    for position, chapter_event in enumerate(chapter_events):
        next_chapter = chapter_events[position + 1] if position + 1 < len(chapter_events) else None
        chapter_end_index = (
            next_chapter["index"]
            if next_chapter is not None
            else conclusion_event["index"] if conclusion_event is not None else len(flattened)
        )
        events_in_chapter = [
            event for event in events if chapter_event["index"] <= event["index"] < chapter_end_index
        ]
        rejection_event = next((event for event in events_in_chapter if event["kind"] == "rejection"), None)
        article_end_limit = rejection_event["index"] if rejection_event is not None else chapter_end_index
        article_events = [
            event for event in events_in_chapter if event["kind"] == "article" and event["index"] < article_end_limit
        ]
        articles: list[dict[str, Any]] = []

        for article_position, article_event in enumerate(article_events):
            next_article = (
                article_events[article_position + 1]
                if article_position + 1 < len(article_events)
                else None
            )
            article_end_index = next_article["index"] if next_article is not None else article_end_limit
            segment = flattened[article_event["index"] + 1 : article_end_index]
            articles.append(build_dort_article(article_event, segment, chapter_event["text"]))

        rejection = None
        if rejection_event is not None:
            rejection = build_dort_rejection(
                rejection_event,
                events_in_chapter,
                flattened,
                chapter_end_index,
                chapter_event["text"],
            )

        doctrinal_chapters.append(
            {
                "chapter_title": chapter_event["text"],
                "page_start": chapter_event["page"],
                "page_end": chapter_end_index and flattened[chapter_end_index - 1].page,
                "articles": articles,
                "rejection_of_errors": rejection,
            }
        )

    conclusion = build_dort_conclusion(conclusion_event, flattened) if conclusion_event is not None else None

    return {
        "doctrinal_chapter_count": len(doctrinal_chapters),
        "article_count": sum(len(chapter["articles"]) for chapter in doctrinal_chapters),
        "error_refutation_count": sum(
            len((chapter["rejection_of_errors"] or {}).get("pairs", []))
            for chapter in doctrinal_chapters
        ),
        "has_conclusion": conclusion is not None,
        "doctrinal_chapters": doctrinal_chapters,
        "conclusion": conclusion,
    }


def flatten_lines(lines_by_page: list[tuple[int, list[str]]]) -> list[TextLine]:
    """Transforma linhas por página em uma sequência linear com metadados."""
    flattened: list[TextLine] = []
    for page_number, lines in lines_by_page:
        for line_number, line in enumerate(lines, start=1):
            flattened.append(TextLine(page=page_number, line_number=line_number, text=line))
    return flattened


def split_london_chapter_heading(line: str) -> tuple[str, str, str | None]:
    """Extrai número, título e possível parágrafo embutido em um cabeçalho de Londres."""
    match = LONDON_CHAPTER_RE.match(line.strip())
    if not match:
        raise ValueError(f"Line is not a London chapter heading: {line}")

    chapter_number = match.group(1)
    remainder = (match.group(2) or "").strip()
    inline_paragraph = None
    paragraph_match = re.search(r"\b([0-9]+)\.\s*(.*)$", remainder)
    if paragraph_match:
        inline_paragraph = f"{paragraph_match.group(1)}. {paragraph_match.group(2).strip()}".strip()
        remainder = remainder[: paragraph_match.start()].strip()

    return chapter_number, re.sub(r"\s+", " ", remainder).strip(), inline_paragraph


def is_london_body_chapter_heading(line: str) -> bool:
    """Indica se a linha é cabeçalho do corpo principal da confissão de Londres."""
    clean_line = line.strip()
    return bool(LONDON_CHAPTER_RE.match(clean_line)) and " - " not in clean_line


def is_probable_london_chapter_title(line: str) -> bool:
    """Indica se uma linha seguinte parece ser o título duplicado do capítulo."""
    clean_line = line.strip()
    if not clean_line or LONDON_PARAGRAPH_RE.match(clean_line) or is_london_body_chapter_heading(clean_line):
        return False
    letters = [char for char in clean_line if char.isalpha()]
    return bool(letters) and sum(char.isupper() for char in letters) / len(letters) >= 0.7


def build_london_chapter_events(flattened: list[TextLine]) -> list[dict[str, Any]]:
    """Coleta os capítulos reais do corpo da Confissão Batista de Londres."""
    body_start = next(
        (
            index
            for index, line in enumerate(flattened)
            if re.match(r"^\s*CAP[ÍI]TULO\s+1\s*$", line.text, re.IGNORECASE)
        ),
        None,
    )
    if body_start is None:
        return []

    events: list[dict[str, Any]] = []
    for index, line in enumerate(flattened[body_start:], start=body_start):
        if not is_london_body_chapter_heading(line.text):
            continue

        chapter_number, inline_title, inline_paragraph = split_london_chapter_heading(line.text)
        title = inline_title
        title_line_index = None
        if not title:
            next_index = index + 1
            if next_index < len(flattened) and is_probable_london_chapter_title(flattened[next_index].text):
                title = flattened[next_index].text.strip()
                title_line_index = next_index

        events.append(
            {
                "index": index,
                "page": line.page,
                "line_number": line.line_number,
                "chapter_number": chapter_number,
                "chapter_title": title,
                "chapter_heading": f"CAPÍTULO {int(chapter_number)} {title}".strip(),
                "title_line_index": title_line_index,
                "inline_paragraph": inline_paragraph,
            }
        )

    return events


def group_table_lines(lines: list[str], columns: int) -> list[str]:
    """Agrupa linhas de uma tabela extraída em colunas."""
    return [" ".join(lines[index : index + columns]) for index in range(0, len(lines), columns)]


def build_london_special_layouts(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Reconstrói tabelas especiais da confissão de Londres."""
    page_three = next((lines for page, lines in lines_by_page if page == 3), [])
    if not page_three:
        return []

    try:
        old_start = page_three.index("O VELHO TESTAMENTO")
        new_start = page_three.index("O NOVO TESTAMENTO")
    except ValueError:
        return []

    old_books = page_three[old_start + 1 : new_start]
    new_end = next(
        (
            index
            for index, line in enumerate(page_three[new_start + 1 :], start=new_start + 1)
            if line.startswith("Todos os quais")
        ),
        len(page_three),
    )
    new_books = page_three[new_start + 1 : new_end]

    return [
        {
            "page": 3,
            "text": "O VELHO TESTAMENTO\n" + "\n".join(group_table_lines(old_books, 4)) + "\n",
        },
        {
            "page": 3,
            "text": "O NOVO TESTAMENTO\n" + "\n".join(group_table_lines(new_books, 3)) + "\n",
        },
    ]


def is_london_reference_start(line: str) -> bool:
    """Indica se uma linha inicia um bloco de referência bíblica numerada."""
    clean_line = line.strip()
    if ":" not in clean_line:
        return False
    return bool(re.match(r"^\s*\[?([0-9]{1,3})\]?\s+(?=(?:[1-3]\s*)?[A-Za-zÀ-ÿ])", clean_line))


def extract_london_reference_markers(text: str) -> list[str]:
    """Extrai marcadores de referência presentes no texto confessional."""
    markers: list[tuple[int, str]] = []
    for match in re.finditer(r"\[([0-9]{1,3})\]", text):
        markers.append((match.start(), match.group(1)))
    for match in re.finditer(r"(?<=[,;:])\s+([0-9]{1,3})(?![\]\d])(?=\s+[A-Za-zÀ-ÿ])", text):
        markers.append((match.start(), match.group(1)))
    for match in re.finditer(r"(?<=[.!?])\s+([0-9]{1,3})(?![\]\d])(?:\s+|$)", text):
        markers.append((match.start(), match.group(1)))

    ordered: list[str] = []
    seen: set[str] = set()
    for _, marker in sorted(markers, key=lambda item: item[0]):
        if marker not in seen:
            ordered.append(marker)
            seen.add(marker)
    return ordered


def extract_london_bible_references(text: str) -> list[str]:
    """Extrai referências bíblicas curtas de um bloco de referência de Londres."""
    pattern = re.compile(
        rf"\b{BIBLE_BOOK_PATTERN}\.{{0,2}}\s*[0-9]+[:.][0-9]+(?:[-–][0-9]+)?"
        r"(?:,\s*[0-9]+(?:[-–][0-9]+)?(?!\s*[A-Za-zÀ-ÿ]))*",
        re.IGNORECASE,
    )
    references: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        reference = re.sub(r"\s+", " ", match.group(0)).strip().replace("..", ".")
        if reference not in seen:
            references.append(reference)
            seen.add(reference)
    return references


def parse_london_reference_blocks(lines: list[TextLine]) -> tuple[str, dict[str, str], dict[str, list[str]]]:
    """Agrupa blocos de referências por marcador numérico."""
    blocks: dict[str, list[str]] = {}
    current_marker: str | None = None

    for line in lines:
        clean_line = line.text.strip()
        marker_match = re.match(r"^\s*\[?([0-9]{1,3})\]?\s+", clean_line)
        if marker_match and is_london_reference_start(clean_line):
            current_marker = marker_match.group(1)
            blocks.setdefault(current_marker, []).append(clean_line)
        elif current_marker is not None:
            blocks[current_marker].append(clean_line)

    references = {
        marker: join_text_lines([TextLine(0, 0, text) for text in block])
        for marker, block in blocks.items()
    }
    associations = {}
    for marker, reference_text in references.items():
        markerless_text = re.sub(rf"^\s*\[?{re.escape(marker)}\]?\s+", "", reference_text)
        associations[marker] = extract_london_bible_references(markerless_text)
    return join_text_lines(lines), references, associations


def split_london_paragraph_segment(lines: list[TextLine]) -> tuple[list[TextLine], list[TextLine]]:
    """Separa texto confessional e bloco de referências de um parágrafo de Londres."""
    reference_start = next((index for index, line in enumerate(lines) if is_london_reference_start(line.text)), None)
    if reference_start is None:
        return lines, []
    return lines[:reference_start], lines[reference_start:]


def build_london_paragraph(
    paragraph_line: TextLine,
    paragraph_segment: list[TextLine],
    chapter_event: dict[str, Any],
) -> dict[str, Any]:
    """Monta um parágrafo numerado da Confissão Batista de Londres."""
    paragraph_match = LONDON_PARAGRAPH_RE.match(paragraph_line.text.strip())
    if paragraph_match is None:
        raise ValueError(f"Line is not a London paragraph: {paragraph_line.text}")

    paragraph_number = paragraph_match.group(1)
    first_text = paragraph_match.group(2).strip()
    body_candidates = [TextLine(paragraph_line.page, paragraph_line.line_number, first_text)] if first_text else []
    body_candidates.extend(paragraph_segment)
    paragraph_text_lines, reference_lines = split_london_paragraph_segment(body_candidates)
    paragraph_text = join_text_lines(paragraph_text_lines)
    reference_text, references, associations = parse_london_reference_blocks(reference_lines)

    page_end = paragraph_line.page
    if reference_lines:
        page_end = reference_lines[-1].page
    elif paragraph_text_lines:
        page_end = paragraph_text_lines[-1].page

    return {
        "chunk_type": "confessional_paragraph",
        "chapter_number": chapter_event["chapter_number"],
        "chapter_title": chapter_event["chapter_heading"],
        "paragraph_number": paragraph_number,
        "page_start": paragraph_line.page,
        "page_end": page_end,
        "paragraph_text": paragraph_text,
        "reference_in_text": extract_london_reference_markers(paragraph_text),
        "reference_text": reference_text,
        "references": references,
        "reference_associations": associations,
    }


def build_london_chapter(
    chapter_event: dict[str, Any],
    chapter_segment: list[TextLine],
) -> dict[str, Any]:
    """Monta um capítulo da Confissão Batista de Londres."""
    segment = list(chapter_segment)
    if chapter_event["inline_paragraph"]:
        segment.insert(0, TextLine(chapter_event["page"], chapter_event["line_number"], chapter_event["inline_paragraph"]))

    paragraph_indexes = [
        index for index, line in enumerate(segment) if LONDON_PARAGRAPH_RE.match(line.text.strip())
    ]
    paragraphs: list[dict[str, Any]] = []
    for order, paragraph_index in enumerate(paragraph_indexes):
        next_paragraph_index = paragraph_indexes[order + 1] if order + 1 < len(paragraph_indexes) else len(segment)
        paragraph_line = segment[paragraph_index]
        paragraph_segment = segment[paragraph_index + 1 : next_paragraph_index]
        paragraphs.append(build_london_paragraph(paragraph_line, paragraph_segment, chapter_event))

    page_end = paragraphs[-1]["page_end"] if paragraphs else chapter_event["page"]
    return {
        "chapter_number": chapter_event["chapter_number"],
        "chapter_title": chapter_event["chapter_heading"],
        "page_start": chapter_event["page"],
        "page_end": page_end,
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraphs,
    }


def build_london_baptist_structure(lines_by_page: list[tuple[int, list[str]]]) -> dict[str, Any]:
    """Constrói a estrutura documental da Confissão Batista de Londres de 1689."""
    flattened = flatten_lines(lines_by_page)
    chapter_events = build_london_chapter_events(flattened)
    chapters: list[dict[str, Any]] = []

    for index, chapter_event in enumerate(chapter_events):
        next_chapter_index = chapter_events[index + 1]["index"] if index + 1 < len(chapter_events) else len(flattened)
        start_index = chapter_event["index"] + 1
        if chapter_event["title_line_index"] == start_index:
            start_index += 1
        segment = flattened[start_index:next_chapter_index]
        chapters.append(build_london_chapter(chapter_event, segment))

    return {
        "chapter_count": len(chapters),
        "paragraph_count": sum(chapter["paragraph_count"] for chapter in chapters),
        "special_layouts": build_london_special_layouts(lines_by_page),
        "chapters": chapters,
    }


def format_westminster_books_table() -> str:
    """Reconstroi a tabela de livros bíblicos da Confissão de Westminster."""
    return (
        "ANTIGO TESTAMENTO\n"
        + ", ".join(WESTMINSTER_OLD_TESTAMENT_BOOKS)
        + "\n\nNOVO TESTAMENTO\n"
        + ", ".join(WESTMINSTER_NEW_TESTAMENT_BOOKS)
    )


def build_westminster_special_layouts() -> list[dict[str, Any]]:
    """Retorna estruturas especiais identificadas no corpo de Westminster."""
    return [{"page": 18, "text": format_westminster_books_table() + "\n"}]


def is_westminster_body_chapter_heading(line: str) -> bool:
    """Indica se a linha é cabeçalho de capítulo no corpo de Westminster."""
    return bool(WESTMINSTER_CHAPTER_RE.match(line.strip()))


def is_probable_westminster_chapter_title(line: str) -> bool:
    """Indica se a linha parece ser título duplicado de capítulo."""
    clean_line = line.strip()
    if not clean_line or WESTMINSTER_SECTION_RE.match(clean_line) or is_westminster_body_chapter_heading(clean_line):
        return False
    letters = [char for char in clean_line if char.isalpha()]
    return bool(letters) and sum(char.isupper() for char in letters) / len(letters) >= 0.7


def build_westminster_chapter_events(flattened: list[TextLine]) -> list[dict[str, Any]]:
    """Coleta os capítulos reais do corpo da Confissão de Westminster."""
    body_start = next(
        (
            index
            for index, line in enumerate(flattened)
            if line.page >= 18 and re.match(r"^\s*CAP[ÍI]TULO\s+I\s*$", line.text, re.IGNORECASE)
        ),
        None,
    )
    if body_start is None:
        return []

    events: list[dict[str, Any]] = []
    for index, line in enumerate(flattened[body_start:], start=body_start):
        match = WESTMINSTER_CHAPTER_RE.match(line.text.strip())
        if match is None:
            continue

        chapter_number = match.group(1).upper()
        inline_title = (match.group(2) or "").strip()
        title = inline_title
        title_line_index = None
        if not title:
            next_index = index + 1
            if next_index < len(flattened) and is_probable_westminster_chapter_title(flattened[next_index].text):
                title = flattened[next_index].text.strip()
                title_line_index = next_index

        title = re.sub(r"\s+", " ", title).strip()
        events.append(
            {
                "index": index,
                "page": line.page,
                "line_number": line.line_number,
                "chapter_number": chapter_number,
                "chapter_title": title,
                "chapter_heading": f"CAPÍTULO {chapter_number} {title}".strip(),
                "title_line_index": title_line_index,
            }
        )

    return events


def normalize_bible_reference(reference: str) -> str:
    """Normaliza espaços e pontuação em uma referência bíblica extraída."""
    normalized = reference.strip().replace("..", ".")
    normalized = re.sub(r"\.\s+(?=[0-9])", " ", normalized)
    normalized = re.sub(r"\s*:\s*", ":", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace(" ,", ",").replace(" ;", ";")
    return normalized


def extract_westminster_biblical_references(text: str) -> list[str]:
    """Extrai referências bíblicas inline de uma seção de Westminster."""
    pattern = re.compile(
        rf"\b{BIBLE_BOOK_PATTERN}\.?\s*[0-9]+\s*[:.]\s*[0-9]+(?:[-–][0-9]+)?"
        r"(?:,\s*[0-9]+(?:[-–][0-9]+)?(?!\s*[A-Za-zÀ-ÿ]))*",
        re.IGNORECASE,
    )
    references: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        reference = normalize_bible_reference(match.group(0))
        if reference not in seen:
            references.append(reference)
            seen.add(reference)
    return references


def rebuild_westminster_section_lines(section_number: str, lines: list[str]) -> list[str]:
    """Reconstroi trechos estruturais especiais de uma seção de Westminster."""
    if section_number != "II":
        return lines
    try:
        table_start = lines.index("ANTIGO TESTAMENTO")
        table_end = next(
            index for index, line in enumerate(lines[table_start + 1 :], start=table_start + 1)
            if line.startswith("Todos os quais")
        )
    except (ValueError, StopIteration):
        return lines

    return lines[:table_start] + [format_westminster_books_table()] + lines[table_end:]


def join_westminster_section_lines(lines: list[str]) -> str:
    """Une linhas de uma seção preservando blocos estruturais com quebras."""
    text = ""
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        if "\n" in clean_line:
            text = text.rstrip() + "\n\n" + clean_line + "\n\n"
        else:
            text += ("" if not text or text.endswith("\n\n") else " ") + clean_line
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_westminster_section(
    section_line: TextLine,
    section_segment: list[TextLine],
    chapter_event: dict[str, Any],
) -> dict[str, Any]:
    """Monta uma seção da Confissão de Westminster."""
    section_match = WESTMINSTER_SECTION_RE.match(section_line.text.strip())
    if section_match is None:
        raise ValueError(f"Line is not a Westminster section: {section_line.text}")

    section_number = section_match.group(1).upper()
    first_text = section_match.group(2).strip()
    body_lines = [first_text] if first_text else []
    body_lines.extend(line.text for line in section_segment)
    body_lines = rebuild_westminster_section_lines(section_number, body_lines)
    section_text = join_westminster_section_lines(body_lines)

    page_end = section_line.page
    if section_segment:
        page_end = section_segment[-1].page

    return {
        "chunk_type": "confessional_section",
        "chapter_number": chapter_event["chapter_number"],
        "chapter_title": chapter_event["chapter_heading"],
        "section_number": section_number,
        "page_start": section_line.page,
        "page_end": page_end,
        "section_text": section_text,
        "biblical_references": extract_westminster_biblical_references(section_text),
    }


def build_westminster_chapter(
    chapter_event: dict[str, Any],
    chapter_segment: list[TextLine],
) -> dict[str, Any]:
    """Monta um capítulo da Confissão de Westminster."""
    chapter_segment = [
        line for line in chapter_segment if not (line.line_number == 1 and line.text.strip().isdigit())
    ]
    section_indexes = [
        index for index, line in enumerate(chapter_segment) if WESTMINSTER_SECTION_RE.match(line.text.strip())
    ]
    sections: list[dict[str, Any]] = []
    for order, section_index in enumerate(section_indexes):
        next_section_index = section_indexes[order + 1] if order + 1 < len(section_indexes) else len(chapter_segment)
        section_line = chapter_segment[section_index]
        section_segment = chapter_segment[section_index + 1 : next_section_index]
        sections.append(build_westminster_section(section_line, section_segment, chapter_event))

    page_end = sections[-1]["page_end"] if sections else chapter_event["page"]
    return {
        "chapter_number": chapter_event["chapter_number"],
        "chapter_title": chapter_event["chapter_heading"],
        "page_start": chapter_event["page"],
        "page_end": page_end,
        "section_count": len(sections),
        "sections": sections,
    }


def build_westminster_structure(lines_by_page: list[tuple[int, list[str]]]) -> dict[str, Any]:
    """Constrói a estrutura documental da Confissão de Fé de Westminster."""
    flattened = flatten_lines(lines_by_page)
    chapter_events = build_westminster_chapter_events(flattened)
    chapters: list[dict[str, Any]] = []

    for index, chapter_event in enumerate(chapter_events):
        next_chapter_index = chapter_events[index + 1]["index"] if index + 1 < len(chapter_events) else len(flattened)
        start_index = chapter_event["index"] + 1
        if chapter_event["title_line_index"] == start_index:
            start_index += 1
        segment = flattened[start_index:next_chapter_index]
        chapters.append(build_westminster_chapter(chapter_event, segment))

    return {
        "chapter_count": len(chapters),
        "section_count": sum(chapter["section_count"] for chapter in chapters),
        "special_layouts": build_westminster_special_layouts(),
        "chapters": chapters,
    }


def normalize_label(value: str) -> str:
    """Normaliza um rótulo curto para comparação estrutural."""
    return re.sub(r"\s+", " ", value.strip().lower())


def parse_lords_day_number(line: str) -> int | None:
    """Extrai o número de uma linha `Dia do Senhor N`."""
    match = re.match(r"^\s*dia do senhor\s+([0-9]+)\b", line, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def normalize_lords_day_line(
    line: str,
    previous_number: int | None,
) -> tuple[str, int | None, bool]:
    """Normaliza um cabeçalho de Dia do Senhor quando a extração perde dígitos."""
    number = parse_lords_day_number(line)
    if number is None:
        return line, None, False

    expected_number = previous_number + 1 if previous_number is not None else number
    if number == expected_number:
        return line, number, False

    expected_text = str(expected_number)
    if previous_number is not None and expected_text.startswith(str(number)):
        return f"Dia do Senhor {expected_number}", expected_number, True

    return line, number, False


def is_catechism_section_line(line: str) -> bool:
    """Indica se a linha é cabeçalho estrutural do Catecismo de Heidelberg."""
    clean_line = line.strip()
    normalized = normalize_label(clean_line)
    if not clean_line:
        return False
    if LORDS_DAY_RE.match(clean_line) or PART_RE.match(clean_line):
        return True
    if normalized in CATECHISM_SECTION_TITLES or normalized in IGNORED_CATECHISM_HEADERS:
        return True
    return False


def build_catechism_contexts(flattened: list[TextLine]) -> dict[int, dict[str, Any]]:
    """Mapeia cada pergunta ao contexto catequético vigente."""
    contexts: dict[int, dict[str, Any]] = {}
    current_part_label: str | None = None
    current_part_title: str | None = None
    current_lords_day: str | None = None
    current_lords_day_raw: str | None = None
    current_lords_day_number: int | None = None
    current_lords_day_inferred = False
    current_section_title: str | None = None
    awaiting_part_title = False

    for index, line in enumerate(flattened):
        text = line.text.strip()
        normalized = normalize_label(text)

        if normalized in IGNORED_CATECHISM_HEADERS:
            continue
        if PART_RE.match(text):
            part_match = re.match(r"^(Parte\s+[IVXLCDM0-9]+)\s*(.*)$", text, re.IGNORECASE)
            if part_match:
                current_part_label = part_match.group(1).strip()
                current_part_title = part_match.group(2).strip() or None
            else:
                current_part_label = text
                current_part_title = None
            current_section_title = None
            awaiting_part_title = current_part_title is None
            continue
        if LORDS_DAY_RE.match(text):
            current_lords_day_raw = text
            normalized_lords_day, lords_day_number, inferred = normalize_lords_day_line(
                text,
                current_lords_day_number,
            )
            current_lords_day = normalized_lords_day
            current_lords_day_number = lords_day_number
            current_lords_day_inferred = inferred
            continue
        if normalized in CATECHISM_SECTION_TITLES:
            if awaiting_part_title and current_part_label is not None:
                current_part_title = text
                current_section_title = None
                awaiting_part_title = False
            else:
                current_section_title = text
            continue
        if QUESTION_RE.match(text):
            current_part = None
            if current_part_label and current_part_title:
                current_part = f"{current_part_label} {current_part_title}"
            elif current_part_label:
                current_part = current_part_label
            contexts[index] = {
                "part_label": current_part_label,
                "part_title": current_part_title,
                "part": current_part,
                "lords_day": current_lords_day,
                "lords_day_raw": current_lords_day_raw,
                "lords_day_number": current_lords_day_number,
                "lords_day_inferred": current_lords_day_inferred,
                "section_title": current_section_title,
            }

    return contexts


def split_question_line(line: str) -> tuple[int, str, str | None]:
    """Extrai número da pergunta, texto da pergunta e resposta inline, se existir."""
    match = re.match(r"^\s*P\.\s*(?P<number>[0-9]+)\.\s*(?P<body>.*)$", line)
    if not match:
        raise ValueError(f"Line is not a catechism question: {line}")

    body = match.group("body").strip()
    answer_match = re.search(r"\s+(?:[0-9]+\s+)?R\.\s*", body)
    if answer_match:
        question_text = body[: answer_match.start()].strip()
        answer_text = body[answer_match.end() :].strip()
        return int(match.group("number")), question_text, answer_text

    return int(match.group("number")), body, None


def split_answer_line(line: str) -> str | None:
    """Extrai o texto de uma linha iniciada por marcador de resposta."""
    match = re.match(r"^\s*(?:[0-9]+\s+)?R\.\s*(?P<body>.*)$", line, re.IGNORECASE)
    if not match:
        return None
    return match.group("body").strip()


def extract_prefixed_answer_marker(line: str) -> str | None:
    """Extrai marcador de referência que aparece antes de `R.`."""
    match = re.match(r"^\s*([0-9]+)\s+R\.", line, re.IGNORECASE)
    return match.group(1) if match else None


def is_reference_block_start(line: str) -> bool:
    """Indica se uma linha parece iniciar bloco de referências bíblicas."""
    return bool(REFERENCE_MARKER_RE.match(line) or SPACED_REFERENCE_MARKER_RE.match(line))


def split_reference_start(line: str) -> tuple[str, str | None]:
    """Separa texto principal de bloco de referências quando ambos estão na mesma linha."""
    matches = [
        match
        for match in (
            REFERENCE_MARKER_RE.search(line),
            SPACED_REFERENCE_MARKER_RE.search(line),
        )
        if match is not None
    ]
    match = min(matches, key=lambda item: item.start()) if matches else None
    if not match:
        return line.strip(), None
    return line[: match.start()].strip(), line[match.start() :].strip()


def extract_answer_markers(answer_text: str) -> list[str]:
    """Extrai marcadores numéricos anexados ao texto da resposta."""
    markers = re.findall(r"(?<![0-9]\.)(?<=[A-Za-zÀ-ÿ).;:,!?\"”])([0-9]+)(?=[^0-9]|$)", answer_text)
    return sorted(set(markers), key=int)


def extract_standalone_numeric_markers(text: str) -> list[str]:
    """Extrai candidatos a marcadores numéricos separados por espaço."""
    markers = re.findall(r"(?<![0-9.])\b([0-9]{1,2})(?=\s|$)", text)
    return sorted(set(markers), key=int)


def normalize_reference_block(reference_lines: list[str]) -> str:
    """Une linhas de referências em um bloco normalizado."""
    joined = " ".join(line.strip() for line in reference_lines if line.strip())
    return re.sub(r"\s+", " ", joined).strip()


def parse_reference_entries(reference_lines: list[str]) -> list[dict[str, str]]:
    """Separa entradas numeradas de referência, mesmo quando estão incompletas."""
    joined = normalize_reference_block(reference_lines)
    if not joined:
        return []

    marker_matches: list[tuple[int, int, str, str]] = []
    for match in REFERENCE_MARKER_RE.finditer(joined):
        marker_matches.append((match.start(), match.end(), match.group(1), "valid"))
    for match in SPACED_REFERENCE_MARKER_RE.finditer(joined):
        marker_matches.append((match.start(), match.end(), match.group(1), "valid"))
    valid_starts = {start for start, _, _, _ in marker_matches}
    for match in INCOMPLETE_REFERENCE_MARKER_RE.finditer(joined):
        if match.start() not in valid_starts:
            marker_matches.append((match.start(), match.end(), match.group(1), "incomplete"))

    marker_matches = sorted(marker_matches, key=lambda item: item[0])
    entries: list[dict[str, str]] = []
    for index, (start, content_start, marker, entry_type) in enumerate(marker_matches):
        end = marker_matches[index + 1][0] if index + 1 < len(marker_matches) else len(joined)
        entries.append(
            {
                "marker": marker,
                "raw_reference": joined[start:end].strip(),
                "reference_text": joined[content_start:end].strip(),
                "entry_type": entry_type,
            }
        )
    return entries


def parse_reference_map(
    reference_lines: list[str],
    allowed_markers: set[str] | None = None,
) -> dict[str, str]:
    """Mapeia marcadores de referência para o texto bíblico correspondente."""
    references: dict[str, str] = {}

    for entry in parse_reference_entries(reference_lines):
        marker = entry["marker"]
        reference_text = entry["reference_text"]
        if allowed_markers is not None and marker not in allowed_markers:
            continue
        if entry["entry_type"] != "valid":
            continue
        if not REFERENCE_TEXT_STARTS_WITH_BOOK_RE.match(reference_text):
            continue
        references[marker] = reference_text

    return references


def build_reference_parse_issues(
    answer_markers: list[str],
    reference_map: dict[str, str],
    reference_lines: list[str],
) -> list[dict[str, Any]]:
    """Registra problemas de parsing de referências que exigem revisão manual."""
    issues: list[dict[str, Any]] = []
    entries = parse_reference_entries(reference_lines)
    entries_by_marker: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        entries_by_marker.setdefault(entry["marker"], []).append(entry)
    valid_entries_by_marker = {
        marker: [entry for entry in marker_entries if entry["entry_type"] == "valid"]
        for marker, marker_entries in entries_by_marker.items()
    }

    for marker in answer_markers:
        if marker in reference_map:
            continue

        matching_entries = entries_by_marker.get(marker, [])
        if not matching_entries:
            issues.append(
                {
                    "marker": marker,
                    "raw_reference": None,
                    "issue": "missing_reference_entry",
                    "status": "manual_review_required",
                }
            )
            continue

        for entry in matching_entries:
            issue = "missing_bible_book"
            if BIBLE_REF_RE.search(entry["reference_text"]):
                issue = "unmapped_reference_entry"
            issues.append(
                {
                    "marker": marker,
                    "raw_reference": entry["raw_reference"],
                    "issue": issue,
                    "status": "manual_review_required",
                }
            )

    duplicated_markers = sorted(
        [marker for marker, marker_entries in valid_entries_by_marker.items() if len(marker_entries) > 1],
        key=int,
    )
    for marker in duplicated_markers:
        for entry in valid_entries_by_marker[marker]:
            issues.append(
                {
                    "marker": marker,
                    "raw_reference": entry["raw_reference"],
                    "issue": "duplicated_reference_marker_suspected",
                    "status": "manual_review_required",
                }
            )

    return issues


def build_catechism_units(lines_by_page: list[tuple[int, list[str]]]) -> list[dict[str, Any]]:
    """Constrói unidades pergunta-resposta para documentos catequéticos."""
    flattened = flatten_lines(lines_by_page)
    contexts = build_catechism_contexts(flattened)
    question_indexes = [
        index for index, line in enumerate(flattened) if QUESTION_RE.match(line.text)
    ]
    units: list[dict[str, Any]] = []

    for position, start_index in enumerate(question_indexes):
        end_index = question_indexes[position + 1] if position + 1 < len(question_indexes) else len(flattened)
        segment = flattened[start_index:end_index]
        if not segment:
            continue

        question_number, first_question_text, inline_answer = split_question_line(segment[0].text)
        question_lines = [first_question_text] if first_question_text else []
        answer_lines: list[str] = []
        reference_lines: list[str] = []
        trailing_section_lines: list[str] = []
        prefixed_answer_markers: list[str] = []
        answer_started = inline_answer is not None
        reference_started = False
        last_unit_page = segment[0].page

        if inline_answer:
            answer_part, reference_part = split_reference_start(inline_answer)
            if answer_part:
                answer_lines.append(answer_part)
                last_unit_page = segment[0].page
            if reference_part:
                reference_started = True
                reference_lines.append(reference_part)
                last_unit_page = segment[0].page

        for line in segment[1:]:
            if is_catechism_section_line(line.text):
                trailing_section_lines.append(line.text)
                continue

            answer_body = split_answer_line(line.text)
            if answer_body is not None and not reference_started:
                answer_started = True
                last_unit_page = line.page
                prefixed_marker = extract_prefixed_answer_marker(line.text)
                if prefixed_marker is not None:
                    prefixed_answer_markers.append(prefixed_marker)
                answer_part, reference_part = split_reference_start(answer_body)
                if answer_part:
                    answer_lines.append(answer_part)
                    last_unit_page = line.page
                if reference_part:
                    reference_started = True
                    reference_lines.append(reference_part)
                    last_unit_page = line.page
                continue

            if not answer_started:
                question_lines.append(line.text)
                last_unit_page = line.page
                continue

            if not reference_started:
                answer_part, reference_part = split_reference_start(line.text)
                if reference_part:
                    if answer_part:
                        answer_lines.append(answer_part)
                        last_unit_page = line.page
                    reference_started = True
                    reference_lines.append(reference_part)
                    last_unit_page = line.page
                    continue

            if is_reference_block_start(line.text):
                reference_started = True

            if reference_started:
                reference_lines.append(line.text)
                last_unit_page = line.page
            else:
                answer_lines.append(line.text)
                last_unit_page = line.page

        question_text = " ".join(question_lines).strip()
        answer_text = " ".join(answer_lines).strip()
        question_markers = extract_answer_markers(question_text)
        base_answer_markers = sorted(
            set(extract_answer_markers(answer_text) + prefixed_answer_markers),
            key=int,
        )
        reference_map = parse_reference_map(reference_lines)
        standalone_markers = [
            marker
            for marker in extract_standalone_numeric_markers(answer_text)
            if marker in reference_map
        ]
        answer_markers = sorted(
            set(base_answer_markers + standalone_markers),
            key=int,
        )
        allowed_markers = set(question_markers + answer_markers)
        reference_map = {
            marker: reference
            for marker, reference in reference_map.items()
            if marker in allowed_markers
        }
        unresolved_markers = [
            marker for marker in answer_markers if marker not in reference_map
        ]
        unreferenced_entries = [
            marker for marker in reference_map if marker not in answer_markers and marker not in question_markers
        ]
        reference_parse_issues = build_reference_parse_issues(
            answer_markers=answer_markers,
            reference_map=reference_map,
            reference_lines=reference_lines,
        )

        units.append(
            {
                "question_number": question_number,
                "page_start": segment[0].page,
                "page_end": last_unit_page,
                "part_label": contexts.get(start_index, {}).get("part_label"),
                "part_title": contexts.get(start_index, {}).get("part_title"),
                "part": contexts.get(start_index, {}).get("part"),
                "lords_day": contexts.get(start_index, {}).get("lords_day"),
                "lords_day_raw": contexts.get(start_index, {}).get("lords_day_raw"),
                "lords_day_number": contexts.get(start_index, {}).get("lords_day_number"),
                "lords_day_inferred": contexts.get(start_index, {}).get("lords_day_inferred"),
                "section_title": contexts.get(start_index, {}).get("section_title"),
                "question_text": question_text,
                "answer_text": answer_text,
                "question_reference_markers": question_markers,
                "answer_reference_markers": answer_markers,
                "references": reference_map,
                "reference_lines": reference_lines,
                "trailing_section_lines_excluded": trailing_section_lines,
                "next_context_lines_detected": trailing_section_lines,
                "unresolved_answer_markers": unresolved_markers,
                "unreferenced_reference_entries": unreferenced_entries,
                "reference_parse_issues": reference_parse_issues,
                "inline_answer_detected": inline_answer is not None,
            }
        )

    return units


def build_catechism_consistency(units: list[dict[str, Any]]) -> dict[str, Any]:
    """Resume sinais de consistência das unidades catequéticas."""
    missing_answers = [unit["question_number"] for unit in units if not unit["answer_text"]]
    inline_answers = [unit["question_number"] for unit in units if unit["inline_answer_detected"]]
    unresolved = {
        str(unit["question_number"]): unit["unresolved_answer_markers"]
        for unit in units
        if unit["unresolved_answer_markers"]
    }
    unreferenced = {
        str(unit["question_number"]): unit["unreferenced_reference_entries"]
        for unit in units
        if unit["unreferenced_reference_entries"]
    }
    reference_parse_issues = {
        str(unit["question_number"]): unit["reference_parse_issues"]
        for unit in units
        if unit["reference_parse_issues"]
    }

    return {
        "qa_unit_count": len(units),
        "missing_answer_question_numbers": missing_answers,
        "inline_answer_question_numbers": inline_answers,
        "unresolved_answer_markers": unresolved,
        "unreferenced_reference_entries": unreferenced,
        "reference_parse_issues": reference_parse_issues,
    }


def infer_risks(summary: dict[str, Any]) -> list[str]:
    """Infere riscos iniciais de extração a partir dos sinais estruturais."""
    risks: list[str] = []
    if summary["average_chars_per_page"] < 500:
        risks.append("A média de caracteres por página é baixa; o PDF pode ter páginas com pouca camada textual.")
    if summary["short_pages"]:
        risks.append("Há páginas muito curtas que podem corresponder a capa, sumário, divisórias ou páginas com extração limitada.")
    if summary["special_layout_pages"]:
        risks.append("Foram encontrados sinais de listas, blocos de referências ou estruturas especiais que exigem cuidado no chunking.")
    if summary["notes_count"] > 20:
        risks.append("A quantidade de possíveis notas ou referências é alta; elas devem ser preservadas sem virar chunks doutrinários isolados.")
    if not risks:
        risks.append("Nenhum risco crítico apareceu nesta leitura preliminar, mas a segmentação ainda precisa de revisão manual.")
    return risks


def analyze_pdf(document: dict[str, Any], fitz_module: Any) -> dict[str, Any]:
    """Analisa a estrutura textual de um PDF do manifesto."""
    pdf_path = ROOT_DIR / document["raw_path"]
    with fitz_module.open(pdf_path) as pdf:
        pages: list[dict[str, Any]] = []
        lines_by_page: list[tuple[int, list[str]]] = []
        all_text = []

        for index, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            all_text.append(text)
            lines_by_page.append((index, lines))
            pages.append(
                {
                    "page_number": index,
                    "character_count": len(text),
                    "line_count": len(lines),
                    "is_very_short": len(text) < 500,
                }
            )

    full_text = "\n".join(all_text)
    character_counts = [page["character_count"] for page in pages]
    short_pages = [page["page_number"] for page in pages if page["is_very_short"]]
    introductory_keywords = ("sumário", "sumario", "prefácio", "prefacio", "introdução", "introducao", "histórico", "historico", "apresentação", "apresentacao")
    detected_introductory_pages = [
        page_number
        for page_number, lines in lines_by_page
        if page_number <= 5 or any(keyword in " ".join(lines).lower() for keyword in introductory_keywords)
    ]
    detected_special_layout_pages = [
        page_number
        for page_number, lines in lines_by_page
        if any("antigo testamento" in line.lower() or "novo testamento" in line.lower() for line in lines)
        or sum(1 for line in lines if len(line) <= 35) >= 18
    ]
    possible_notes = [
        {"page": page_number, "text": line}
        for page_number, lines in lines_by_page
        for line in lines
        if re.match(r"^\s*(?:\[[0-9]+\]|[0-9]{1,3}\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç])", line)
    ]
    bible_refs = BIBLE_REF_RE.findall(full_text)

    is_heidelberg = document["document_id"] == "catecismo-heidelberg"
    is_dort = document["document_id"] == "canones-de-dort"
    is_london = document["document_id"] == "confissao-batista-londres-1689"
    is_westminster = document["document_id"] == "confissao-fe-westminster"
    uses_structured_output = is_dort or is_heidelberg or is_london or is_westminster
    if is_westminster:
        introductory_pages = list(range(3, 18))
    elif uses_structured_output:
        introductory_pages = [1]
    else:
        introductory_pages = sorted(set(detected_introductory_pages))
    if is_westminster:
        special_layout_pages = [18]
    elif is_london:
        special_layout_pages = [3]
    elif uses_structured_output:
        special_layout_pages = []
    else:
        special_layout_pages = sorted(set(detected_special_layout_pages))

    summary: dict[str, Any] = {
        "document_id": document["document_id"],
        "title": document["title"],
        "raw_path": document["raw_path"],
        "page_count": len(pages),
        "average_chars_per_page": round(mean(character_counts), 2) if character_counts else 0,
        "short_pages": short_pages,
        "introductory_pages": introductory_pages,
        "special_layout_pages": special_layout_pages,
    }
    if is_dort:
        summary["canons_structure"] = build_dort_structure(lines_by_page)
    elif is_heidelberg:
        catechism_units = build_catechism_units(lines_by_page)
        summary["introductory_contexts"] = collect_catechism_introductory_contexts(lines_by_page)
        summary["parts"] = collect_catechism_parts(lines_by_page)
        summary["catechism_units"] = catechism_units
        summary["catechism_consistency"] = build_catechism_consistency(catechism_units)
    elif is_london:
        summary["london_baptist_structure"] = build_london_baptist_structure(lines_by_page)
    elif is_westminster:
        summary["westminster_structure"] = build_westminster_structure(lines_by_page)
    else:
        summary.update(
            {
                "titles": collect_catechism_titles(lines_by_page) if is_heidelberg else collect_titles(lines_by_page),
                "chapters": collect_matches(lines_by_page, CHAPTER_RE, merge_continuations=True),
                "articles": collect_matches(lines_by_page, ARTICLE_RE),
                "questions": collect_matches(lines_by_page, QUESTION_RE),
                "answers": collect_matches(lines_by_page, ANSWER_RE),
                "rejections": collect_matches(lines_by_page, REJECTION_RE),
                "lords_days": collect_matches(lines_by_page, LORDS_DAY_RE),
                "parts": collect_catechism_parts(lines_by_page) if is_heidelberg else collect_matches(lines_by_page, PART_RE),
                "possible_bible_references_count": len(bible_refs),
                "notes_count": len(possible_notes),
                "possible_notes_examples": possible_notes[:20],
                "pages": pages,
            }
        )
    return summary


def write_json_report(summary: dict[str, Any]) -> Path:
    """Grava o relatório estrutural em JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{summary['document_id']}.structure.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def format_examples(items: list[dict[str, Any]], empty_message: str, limit: int = 8) -> list[str]:
    """Formata exemplos de padrões estruturais para relatório Markdown."""
    if not items:
        return [f"- {empty_message}"]
    return [f"- p. {item['page']}: `{item['text']}`" for item in items[:limit]]


def write_markdown_report(summary: dict[str, Any]) -> Path:
    """Grava o relatório estrutural em Markdown com linguagem humana."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{summary['document_id']}.structure.md"

    lines = [
        f"# Análise estrutural — {summary['title']}",
        "",
        "## Síntese",
        "",
        (
            f"Foram analisadas {summary['page_count']} páginas do arquivo "
            f"`{summary['raw_path']}`. A média aproximada foi de "
            f"{summary['average_chars_per_page']} caracteres por página."
        ),
        "",
        "## O que foi encontrado",
        "",
        f"- Páginas muito curtas: {summary['short_pages'] or 'nenhuma ocorrência relevante'}",
        f"- Páginas introdutórias: {summary['introductory_pages'] or 'nenhuma ocorrência relevante'}",
        f"- Páginas com possíveis estruturas especiais: {summary['special_layout_pages'] or 'nenhuma ocorrência relevante'}",
    ]
    if "possible_bible_references_count" in summary:
        lines.append(f"- Possíveis referências bíblicas identificadas: {summary['possible_bible_references_count']}")
    if "notes_count" in summary:
        lines.append(f"- Possíveis notas ou blocos numerados: {summary['notes_count']}")

    if any(key in summary for key in ("chapters", "titles", "articles", "questions", "answers", "rejections")):
        lines.extend(
            [
                "",
                "## Padrões estruturais observados",
                "",
                "### Títulos e capítulos",
                "",
                *format_examples(
                    summary.get("chapters", []) or summary.get("titles", []),
                    "Nenhum padrão recorrente de título ou capítulo foi detectado.",
                ),
                "",
                "### Artigos",
                "",
                *format_examples(summary.get("articles", []), "Nenhum artigo estrutural foi detectado no início de linha."),
                "",
                "### Perguntas e respostas",
                "",
                *format_examples(
                    summary.get("questions", []) + summary.get("answers", []),
                    "Nenhum padrão de pergunta ou resposta foi detectado.",
                ),
                "",
                "### Rejeições de erro",
                "",
                *format_examples(summary.get("rejections", []), "Nenhum padrão de rejeição de erro foi detectado."),
            ]
        )
    if "catechism_consistency" in summary:
        consistency = summary["catechism_consistency"]
        lines.extend(
            [
                "",
                "### Consistência catequética",
                "",
                f"- Contextos introdutórios estruturados: {len(summary.get('introductory_contexts', []))}",
                f"- Unidades pergunta-resposta montadas: {consistency['qa_unit_count']}",
                (
                    "- Perguntas com resposta na mesma linha: "
                    f"{consistency['inline_answer_question_numbers'] or 'nenhuma ocorrência relevante'}"
                ),
                (
                    "- Perguntas sem resposta textual detectada: "
                    f"{consistency['missing_answer_question_numbers'] or 'nenhuma ocorrência relevante'}"
                ),
                (
                    "- Marcadores de resposta sem referência mapeada: "
                    f"{consistency['unresolved_answer_markers'] or 'nenhuma ocorrência relevante'}"
                ),
                (
                    "- Problemas de parsing de referências: "
                    f"{consistency['reference_parse_issues'] or 'nenhuma ocorrência relevante'}"
                ),
            ]
        )
    if "canons_structure" in summary:
        canons = summary["canons_structure"]
        lines.extend(
            [
                "",
                "### Estrutura organizada dos Cânones de Dort",
                "",
                (
                    "- A estrutura preparada para o chunking está registrada no JSON "
                    "em `canons_structure`, sem os campos genéricos que não se aplicam "
                    "a este documento."
                ),
                f"- Capítulos doutrinários estruturados: {canons['doctrinal_chapter_count']}",
                f"- Artigos doutrinários estruturados: {canons['article_count']}",
                f"- Pares erro-refutação estruturados: {canons['error_refutation_count']}",
                f"- Conclusão estruturada: {'sim' if canons['has_conclusion'] else 'não'}",
            ]
        )
    if "london_baptist_structure" in summary:
        london = summary["london_baptist_structure"]
        lines.extend(
            [
                "",
                "### Estrutura organizada da Confissão Batista de Londres",
                "",
                (
                    "- A estrutura preparada para o chunking está registrada no JSON "
                    "em `london_baptist_structure`, sem os campos genéricos que não se "
                    "aplicam a este documento."
                ),
                f"- Capítulos estruturados: {london['chapter_count']}",
                f"- Parágrafos estruturados: {london['paragraph_count']}",
                f"- Estruturas especiais preservadas: {len(london['special_layouts'])}",
            ]
        )
    if "westminster_structure" in summary:
        westminster = summary["westminster_structure"]
        lines.extend(
            [
                "",
                "### Estrutura organizada da Confissão de Fé de Westminster",
                "",
                (
                    "- A estrutura preparada para o chunking está registrada no JSON "
                    "em `westminster_structure`, sem os campos genéricos que não se "
                    "aplicam a este documento."
                ),
                f"- Capítulos estruturados: {westminster['chapter_count']}",
                f"- Seções estruturadas: {westminster['section_count']}",
                f"- Estruturas especiais preservadas: {len(westminster['special_layouts'])}",
            ]
        )
    risks = summary.get("risks", [])
    if risks:
        lines.extend(["", "## Riscos de extração", ""])
        lines.extend(f"- {risk}" for risk in risks)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_skipped_report(reason: str) -> None:
    """Registra que a análise estrutural não pôde ser executada."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "structure_analysis_not_executed.md"
    path.write_text(
        "\n".join(
            [
                "# Análise estrutural não executada",
                "",
                reason,
                "",
                "A análise estrutural depende de um manifesto validado com os quatro documentos do corpus reformado.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """Executa a análise estrutural dos PDFs descritos no manifesto."""
    if not MANIFEST_PATH.exists():
        reason = "O manifesto `corpus/raw/reformed_manifest.json` não foi encontrado."
        print(reason)
        write_skipped_report(reason)
        return 1

    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError:
        reason = "PyMuPDF não está instalado; a análise estrutural dos PDFs não pôde ser executada."
        print(reason)
        write_skipped_report(reason)
        return 1

    manifest = load_manifest(MANIFEST_PATH)
    documents = manifest.get("documents", [])
    if len(documents) != 4:
        reason = "O manifesto não contém os quatro documentos esperados do corpus reformado."
        print(reason)
        write_skipped_report(reason)
        return 1

    print("A análise estrutural será executada para os quatro documentos do manifesto reformado.")
    for document in documents:
        summary = analyze_pdf(document, fitz)
        json_path = write_json_report(summary)
        md_path = write_markdown_report(summary)
        print(
            f"- {document['document_id']}: relatórios em "
            f"{md_path.relative_to(ROOT_DIR).as_posix()} e {json_path.relative_to(ROOT_DIR).as_posix()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
