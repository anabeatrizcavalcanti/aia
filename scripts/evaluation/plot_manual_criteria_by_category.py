"""Gera grafico de barras da verificacao manual por categoria."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


CATEGORIES = [
    "Doutrinaria\ngeral",
    "Doutrinaria\nespecifica",
    "Normativa\ngeral",
    "Normativa\nespecifica",
    "Multidocumental",
]

CRITERIA = [
    "Aderencia",
    "Fonte esperada",
    "Sem mistura",
    "Citacoes",
    "Completude",
    "Limitacao",
]

VALUES = np.array(
    [
        [100, 60, 90, 90, 90, 90],
        [100, 100, 100, 90, 70, 90],
        [100, 100, 90, 100, 70, 80],
        [100, 100, 100, 100, 70, 70],
        [70, 70, 80, 90, 50, 80],
    ],
    dtype=float,
)


def main() -> None:
    output_dir = Path("reports/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)

    x = np.arange(len(CATEGORIES))
    width = 0.12
    offsets = (np.arange(len(CRITERIA)) - (len(CRITERIA) - 1) / 2) * width

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
    ]

    fig, ax = plt.subplots(figsize=(11, 5.8))
    for index, (criterion, color) in enumerate(zip(CRITERIA, colors)):
        bars = ax.bar(x + offsets[index], VALUES[:, index], width, label=criterion, color=color)
        ax.bar_label(bars, labels=[f"{value:.0f}%" for value in VALUES[:, index]], padding=2, fontsize=7)

    ax.set_title("Verificacao manual por categoria e criterio", fontsize=13, weight="bold")
    ax.set_ylabel("Atendimento ao criterio (%)")
    ax.set_ylim(0, 112)
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORIES)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)

    fig.tight_layout()
    fig.savefig(output_dir / "manual_criteria_by_category.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "manual_criteria_by_category.svg", bbox_inches="tight")


if __name__ == "__main__":
    main()
