import React, { useEffect, useState } from "react";
import { ChevronRight, FileText, Search, ShieldCheck, X, XCircle } from "lucide-react";

const STEPS = [
  {
    icon: Search,
    title: "Faça uma pergunta",
    description: "Digite uma questão doutrinária ou normativa em linguagem natural ou escolha um dos tópicos sugeridos.",
  },
  {
    icon: ShieldCheck,
    title: "Receba uma resposta fundamentada",
    description: "O assistente consulta documentos da Aliança e responde com fontes marcadas no texto.",
  },
  {
    icon: FileText,
    title: "Veja os trechos usados",
    description: "Cada número de fonte leva ao documento, à referência e ao trecho recuperado.",
  },
  {
    icon: XCircle,
    title: "Sem base suficiente, sem resposta",
    description: "Quando os documentos não sustentam uma resposta segura, o bot informa essa limitação.",
  },
];

function IntroModal({ documents = [], isLoadingDocuments = false, onClose }) {
  const [tab, setTab] = useState("intro");

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="intro-modal-shell" role="dialog" aria-modal="true" aria-labelledby="introModalTitle">
      <button className="intro-modal-backdrop" type="button" aria-label="Fechar introdução" onClick={onClose} />

      <div className="intro-modal-panel">
        <header className="intro-modal-header">
          <div className="intro-modal-title-block">
            <h2 id="introModalTitle">Conheça a AIA</h2>
            <span>Assistente Inteligente da ALIANÇA com fontes rastreáveis</span>
          </div>

          <button className="intro-modal-close" type="button" onClick={onClose} aria-label="Fechar introdução">
            <X size={18} aria-hidden="true" />
          </button>

          <div className="intro-modal-tabs" aria-label="Seções da introdução">
            <button className={tab === "intro" ? "active" : ""} type="button" onClick={() => setTab("intro")}>
              Como usar
            </button>
            <button className={tab === "docs" ? "active" : ""} type="button" onClick={() => setTab("docs")}>
              Documentos
            </button>
          </div>
        </header>

        <div className={`intro-modal-body ${tab === "intro" ? "is-intro" : "is-docs"}`}>
          {tab === "intro" ? (
            <div className="intro-modal-intro">
              <p>
                A AIA é uma assistente inteligente de consulta documental que responde a partir de documentos doutrinários, regimentais,
                éticos e administrativos da Aliança. Ela encontra trechos relevantes, organiza uma resposta clara e mostra quais fontes sustentam cada ponto. É simples de usar:
                escreva sua pergunta, envie e confira as fontes ao final.
              </p>

              <div className="intro-step-list">
                {STEPS.map((step) => {
                  const Icon = step.icon;
                  return (
                    <div className="intro-step" key={step.title}>
                      <span className="intro-step-icon" aria-hidden="true">
                        <Icon size={14} />
                      </span>
                      <div>
                        <strong>{step.title}</strong>
                        <p>{step.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="intro-modal-docs">
              {isLoadingDocuments ? (
                <p>Carregando a base documental atual da Aliança.</p>
              ) : (
                <p>
                  A base documental atual contém {documents.length} {documents.length === 1 ? "documento" : "documentos"} processados.
                </p>
              )}

              {isLoadingDocuments ? <span className="intro-docs-status">Carregando documentos...</span> : null}

              {!isLoadingDocuments && documents.length ? (
                <div className="intro-document-list">
                  {documents.map((document) => (
                    <article className="intro-document-item" key={document.document_id || document.title}>
                      <strong>{document.title}</strong>
                    </article>
                  ))}
                </div>
              ) : null}

              {!isLoadingDocuments && !documents.length ? (
                <span className="intro-docs-status">Não foi possível carregar a lista de documentos agora.</span>
              ) : null}
            </div>
          )}
        </div>

        <footer className="intro-modal-footer">
          <button type="button" onClick={onClose}>
            Começar a usar
            <ChevronRight size={14} aria-hidden="true" />
          </button>
        </footer>
      </div>
    </div>
  );
}

export default IntroModal;
