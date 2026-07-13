import React from "react";

function SuggestionCard({ suggestion, disabled, onSelect }) {
  const Icon = suggestion.icon;

  return (
    <button
      type="button"
      className="suggestion-card"
      disabled={disabled}
      onClick={onSelect}
      aria-label={`Enviar pergunta: ${suggestion.question}`}
    >
      <span className="suggestion-icon" aria-hidden="true">
        <Icon size={18} />
      </span>
      <span className="suggestion-copy">
        <strong>{suggestion.title}</strong>
        <small>{suggestion.detail}</small>
      </span>
    </button>
  );
}

export default SuggestionCard;
