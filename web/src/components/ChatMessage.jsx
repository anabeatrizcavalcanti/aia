import React, { useState } from "react";
import { AlertTriangle, ChevronDown, ShieldCheck } from "lucide-react";
import SourceCard from "./SourceCard.jsx";

function formatAnswerText(message) {
  const answer = message.answer || message.message || "Sem resposta textual retornada.";
  return String(answer)
    .replace(/\r\n/g, "\n")
    .replace(/^\s*resposta\s*:?\s*/i, "")
    .trim();
}

function findSectionMarker(text, type, regex) {
  const match = regex.exec(text);
  if (!match) return null;

  const label = match[1] || match[0];
  const labelOffset = match[0].lastIndexOf(label);
  const index = match.index + Math.max(labelOffset, 0);
  return {
    index,
    end: index + label.length,
    type,
  };
}

function parseAnswerSections(message) {
  const rawText = formatAnswerText(message);
  const markers = [
    findSectionMarker(rawText, "base", /(?:^|\n|\s)((?:\*\*)?\s*base\s+documentt?al\s*:\s*(?:\*\*)?)/i),
    findSectionMarker(rawText, "observation", /(?:^|\n|\s)((?:\*\*)?\s*observa[cç][aã]o\s*:\s*(?:\*\*)?)/i),
  ]
    .filter(Boolean)
    .sort((a, b) => a.index - b.index);

  if (!markers.length) {
    return { answerText: rawText.trim(), baseDocumental: "", observation: "" };
  }

  const answerText = rawText.slice(0, markers[0].index).trim();
  let baseDocumental = "";
  let observation = "";

  markers.forEach((marker, index) => {
    const next = markers[index + 1]?.index ?? rawText.length;
    const sectionText = rawText.slice(marker.end, next).trim();
    if (marker.type === "base") baseDocumental = sectionText;
    if (marker.type === "observation") observation = sectionText;
  });

  return { answerText, baseDocumental, observation };
}

function baseDocumentalEntry(baseDocumental, index) {
  if (!baseDocumental) return "";
  const sourceNumber = index + 1;
  const lines = baseDocumental.split(/\r?\n/);
  const markerPattern = new RegExp(`^\\s*(?:[-*]\\s*)?\\[${sourceNumber}\\]\\s*`);
  const anyMarkerPattern = /^\s*(?:[-*]\s*)?\[\d+\]\s*/;
  const start = lines.findIndex((line) => markerPattern.test(line));

  if (start < 0) return index === 0 ? baseDocumental.trim() : "";

  const selected = [];
  for (let lineIndex = start; lineIndex < lines.length; lineIndex += 1) {
    const line = lines[lineIndex];
    if (lineIndex > start && anyMarkerPattern.test(line)) break;
    selected.push(line);
  }
  return selected.join("\n").trim();
}

function citationsWithBaseDocumental(citations, baseDocumental) {
  if (!baseDocumental) return citations;
  if (!citations.length) {
    return [
      {
        document: "Base documental",
        parent_title: "Trechos citados pelo modelo",
        pages: null,
        details: baseDocumental,
      },
    ];
  }
  return citations.map((citation, index) => ({
    ...citation,
    base_documental_text: baseDocumentalEntry(baseDocumental, index),
  }));
}

function citationNumbersInText(...texts) {
  const numbers = [];
  const seen = new Set();
  texts
    .filter(Boolean)
    .forEach((text) => {
      String(text)
        .match(/\[(\d+)\]/g)
        ?.forEach((marker) => {
          const number = Number(marker.replace(/\D/g, ""));
          if (Number.isInteger(number) && !seen.has(number)) {
            seen.add(number);
            numbers.push(number);
          }
        });
    });
  return numbers;
}

function citationsReferencedByAnswer(citations, citedNumbers) {
  const withOriginalNumbers = citations.map((citation, index) => ({
    ...citation,
    original_number: index + 1,
  }));

  if (!citedNumbers.length) {
    return withOriginalNumbers.map((citation, index) => ({
      ...citation,
      display_number: index + 1,
    }));
  }

  return citedNumbers
    .map((sourceNumber) => withOriginalNumbers[sourceNumber - 1])
    .filter(Boolean)
    .map((citation, index) => ({
      ...citation,
      display_number: index + 1,
    }));
}

function citationDisplayMap(citations) {
  return new Map(
    citations
      .map((citation) => [Number(citation.original_number), Number(citation.display_number)])
      .filter(([originalNumber, displayNumber]) => Number.isInteger(originalNumber) && Number.isInteger(displayNumber)),
  );
}

function uniqueDocumentsFromCitations(citations) {
  return Array.from(
    new Set(
      citations
        .map((citation) => citation.document || citation.document_id)
        .filter(Boolean),
    ),
  );
}

function contextCountLabel(count) {
  if (!Number.isInteger(count)) return "";
  return `${count} ${count === 1 ? "contexto" : "contextos"}`;
}

function renderInlineMarkdown(text, onCiteClick, displayMap) {
  const parts = String(text).split(/(\*\*[^*]+\*\*|\[\d+\])/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    const citationMatch = part.match(/^\[(\d+)\]$/);
    if (citationMatch) {
      const citationNumber = Number(citationMatch[1]);
      const displayNumber = displayMap?.get(citationNumber) || citationNumber;
      return (
        <button
          className="citation-marker"
          key={index}
          type="button"
          onClick={() => onCiteClick?.(displayNumber)}
          aria-label={`Ver fonte ${displayNumber}`}
        >
          {displayNumber}
        </button>
      );
    }

    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

function normalizeInlineNumberedList(text) {
  const value = String(text || "").replace(/\r\n/g, "\n").trim();
  const numberedMarkers = value.match(/(?:^|\s)\d{1,2}\.\s+/g) || [];

  if (numberedMarkers.length < 2) return value;
  return value.replace(/\s+(\d{1,2}\.\s+)/g, "\n$1");
}

function groupTextBlocks(text) {
  const lines = normalizeInlineNumberedList(text)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  const groups = [];
  let listGroup = null;

  function flushList() {
    if (listGroup?.items.length) groups.push(listGroup);
    listGroup = null;
  }

  lines.forEach((line) => {
    const ordered = line.match(/^\d{1,2}\.\s+(.+)/);
    const unordered = line.match(/^[-*]\s+(.+)/);

    if (ordered || unordered) {
      const type = ordered ? "ordered" : "unordered";
      if (!listGroup || listGroup.type !== type) {
        flushList();
        listGroup = { type, items: [] };
      }
      listGroup.items.push((ordered || unordered)[1]);
      return;
    }

    flushList();
    groups.push({ type: "paragraph", text: line });
  });

  flushList();
  return groups;
}

function capitalizeSentenceStarts(text) {
  return String(text || "").replace(
    /(^|[.!?]\s+|\n+)(\s*(?:["'“”‘’([{]\s*)?(?:\*\*)?)([a-záàâãéêíóôõúç])/g,
    (match, prefix, opening, letter) => `${prefix}${opening}${letter.toLocaleUpperCase("pt-BR")}`,
  );
}

function renderFormattedText(text, onCiteClick, displayMap) {
  return groupTextBlocks(text).map((group, index) => {
    if (group.type === "ordered") {
      return (
        <ol className="answer-list" key={index}>
          {group.items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInlineMarkdown(capitalizeSentenceStarts(item), onCiteClick, displayMap)}</li>
          ))}
        </ol>
      );
    }

    if (group.type === "unordered") {
      return (
        <ul className="answer-list" key={index}>
          {group.items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInlineMarkdown(capitalizeSentenceStarts(item), onCiteClick, displayMap)}</li>
          ))}
        </ul>
      );
    }

    return (
      <p className="answer-paragraph" key={index}>
        {renderInlineMarkdown(capitalizeSentenceStarts(group.text), onCiteClick, displayMap)}
      </p>
    );
  });
}

function ChatMessage({ message }) {
  const [highlightedSource, setHighlightedSource] = useState(null);

  if (message.role === "user") {
    return (
      <article className="chat-message user-message">
        <div className="message-card user-card">{message.question}</div>
      </article>
    );
  }

  const citations = Array.isArray(message.citations) ? message.citations : [];
  const sections = parseAnswerSections(message);
  const citedNumbers = citationNumbersInText(sections.answerText, sections.observation, message.metadata?.note);
  const displayCitations = citationsReferencedByAnswer(
    citationsWithBaseDocumental(citations, sections.baseDocumental),
    citedNumbers,
  );
  const displayMap = citationDisplayMap(displayCitations);
  const documents = displayCitations.length
    ? uniqueDocumentsFromCitations(displayCitations)
    : Array.isArray(message.used_documents)
      ? message.used_documents
      : [];
  const corrections = message.query_corrections || message.metadata?.query_corrections || [];
  const normalizedQuery = message.normalized_query || message.metadata?.normalized_query;
  const originalQuery = message.query || message.metadata?.original_query;
  const wasNormalized = Boolean(message.query_was_normalized || message.metadata?.query_was_normalized || corrections.length);

  function handleCitationClick(sourceNumber) {
    setHighlightedSource((current) => (current === sourceNumber ? null : sourceNumber));
    window.setTimeout(() => {
      document
        .getElementById(`source-${message.id || "message"}-${sourceNumber}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 40);
  }

  return (
    <article className={`chat-message bot-message ${message.status || "answered"}`}>
      <div className="message-card bot-card">
        {message.status === "refused" ? (
          <div className="refusal-note">
            <AlertTriangle size={17} aria-hidden="true" />
            <span>Não houve evidência documental suficiente para responder com segurança.</span>
          </div>
        ) : null}

        <div className="answer-body">{renderFormattedText(sections.answerText, handleCitationClick, displayMap)}</div>

        {message.metadata?.note ? <div className="message-subnote">{renderFormattedText(message.metadata.note, handleCitationClick, displayMap)}</div> : null}

        {sections.observation ? (
          <div className="message-subnote">{renderFormattedText(sections.observation, handleCitationClick, displayMap)}</div>
        ) : null}

        {wasNormalized && originalQuery && normalizedQuery && originalQuery !== normalizedQuery ? (
          <p className="query-interpretation">Interpretação aplicada: “{originalQuery}” foi tratada como “{normalizedQuery}”.</p>
        ) : null}

        {documents.length || message.used_context_count || message.model ? (
          <div className="message-summary">
            {displayCitations.length ? (
              <span>{contextCountLabel(displayCitations.length)}</span>
            ) : message.used_context_count ? (
              <span>{contextCountLabel(message.used_context_count)}</span>
            ) : null}
            {documents.slice(0, 3).map((document) => <span key={document}>{document}</span>)}
            {message.model ? <span>{message.model}</span> : null}
          </div>
        ) : null}

        {displayCitations.length ? (
          <details className="source-section" aria-label="Fontes documentais usadas" open>
            <summary className="source-section-title">
              <ShieldCheck size={15} aria-hidden="true" />
              <span>Fontes documentais</span>
              <ChevronDown size={14} className="source-chevron" aria-hidden="true" />
            </summary>
            <div className="source-list">
              {displayCitations.map((citation, index) => (
                <div
                  id={`source-${message.id || "message"}-${citation.display_number || index + 1}`}
                  key={`${citation.source_id || index}`}
                >
                  <SourceCard
                    citation={citation}
                    index={index}
                    highlighted={highlightedSource === (citation.display_number || index + 1)}
                    onHighlightClear={() => setHighlightedSource(null)}
                  />
                </div>
              ))}
            </div>
          </details>
        ) : null}
      </div>
    </article>
  );
}

export default ChatMessage;
