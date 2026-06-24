# Extração e normalização do corpus reformado

## Status

PARTIAL

## Registro

Os quatro PDFs do corpus reformado foram extraídos com PyMuPDF e normalizados sem alteração interpretativa do texto. A rastreabilidade por página foi preservada nos arquivos `.json` e `.txt`.

| document_id | Páginas extraídas | Páginas normalizadas |
| --- | ---: | ---: |
| `confissao-fe-westminster` | 60 | 60 |
| `canones-de-dort` | 33 | 33 |
| `catecismo-heidelberg` | 29 | 29 |
| `confissao-batista-londres-1689` | 81 | 81 |

## Entradas

- `corpus/raw/reformed_manifest.json`
- relatórios estruturais em `corpus/reports/structure_analysis/`
- auditorias em `reports/audits/`

## Saídas

- arquivos extraídos em `corpus/processed/extracted/reformed/`
- arquivos normalizados em `corpus/processed/normalized/reformed/`
- relatório de extração em `corpus/reports/extraction/`
- relatório de normalização em `corpus/reports/normalization/`

## Extração

A extração preservou `document_id`, título, tipo documental, tradição, caminho do PDF e texto por página.

O status ficou `PARTIAL` porque a página 1 da Confissão de Fé de Westminster não retornou texto extraível. O restante do corpus gerou texto utilizável.

## Normalização

A normalização aplicada foi mecânica: espaços, quebras de linha, caracteres invisíveis e hifenização segura. Marcadores estruturais como capítulos, artigos, perguntas, respostas, parágrafos e referências foram preservados.

## Validação

Comandos executados nesta etapa:

```bash
python scripts/pipeline/extract_reformed_corpus.py
python scripts/pipeline/normalize_reformed_corpus.py
python -m py_compile scripts/pipeline/extract_reformed_corpus.py
python -m py_compile scripts/pipeline/normalize_reformed_corpus.py
python -m pytest tests/test_extraction_normalization.py
```

Resultado registrado: `9 passed`.

## Observações

- Westminster mantém uma página inicial sem texto extraível.
- Algumas páginas ficaram com zona preliminar `unknown`; isso foi mantido em vez de forçar classificação.
- Não houve OCR, chamada à OpenAI, geração de chunks, embeddings ou índice vetorial.
- Nenhum conteúdo doutrinário foi reescrito.
