import React from "react";

const LoadingBubble = React.forwardRef(function LoadingBubble(_props, ref) {
  return (
    <div className="loading-message" ref={ref} aria-live="polite">
      <div className="loading-card">
        <span className="thinking-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span>Consultando documentos e verificando fontes...</span>
      </div>
    </div>
  );
});

export default LoadingBubble;
