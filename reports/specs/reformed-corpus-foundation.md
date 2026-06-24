# Corpus reformado: fundação documental

## Status

PASS

## Registro

Os quatro PDFs do corpus reformado foram localizados em `corpus/raw/reformed/` e associados aos identificadores oficiais do projeto.

| document_id | Arquivo |
| --- | --- |
| `confissao-fe-westminster` | `corpus/raw/reformed/A_Confissao_de_Fe_de_Westminster_1647_Or.pdf` |
| `canones-de-dort` | `corpus/raw/reformed/Os-Canones-de-Dort.pdf` |
| `catecismo-heidelberg` | `corpus/raw/reformed/O CATECISMO DE HEIDELBERG (Portuguese).pdf` |
| `confissao-batista-londres-1689` | `corpus/raw/reformed/A Confissão de Fé Batista de Londres de 1689.pdf` |

O manifesto `corpus/raw/reformed_manifest.json` foi criado com esses caminhos e com `status=raw_validated` para todos os documentos.

## Análise estrutural

A análise inicial foi feita com PyMuPDF e gerou arquivos Markdown e JSON em `corpus/reports/structure_analysis/`.

| document_id | Páginas | Estrutura observada |
| --- | ---: | --- |
| `confissao-fe-westminster` | 60 | capítulos e seções |
| `canones-de-dort` | 33 | capítulos doutrinários, artigos, rejeições e conclusão |
| `catecismo-heidelberg` | 29 | partes, Dias do Senhor e perguntas-respostas |
| `confissao-batista-londres-1689` | 81 | capítulos e parágrafos numerados |

## Scripts envolvidos

- `scripts/corpus/validate_reformed_raw_corpus.py`
- `scripts/corpus/analyze_reformed_pdf_structure.py`
- `scripts/pipeline/extract_reformed_corpus.py`
- `scripts/pipeline/normalize_reformed_corpus.py`
- `scripts/pipeline/chunk_reformed_corpus.py`

## Validação

Foram executados os scripts de validação e análise estrutural, a compilação dos scripts principais e o teste `tests/test_reformed_corpus_structure.py`.

Resultado registrado: `5 passed` na primeira validação da estrutura do corpus.

## Observações

- A associação dos PDFs depende de heurísticas de nome de arquivo.
- Não foi usado OCR.
- As contagens iniciais de referências e notas eram aproximações; depois foram substituídas por estruturas mais específicas nos JSONs revisados.
- Nenhum conteúdo doutrinário foi alterado manualmente.
