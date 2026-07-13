import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

function normalizeWhitespace(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function toTitleCaseReference(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function uniqueValues(values) {
  return Array.from(new Set(values.filter(Boolean)));
}

function normalizeReferenceNumber(value) {
  const text = String(value || "").trim();
  if (/^[ivxlcdm]+$/i.test(text)) return text.toUpperCase();
  return /^\d+$/.test(text) ? String(Number(text)) : text;
}

function joinPt(values) {
  if (values.length <= 1) return values[0] || "";
  if (values.length === 2) return `${values[0]} e ${values[1]}`;
  return `${values.slice(0, -1).join(", ")} e ${values[values.length - 1]}`;
}

function formatPages(value) {
  const text = normalizeWhitespace(value);
  if (!text || text === "não informado") return "";
  if (/^p\.?\s+/i.test(text) || /^página/i.test(text)) return text;
  return `p. ${text}`;
}

function numberedReference(singular, plural, values) {
  const normalized = uniqueValues(values.map(normalizeReferenceNumber));
  if (!normalized.length) return "";
  return `${normalized.length === 1 ? singular : plural} ${joinPt(normalized)}`;
}

function extractStructuralReference(details) {
  const text = normalizeWhitespace(details);
  const referenceValue = "(?:\\d+|[ivxlcdm]+)";
  const match = text.match(
    new RegExp(
      `\\b((?:artigos?|par[aá]grafos?|se[cç](?:[aã]o|[oõ]es)|perguntas?)\\s+${referenceValue}(?:\\s*,\\s*${referenceValue})*(?:\\s*e\\s*${referenceValue})?)\\b`,
      "i",
    ),
  );
  return toTitleCaseReference(match?.[1] || "");
}

function extractReferenceValuesFromChunkIds(ids, marker) {
  const values = [];
  const pattern = new RegExp(`${marker}[-_]([a-z0-9]+)`, "gi");

  ids.forEach((id) => {
    const normalizedId = String(id || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
    let match = pattern.exec(normalizedId);

    while (match) {
      values.push(match[1]);
      match = pattern.exec(normalizedId);
    }
  });

  return values;
}

function extractStructuralReferenceFromChunkIds(citation) {
  const chunkIds = [
    ...(Array.isArray(citation.included_chunk_ids) ? citation.included_chunk_ids : []),
    ...(Array.isArray(citation.anchor_chunk_ids) ? citation.anchor_chunk_ids : []),
  ];

  if (!chunkIds.length) return "";

  const paragraphReference = numberedReference(
    "Parágrafo",
    "Parágrafos",
    extractReferenceValuesFromChunkIds(chunkIds, "paragrafo"),
  );
  if (paragraphReference) return paragraphReference;

  const articleReference = numberedReference(
    "Artigo",
    "Artigos",
    extractReferenceValuesFromChunkIds(chunkIds, "artigo"),
  );
  if (articleReference) return articleReference;

  const questionReference = numberedReference(
    "Pergunta",
    "Perguntas",
    extractReferenceValuesFromChunkIds(chunkIds, "pergunta"),
  );
  if (questionReference) return questionReference;

  const sectionReference = numberedReference(
    "Seção",
    "Seções",
    extractReferenceValuesFromChunkIds(chunkIds, "secao"),
  );
  if (sectionReference) return sectionReference;

  return "";
}

function buildReferenceLine(citation, parentTitle, structuralReference) {
  if (citation.full_reference) {
    const pages = formatPages(citation.pages);
    return uniqueValues([citation.full_reference, pages].map(normalizeWhitespace).filter(Boolean)).join(" · ");
  }
  const pages = formatPages(citation.pages);
  const segments = [formatChapterTitle(parentTitle), structuralReference, pages]
    .map(normalizeWhitespace)
    .filter(Boolean);
  return uniqueValues(segments).join(" · ");
}

function formatChapterTitle(value) {
  return String(value || "").replace(
    /^(CAP[ÍI]TULO\s+(?:\d+|[IVXLCDM]+))\s+(?![—-])(.+)$/i,
    "$1 — $2",
  );
}

function dehyphenateWords(text) {
  return String(text || "")
    .replace(/\u00ad/g, "")
    .replace(/([A-Za-zÀ-ÿ])-\s+([A-Za-zÀ-ÿ])/g, "$1$2");
}

function normalizeChunkExcerptText(text) {
  let value = dehyphenateWords(text)
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  value = splitLeadingHeading(value);
  value = splitInlineStructuralMarkers(value);

  return value;
}

function splitLeadingHeading(text) {
  let value = String(text || "").trim();

  value = value.replace(
    /^(CAP[ÍI]TULO\s+(?:\d+|[IVXLCDM]+))\s+(?![—-])([A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ,]+?)\s+((?:\d+|[IVXLCDM]+)\.\s+)/,
    "$1 — $2\n\n$3",
  );

  value = value.replace(
    /^(CAP[ÍI]TULO\s+(?:\d+|[IVXLCDM]+)\s+—\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ,]+?)\s+((?:\d+|[IVXLCDM]+)\.\s+)/,
    "$1\n\n$2",
  );

  value = value.replace(
    /^((?:Artigo|Parágrafo|Pergunta|Resposta|Seção)\s+(?:\d+|[IVXLCDM]+)(?:\s+[—-]\s+[^\n]+?)?)\n+(\S)/i,
    "$1\n\n$2",
  );

  value = value.replace(
    /^(Conclus[aã]o(?:\s+[—-]\s+[^.?!:]+?)?)\s+((?:[A-ZÁÉÍÓÚÂÊÔÃÕÇ]|\d+\.))/i,
    "$1\n\n$2",
  );

  return value;
}

function splitInlineStructuralMarkers(text) {
  return String(text || "")
    .replace(/\s+(Artigo\s+\d+\s+[—-]\s+)/gi, "\n\n$1")
    .replace(/\s+(Parágrafo\s+\d+\s+[—-]\s+)/gi, "\n\n$1")
    .replace(/\s+(Pergunta\s+\d+\s+[—-]\s+)/gi, "\n\n$1")
    .replace(/\s+(Seção\s+[IVXLCDM]+\s+[—-]\s+)/gi, "\n\n$1")
    .replace(/\s+(Conclus[aã]o\s+[—-]\s+)/gi, "\n\n$1");
}

function truncateAtWord(text, maxLength) {
  const value = String(text || "").trim();
  if (value.length <= maxLength) return value;
  const slice = value.slice(0, maxLength).trim();
  const lastSpace = slice.lastIndexOf(" ");
  if (lastSpace < Math.floor(maxLength * 0.75)) return `${slice}...`;
  return `${slice.slice(0, lastSpace).trim()}...`;
}

function isTechnicalContextLine(line) {
  return (
    /^\[[^\]]+\]$/.test(line) ||
    /^-{2,}/.test(line) ||
    /^(pergunta|documento|unidade|páginas|paginas|chunks?|chunk\s+âncora|chunk\s+ancora|contexto\s+relacionado|texto|fonte|estratégia|estrategia|status|status\s+da\s+expansão|status\s+da\s+expansao|referência|referencia)\s*:/i.test(
      line,
    )
  );
}

function extractChunkTextFromContextText(contextText) {
  const lines = String(contextText || "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim());

  const blocks = [];
  let current = [];
  let insideChunkBlock = false;

  function flushBlock() {
    const text = normalizeChunkExcerptText(current.join(" "));
    if (text) blocks.push(text);
    current = [];
  }

  lines.forEach((line) => {
    if (!line) return;

    if (/^---/.test(line)) {
      flushBlock();
      insideChunkBlock = true;
      return;
    }

    if (!insideChunkBlock && line !== "[TRECHOS]") return;
    if (line === "[TRECHOS]" || isTechnicalContextLine(line)) return;

    current.push(line);
  });

  flushBlock();
  return blocks.join("\n\n");
}

function extractDocumentExcerpt(citation) {
  const chunkTexts = Array.isArray(citation.chunk_texts)
    ? citation.chunk_texts
        .map((chunk) => normalizeChunkExcerptText(chunk?.text))
        .filter(Boolean)
    : [];

  if (chunkTexts.length) {
    const text = chunkTexts.join("\n\n");
    return truncateAtWord(text, 620);
  }

  const contextText = extractChunkTextFromContextText(citation.context_text);
  if (contextText) {
    return truncateAtWord(contextText, 620);
  }

  const rawText =
    citation.base_documental_text ||
    citation.excerpt ||
    citation.details ||
    "";

  const lines = String(rawText)
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !isTechnicalContextLine(line));

  const text = normalizeChunkExcerptText(lines.join(" "));
  if (!text) return "";
  return truncateAtWord(text, 520);
}

function renderExcerpt(excerpt) {
  return String(excerpt)
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block, index) => {
      const isHeading = /^(CAP[ÍI]TULO|Artigo|Parágrafo|Inciso|Alínea|Pergunta|Resposta|Seção|Conclus[aã]o)\s+/i.test(block);
      return (
        <p className={isHeading ? "source-excerpt-heading" : "source-excerpt-paragraph"} key={index}>
          {block}
        </p>
      );
    });
}

function SourceCard({ citation, index, highlighted = false, onHighlightClear }) {
  const [expanded, setExpanded] = useState(false);
  const sourceNumber = citation.display_number || index + 1;
  const document = citation.document || citation.document_id || "Documento não informado";
  const parentTitle = citation.parent_title || citation.full_reference || citation.unit || citation.section_title || "Unidade não informada";
  const details = citation.base_documental_text || citation.details || "";
  const structuralReference =
    citation.structural_reference ||
    extractStructuralReference(details) ||
    extractStructuralReferenceFromChunkIds(citation);
  const referenceLine = buildReferenceLine(citation, parentTitle, structuralReference);
  const excerpt = extractDocumentExcerpt(citation);

  return (
    <article className={`source-card ${highlighted ? "is-highlighted" : ""}`}>
      <div className="source-main">
        <span className="source-number" aria-hidden="true">
          {sourceNumber}
        </span>
        <div className="source-copy">
          <h3>{document}</h3>
          {referenceLine ? <p>{referenceLine}</p> : null}

          {excerpt ? (
            <div className="source-excerpt-wrap">
              <button
                className="source-excerpt-toggle"
                type="button"
                onClick={() => {
                  setExpanded((current) => !current);
                  onHighlightClear?.();
                }}
                aria-expanded={expanded}
              >
                <span>Ver trecho</span>
                {expanded ? <ChevronUp size={12} aria-hidden="true" /> : <ChevronDown size={12} aria-hidden="true" />}
              </button>

              {expanded ? <blockquote className="source-excerpt">{renderExcerpt(excerpt)}</blockquote> : null}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}

export default SourceCard;
