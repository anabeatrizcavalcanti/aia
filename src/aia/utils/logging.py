"""
Configuração inicial de logging do projeto.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para módulos do AIA.
    """
    return logging.getLogger(name)
