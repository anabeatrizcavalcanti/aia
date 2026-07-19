import React, { useEffect, useRef, useState } from "react";
import {
  BookOpen,
  BookOpenText,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Cross,
  Church,
  Globe,
  Link2,
  Loader2,
  RotateCcw,
  Scale,
  Send,
  Shield,
  Sprout,
  Waves,
  Sparkles,
  Star,
  Users,
} from "lucide-react";

import ChatMessage from "./components/ChatMessage.jsx";
import Header from "./components/Header.jsx";
import IntroModal from "./components/IntroModal.jsx";
import LoadingBubble from "./components/LoadingBubble.jsx";
import SuggestionCard from "./components/SuggestionCard.jsx";

const DOCTRINAL_SUGGESTIONS = [
  {
    question: "Do que se trata a justificação?",
    title: "Justificação",
    detail: "fé, perdão e justiça de Cristo",
    icon: Scale,
  },
  {
    question: "O que é ser regenerado?",
    title: "Regeneração",
    detail: "nova vida e obra do Espírito",
    icon: Sprout,
  },
  {
    question: "O que é o batismo?",
    title: "Batismo",
    detail: "sinal, ordenança e vida cristã",
    icon: Waves,
  },
  {
    question: "Qual é o papel das Escrituras?",
    title: "Escrituras",
    detail: "autoridade, inspiração e regra de fé",
    icon: BookOpenText,
  },
  {
    question: "O que é a perseverança dos santos?",
    title: "Perseverança",
    detail: "graça, fé e segurança cristã",
    icon: Shield,
  },
];

const NORMATIVE_SUGGESTIONS = [
  {
    question: "Qual os deveres da igreja local?",
    title: "Igreja local",
    detail: "vida, deveres e organização",
    icon: Church,
  },
  {
    question: "Quais são os deveres éticos do pastor?",
    title: "Ética ministerial",
    detail: "pastor, igreja e Aliança",
    icon: Star,
  },
  {
    question: "O que a Aliança estabelece sobre missões?",
    title: "Missões",
    detail: "campos missionários e expansão",
    icon: Globe,
  },
  {
    question: "Como funciona a filiação à Aliança?",
    title: "Filiação",
    detail: "igrejas e vínculo institucional",
    icon: Link2,
  },
  {
    question: "Como funciona o processo de ordenação?",
    title: "Ordenação",
    detail: "ministério, curso e avaliação",
    icon: Users,
  },
];

const SUGGESTIONS = [...DOCTRINAL_SUGGESTIONS, ...NORMATIVE_SUGGESTIONS];

const FALLBACK_DOCUMENTS = [
  {
    document_id: "confissao-fe-westminster",
    title: "Confissão de Fé de Westminster",
    document_type: "confession_of_faith",
  },
  {
    document_id: "canones-de-dort",
    title: "Cânones de Dort",
    document_type: "doctrinal_canons",
  },
  {
    document_id: "catecismo-heidelberg",
    title: "Catecismo de Heidelberg",
    document_type: "catechism",
  },
  {
    document_id: "confissao-batista-londres-1689",
    title: "Confissão Batista de Londres de 1689",
    document_type: "confession_of_faith",
  },
  {
    document_id: "confissao-fe-congregacional-alianca",
    title: "Confissão de Fé Congregacional",
    document_type: "confession_of_faith",
  },
  {
    document_id: "constituicao-alianca-2022",
    title: "Constituição da Aliança",
    document_type: "constitution",
  },
  {
    document_id: "regimento-interno-alianca-2022",
    title: "Regimento Interno da Aliança",
    document_type: "internal_regiment",
  },
  {
    document_id: "codigo-etica-ministro-alianca",
    title: "Código de Ética do Ministro Congregacional",
    document_type: "normative_ethics",
  },
  {
    document_id: "resolucao-alianca-01-2020",
    title: "Resolução Aliança nº 01/2020",
    document_type: "administrative_resolution",
  },
];

const INITIAL_MESSAGE = {
  id: "welcome",
  role: "bot",
  status: "intro",
  answer:
    "Olá! Sou a AIA, Assistente Inteligente da ALIANÇA. Respondo perguntas doutrinárias e normativas com base nos documentos processados e apresento as fontes utilizadas. Quando não houver evidência documental suficiente, a resposta será recusada.",
  metadata: {
    note: "As respostas são limitadas aos documentos atualmente processados na base documental.",
  },
  citations: [],
};

function iconForSuggestion(suggestion) {
  const text = `${suggestion.title || ""} ${suggestion.question || ""}`.toLowerCase();
  if (text.includes("justifica")) return Scale;
  if (text.includes("ordena")) return Users;
  if (text.includes("batismo") || text.includes("sacramento")) return Waves;
  if (text.includes("igreja")) return Church;
  if (text.includes("persever") || text.includes("salvação") || text.includes("salvacao")) return Shield;
  if (text.includes("miss") || text.includes("campo") || text.includes("emancipa")) return Globe;
  if (text.includes("regenera")) return Sprout;
  if (text.includes("ética") || text.includes("etica") || text.includes("pastor")) return Star;
  if (text.includes("expia") || text.includes("reden")) return Cross;
  if (text.includes("escritura") || text.includes("bíblia") || text.includes("biblia")) return BookOpenText;
  if (text.includes("fili")) return Link2;
  if (text.includes("alian") || text.includes("constitui") || text.includes("regimento") || text.includes("pacto") || text.includes("mediador")) return BookOpen;
  return BookOpenText;
}

function hydrateSuggestion(suggestion, index = 0) {
  const question = String(suggestion.question || "").trim();
  const fallbackTitle = question ? question.replace(/[?.!]+$/, "") : "Pergunta sugerida";
  return {
    question,
    title: String(suggestion.title || fallbackTitle).trim(),
    detail: String(suggestion.detail || "continuação da conversa").trim(),
    icon: iconForSuggestion(suggestion),
    id: `${question || fallbackTitle}-${index}`,
  };
}

function createMessageId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function buildChatHistory(messages, maxMessages = 8) {
  return messages
    .filter((message) => message.id !== "welcome")
    .filter((message) => message.role === "user" || message.role === "bot")
    .slice(-maxMessages)
    .map((message) => {
      if (message.role === "user") {
        return {
          role: "user",
          content: String(message.question || "").slice(0, 1600),
        };
      }
      return {
        role: "assistant",
        content: String(message.answer || message.message || "").slice(0, 1600),
      };
    })
    .filter((message) => message.content.trim());
}

function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [availableDocuments, setAvailableDocuments] = useState(FALLBACK_DOCUMENTS);
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true);
  const [showIntro, setShowIntro] = useState(() => {
    try {
      return localStorage.getItem("aia-intro-seen") !== "true";
    } catch {
      return true;
    }
  });
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [dynamicSuggestions, setDynamicSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionMode, setSuggestionMode] = useState("topics");
  const [questionSuggestionsEnabled, setQuestionSuggestionsEnabled] = useState(() => {
    try {
      return localStorage.getItem("aia-question-suggestions") !== "false";
    } catch {
      return true;
    }
  });
  const topicScrollRef = useRef(null);
  const questionInputRef = useRef(null);
  const loadingBubbleRef = useRef(null);

  const conversationStarted = messages.some((message) => message.role === "user");
  const hasDynamicSuggestions = dynamicSuggestions.length > 0;
  const isQuestionMode = hasDynamicSuggestions && suggestionMode === "questions";
  const conversationSuggestions = isQuestionMode ? dynamicSuggestions : suggestionsLoading && !hasDynamicSuggestions ? [] : SUGGESTIONS;
  const suggestionLabel = isQuestionMode ? "Perguntas" : "Tópicos";
  const suggestionPanelTitle = isQuestionMode ? "Perguntas sugeridas" : "Tópicos sugeridos";
  const visibleMessages = conversationStarted ? messages.filter((message) => message.id !== "welcome") : [];

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("aia-question-suggestions", String(questionSuggestionsEnabled));
    } catch {
      // Preferir não interromper a conversa se o navegador bloquear localStorage.
    }
  }, [questionSuggestionsEnabled]);

  useEffect(() => {
    const input = questionInputRef.current;
    if (!input) return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 72)}px`;
  }, [question]);

  useEffect(() => {
    if (!isLoading) return;
    window.setTimeout(() => {
      loadingBubbleRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 60);
  }, [isLoading]);

  async function fetchDocuments() {
    setIsDocumentsLoading(true);
    try {
      const response = await fetch("/api/documents");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      if (Array.isArray(data.documents) && data.documents.length) {
        setAvailableDocuments(data.documents);
      }
    } catch {
      setAvailableDocuments(FALLBACK_DOCUMENTS);
    } finally {
      setIsDocumentsLoading(false);
    }
  }

  function closeIntro() {
    setShowIntro(false);
    try {
      localStorage.setItem("aia-intro-seen", "true");
    } catch {
      // Fechar o modal não deve depender do armazenamento local do navegador.
    }
  }

  async function readJsonResponse(response, label) {
    const text = await response.text();
    if (!text.trim()) {
      throw new Error(`${label} retornou HTTP ${response.status} sem corpo.`);
    }
    let payload;
    try {
      payload = JSON.parse(text);
    } catch {
      throw new Error(`${label} retornou HTTP ${response.status} sem JSON válido: ${text.slice(0, 180)}`);
    }
    if (!response.ok) {
      const message = payload.message || payload.detail || `HTTP ${response.status}`;
      throw new Error(`${label}: ${message}`);
    }
    return payload;
  }

  async function sendQuestion(nextQuestion) {
    const cleanQuestion = nextQuestion.trim();
    if (!cleanQuestion || isLoading) return;
    const chatHistory = buildChatHistory(messages);

    setMessages((current) => [
      ...current,
      { id: createMessageId(), role: "user", question: cleanQuestion },
    ]);
    setQuestion("");
    setSuggestionsOpen(false);
    setDynamicSuggestions([]);
    setSuggestionMode("questions");
    setIsLoading(true);
    let answerPayload = null;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: cleanQuestion,
          document_id: null,
          chunk_type: null,
          history: chatHistory,
        }),
      });

      const payload = await readJsonResponse(response, "API de chat");
      answerPayload = payload;
      setMessages((current) => [
        ...current,
        { ...payload, id: createMessageId(), role: "bot" },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: createMessageId(),
          role: "bot",
          status: "error",
          answer: `Erro ao consultar a API local: ${error.message}`,
          citations: [],
          metadata: {},
        },
      ]);
    } finally {
      setIsLoading(false);
    }

    if (answerPayload && questionSuggestionsEnabled) {
      refreshSuggestions(cleanQuestion, answerPayload);
    } else if (answerPayload) {
      setSuggestionsLoading(false);
      setDynamicSuggestions([]);
      setSuggestionMode("topics");
    }
  }

  async function refreshSuggestions(lastQuestion, answerPayload) {
    if (!questionSuggestionsEnabled) return;
    setSuggestionsLoading(true);
    try {
      const response = await fetch("/api/suggestions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: lastQuestion,
          answer: answerPayload.answer,
          used_documents: answerPayload.used_documents || [],
          citations: answerPayload.citations || [],
          max_suggestions: 6,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await readJsonResponse(response, "API de sugestões");
      const nextSuggestions = Array.isArray(payload.suggestions)
        ? payload.suggestions
            .map((suggestion, index) => hydrateSuggestion(suggestion, index))
            .filter((suggestion) => suggestion.question)
        : [];

      if (nextSuggestions.length) {
        setDynamicSuggestions(nextSuggestions);
        setSuggestionMode("questions");
        setSuggestionsOpen(true);
      }
    } catch {
      setDynamicSuggestions([]);
      setSuggestionMode("topics");
    } finally {
      setSuggestionsLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendQuestion(question);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendQuestion(question);
    }
  }

  function clearConversation() {
    setMessages([INITIAL_MESSAGE]);
    setQuestion("");
    setSuggestionsOpen(false);
    setDynamicSuggestions([]);
    setSuggestionMode("topics");

    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function toggleQuestionSuggestions() {
    setQuestionSuggestionsEnabled((current) => {
      const next = !current;
      if (!next) {
        setSuggestionsLoading(false);
        setDynamicSuggestions([]);
        setSuggestionMode("topics");
      }
      return next;
    });
  }

  function scrollSuggestionStrip(direction) {
    topicScrollRef.current?.scrollBy({
      left: direction * 320,
      behavior: "smooth",
    });
  }

  function handleSuggestionWheel(event) {
    if (!topicScrollRef.current || Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
    event.preventDefault();
    topicScrollRef.current.scrollLeft += event.deltaY;
  }

  return (
    <div className="app-shell" aria-label="AIA">
      {showIntro ? (
        <IntroModal documents={availableDocuments} isLoadingDocuments={isDocumentsLoading} onClose={closeIntro} />
      ) : null}

      <Header onIntroOpen={() => setShowIntro(true)} />

      <main className={`main-content ${!conversationStarted ? "landing-main" : ""}`} aria-label="Conversa com o AIA">
        <div className="message-stack" aria-live="polite">
          {visibleMessages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {isLoading ? <LoadingBubble ref={loadingBubbleRef} /> : null}

          {!conversationStarted ? (
            <section className="quick-start" aria-label="Tópicos sugeridos">
              <p className="quick-start-intro">Faça uma pergunta doutrinária ou normativa, ou escolha um tópico abaixo.</p>
              <div className="suggestion-groups">
                <div className="suggestion-group" aria-label="Tópicos doutrinários sugeridos">
                  <p className="suggestion-group-title">Doutrina</p>
                  <div className="suggestion-grid">
                    {DOCTRINAL_SUGGESTIONS.map((suggestion) => (
                      <SuggestionCard
                        key={suggestion.question}
                        suggestion={suggestion}
                        disabled={isLoading}
                        onSelect={() => sendQuestion(suggestion.question)}
                      />
                    ))}
                  </div>
                </div>

                <div className="suggestion-group" aria-label="Tópicos normativos sugeridos">
                  <p className="suggestion-group-title">Normas e denominação</p>
                  <div className="suggestion-grid">
                    {NORMATIVE_SUGGESTIONS.map((suggestion) => (
                      <SuggestionCard
                        key={suggestion.question}
                        suggestion={suggestion}
                        disabled={isLoading}
                        onSelect={() => sendQuestion(suggestion.question)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </section>
          ) : null}
        </div>
      </main>

      <section className="composer-dock" aria-label="Enviar pergunta">
        <div className="composer-inner">
          {conversationStarted ? (
            <div className="compact-suggestions">
              {suggestionsOpen ? (
                <div className={`compact-suggestions-panel ${isQuestionMode ? "question-suggestions-panel" : "topic-suggestions-panel"}`}>
                  <div className="compact-suggestions-header">
                    <p>{suggestionPanelTitle}</p>
                    {hasDynamicSuggestions ? (
                      <div className="suggestion-mode-switch" aria-label="Alternar sugestões">
                        <button
                          type="button"
                          className={isQuestionMode ? "active" : ""}
                          onClick={() => setSuggestionMode("questions")}
                        >
                          Perguntas
                        </button>
                        <button
                          type="button"
                          className={!isQuestionMode ? "active" : ""}
                          onClick={() => setSuggestionMode("topics")}
                        >
                          Tópicos
                        </button>
                      </div>
                    ) : null}
                  </div>
                  {isQuestionMode ? (
                    <div className="compact-suggestion-list">
                      {suggestionsLoading ? <span className="suggestions-loading">Gerando novas perguntas...</span> : null}
                      {conversationSuggestions.map((suggestion) => {
                        const Icon = suggestion.icon;
                        return (
                          <button
                            key={suggestion.id || suggestion.question}
                            type="button"
                            className="topic-pill question-pill"
                            disabled={isLoading}
                            onClick={() => sendQuestion(suggestion.question)}
                            title={suggestion.question}
                          >
                            <Icon size={14} aria-hidden="true" />
                            <span>{suggestion.question}</span>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="compact-topic-groups">
                      <div className="compact-topic-group">
                        <p className="compact-topic-group-title">Doutrina</p>
                        <div className="compact-topic-row">
                          {DOCTRINAL_SUGGESTIONS.map((suggestion) => {
                            const Icon = suggestion.icon;
                            return (
                              <button
                                key={suggestion.question}
                                type="button"
                                className="topic-pill"
                                disabled={isLoading}
                                onClick={() => sendQuestion(suggestion.question)}
                                title={suggestion.question}
                              >
                                <Icon size={14} aria-hidden="true" />
                                <span>{suggestion.title}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="compact-topic-group">
                        <p className="compact-topic-group-title">Normas e denominação</p>
                        <div className="compact-topic-row">
                          {NORMATIVE_SUGGESTIONS.map((suggestion) => {
                            const Icon = suggestion.icon;
                            return (
                              <button
                                key={suggestion.question}
                                type="button"
                                className="topic-pill"
                                disabled={isLoading}
                                onClick={() => sendQuestion(suggestion.question)}
                                title={suggestion.question}
                              >
                                <Icon size={14} aria-hidden="true" />
                                <span>{suggestion.title}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : null}

              <div className="compact-suggestion-strip">
                <button
                  className="strip-action"
                  type="button"
                  onClick={() => setSuggestionsOpen((current) => !current)}
                  aria-expanded={suggestionsOpen}
                >
                  {suggestionsOpen ? <ChevronDown size={13} aria-hidden="true" /> : <ChevronUp size={13} aria-hidden="true" />}
                  <span>{suggestionLabel}</span>
                </button>

                <span className="strip-divider" aria-hidden="true" />

                {hasDynamicSuggestions ? (
                  <>
                    <button
                      className="strip-action muted"
                      type="button"
                      onClick={() => setSuggestionMode((current) => (current === "questions" ? "topics" : "questions"))}
                    >
                      <span>{isQuestionMode ? "Ver tópicos" : "Ver perguntas"}</span>
                    </button>

                    <span className="strip-divider" aria-hidden="true" />
                  </>
                ) : null}

                <button
                  className={`suggestion-ai-toggle ${questionSuggestionsEnabled ? "on" : ""}`}
                  type="button"
                  onClick={toggleQuestionSuggestions}
                  aria-pressed={questionSuggestionsEnabled}
                  title={questionSuggestionsEnabled ? "Desativar sugestões de perguntas" : "Ativar sugestões de perguntas"}
                >
                  <Sparkles size={12} aria-hidden="true" />
                  <span>{questionSuggestionsEnabled ? "Sugestões IA" : "Sugestões off"}</span>
                </button>

                <span className="strip-divider" aria-hidden="true" />

                <button
                  className="scroll-control"
                  type="button"
                  onClick={() => scrollSuggestionStrip(-1)}
                  aria-label="Deslizar sugestões para a esquerda"
                >
                  <ChevronLeft size={13} aria-hidden="true" />
                </button>

                <div
                  ref={topicScrollRef}
                  className="topic-scroll"
                  aria-label={isQuestionMode ? "Perguntas sugeridas" : "Tópicos rápidos"}
                  onWheel={handleSuggestionWheel}
                >
                  {suggestionsLoading && !hasDynamicSuggestions ? (
                    <span className="topic-chip ghost-chip">Gerando perguntas...</span>
                  ) : null}
                  {conversationSuggestions.map((suggestion) => {
                    const Icon = suggestion.icon;
                    return (
                      <button
                        key={suggestion.id || suggestion.question}
                        type="button"
                        className={`topic-chip ${isQuestionMode ? "question-chip" : ""}`}
                        disabled={isLoading}
                        onClick={() => sendQuestion(suggestion.question)}
                        title={suggestion.question}
                      >
                        <Icon size={isQuestionMode ? 14 : 12} aria-hidden="true" />
                        <span>{isQuestionMode ? suggestion.question : suggestion.title}</span>
                      </button>
                    );
                  })}
                </div>

                <button
                  className="scroll-control"
                  type="button"
                  onClick={() => scrollSuggestionStrip(1)}
                  aria-label="Deslizar sugestões para a direita"
                >
                  <ChevronRight size={13} aria-hidden="true" />
                </button>

                <span className="strip-divider" aria-hidden="true" />

                <button className="strip-action muted" type="button" onClick={clearConversation}>
                  <RotateCcw size={12} aria-hidden="true" />
                  <span>Limpar</span>
                </button>
              </div>
            </div>
          ) : null}

          <form className="composer" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="questionInput">
              Pergunta
            </label>

            <div className="composer-input-wrap">
              <div className="input-row">
                <textarea
                  ref={questionInputRef}
                  id="questionInput"
                  value={question}
                  maxLength={1200}
                  rows={1}
                  placeholder="Digite uma pergunta doutrinária ou normativa..."
                  onChange={(event) => setQuestion(event.target.value.slice(0, 1200))}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                />
              </div>

              <button className="send-button" type="submit" disabled={isLoading || !question.trim()} aria-label="Enviar pergunta">
                {isLoading ? <Loader2 size={15} className="spin" aria-hidden="true" /> : <Send size={15} aria-hidden="true" />}
              </button>
            </div>
          </form>

          <p className="composer-disclaimer">
            A AIA pode cometer erros. Por isso, confira as fontes e documentos relevantes.
          </p>
        </div>
      </section>
    </div>
  );
}

export default App;
