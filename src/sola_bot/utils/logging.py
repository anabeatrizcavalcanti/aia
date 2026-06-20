"""
Configuração inicial de logging do projeto.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para módulos do SolaBot.
    """
    return logging.getLogger(name)
