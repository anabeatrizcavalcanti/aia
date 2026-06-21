# Validação do corpus reformado bruto

## Status

PASS

## O que foi analisado

A validação examinou os arquivos PDF presentes em `corpus/raw/reformed/` e tentou associá-los aos quatro documentos esperados do corpus reformado principal do SolaBot.

## PDFs encontrados

- `A Confissão de Fé Batista de Londres de 1689.pdf`
- `A_Confissao_de_Fe_de_Westminster_1647_Or.pdf`
- `O CATECISMO DE HEIDELBERG (Portuguese).pdf`
- `Os-Canones-de-Dort.pdf`

## Associações realizadas

- `confissao-fe-westminster` foi associado a `A_Confissao_de_Fe_de_Westminster_1647_Or.pdf`.
- `canones-de-dort` foi associado a `Os-Canones-de-Dort.pdf`.
- `catecismo-heidelberg` foi associado a `O CATECISMO DE HEIDELBERG (Portuguese).pdf`.
- `confissao-batista-londres-1689` foi associado a `A Confissão de Fé Batista de Londres de 1689.pdf`.

## Pendências e riscos

A validação localizou os quatro documentos esperados e não encontrou ambiguidade nas associações por nome de arquivo.

## Resultado da validação

Os quatro documentos foram identificados. O manifesto `corpus/raw/reformed_manifest.json` foi criado ou atualizado com os caminhos reais dos PDFs.
