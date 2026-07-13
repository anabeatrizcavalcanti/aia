import React from "react";

function Header({ onIntroOpen }) {
  return (
    <header className="hero-header">
      <div className="header-inner">
        <div className="brand-copy">
          <p className="eyebrow">Assistente documental da Aliança</p>
          <h1>FonteAliança</h1>
          <div className="brand-subline">
            <p>Consulta doutrinária e normativa com fontes rastreáveis.</p>
          </div>
        </div>

        <button className="intro-help-button" type="button" onClick={onIntroOpen} aria-label="Abrir guia de uso">
          ?
        </button>
      </div>
    </header>
  );
}

export default Header;
