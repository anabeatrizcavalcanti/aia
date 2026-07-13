"""Inicia a interface web local do SolaBot."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main() -> None:
    """Sobe a API local com o frontend estático."""
    try:
        import uvicorn

        host = os.getenv("HOST", "127.0.0.1")
        port = int(os.getenv("PORT", "8000"))
        uvicorn.run(
            "sola_bot.api.app:app",
            host=host,
            port=port,
            reload=False,
        )
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependência"
        print(
            f"Dependência ausente: {missing}. Instale as dependências do requirements.txt "
            "antes de iniciar a interface web.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
