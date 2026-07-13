# Relatório da pipeline final de retrieval

## Status

PASS

## Configuração

{
  "source": "hierarchical_retriever",
  "final_context_top_k": 4,
  "max_total_context_chars": 18000,
  "max_context_chars_per_parent": 9000,
  "consolidate_by_parent_key": true,
  "deduplicate_included_chunks": true,
  "prefer_expanded_contexts": true,
  "reduce_introductory_context_for_doctrinal_queries": true,
  "keep_anchor_only_when_no_expanded_alternative": true,
  "preserve_document_diversity": true,
  "max_contexts_per_parent_key": 1,
  "include_context_package_header": true,
  "include_source_map": true,
  "default_filters": {
    "corpus_id": "reformed",
    "retrieval_namespace": "reformed_confessional"
  }
}

## Consultas

### O que é o batismo?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `3`
- Total de caracteres: `10543`
- Parent keys selecionados: `['confissao-batista-londres-1689::chapter::capitulo-29', 'confissao-fe-westminster::chapter::capitulo-xxviii', 'confissao-batista-londres-1689::chapter::capitulo-28']`
- Parent keys removidos ou fundidos: `{'fused_count': 2, 'removed': {'removed_introductory_anchor_only': []}, 'dropped_by_limit': []}`
- Decisões sobre anchor_only: `{'not_anchor_only': 3}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `confissao-batista-londres-1689::chapter::capitulo-29` | `confissao-batista-londres-1689` | `expanded_consolidated` | `doctrinal` | 4 | 4446 |
| 2 | `confissao-fe-westminster::chapter::capitulo-xxviii` | `confissao-fe-westminster` | `expanded` | `doctrinal` | 7 | 4190 |
| 3 | `confissao-batista-londres-1689::chapter::capitulo-28` | `confissao-batista-londres-1689` | `expanded` | `doctrinal` | 2 | 1907 |

### O que é necessário para a salvação?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `3`
- Total de caracteres: `15411`
- Parent keys selecionados: `['confissao-batista-londres-1689::chapter::capitulo-1', 'confissao-batista-londres-1689::chapter::capitulo-15', 'catecismo-heidelberg::group::dia-do-senhor-16']`
- Parent keys removidos ou fundidos: `{'fused_count': 1, 'removed': {'removed_introductory_anchor_only': []}, 'dropped_by_limit': ['confissao-batista-londres-1689::chapter::capitulo-14']}`
- Decisões sobre anchor_only: `{'not_anchor_only': 3}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `confissao-batista-londres-1689::chapter::capitulo-1` | `confissao-batista-londres-1689` | `expanded` | `doctrinal` | 2 | 5528 |
| 2 | `confissao-batista-londres-1689::chapter::capitulo-15` | `confissao-batista-londres-1689` | `expanded_consolidated` | `doctrinal` | 5 | 6853 |
| 3 | `catecismo-heidelberg::group::dia-do-senhor-16` | `catecismo-heidelberg` | `expanded` | `doctrinal` | 5 | 3030 |

### O que é eleição?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `1`
- Total de caracteres: `4126`
- Parent keys selecionados: `['canones-de-dort::chapter::primeiro-capitulo-da-doutrina']`
- Parent keys removidos ou fundidos: `{'fused_count': 4, 'removed': {'removed_introductory_anchor_only': []}, 'dropped_by_limit': []}`
- Decisões sobre anchor_only: `{'not_anchor_only': 1}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `canones-de-dort::chapter::primeiro-capitulo-da-doutrina` | `canones-de-dort` | `expanded_consolidated` | `doctrinal` | 12 | 4126 |

### O que é justificação?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `2`
- Total de caracteres: `9117`
- Parent keys selecionados: `['confissao-batista-londres-1689::chapter::capitulo-11', 'confissao-fe-westminster::chapter::capitulo-xi']`
- Parent keys removidos ou fundidos: `{'fused_count': 3, 'removed': {'removed_introductory_anchor_only': []}, 'dropped_by_limit': []}`
- Decisões sobre anchor_only: `{'not_anchor_only': 2}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `confissao-batista-londres-1689::chapter::capitulo-11` | `confissao-batista-londres-1689` | `expanded_consolidated` | `doctrinal` | 6 | 4665 |
| 2 | `confissao-fe-westminster::chapter::capitulo-xi` | `confissao-fe-westminster` | `expanded` | `doctrinal` | 6 | 4452 |

### O que a tradição reformada ensina sobre as Escrituras?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `1`
- Total de caracteres: `6721`
- Parent keys selecionados: `['confissao-batista-londres-1689::chapter::capitulo-1']`
- Parent keys removidos ou fundidos: `{'fused_count': 1, 'removed': {'removed_introductory_anchor_only': ['confissao-fe-westminster::section::pagina-12', 'canones-de-dort::section::pagina-1', 'confissao-fe-westminster::section::pagina-8']}, 'dropped_by_limit': []}`
- Decisões sobre anchor_only: `{'not_anchor_only': 1}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `confissao-batista-londres-1689::chapter::capitulo-1` | `confissao-batista-londres-1689` | `expanded_consolidated` | `doctrinal` | 4 | 6721 |

### O crente pode perder a salvação?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `3`
- Total de caracteres: `16624`
- Parent keys selecionados: `['confissao-fe-westminster::chapter::capitulo-xviii', 'canones-de-dort::chapter::quinto-capitulo-da-doutrina', 'confissao-batista-londres-1689::chapter::capitulo-18']`
- Parent keys removidos ou fundidos: `{'fused_count': 2, 'removed': {'removed_introductory_anchor_only': []}, 'dropped_by_limit': []}`
- Decisões sobre anchor_only: `{'not_anchor_only': 3}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `confissao-fe-westminster::chapter::capitulo-xviii` | `confissao-fe-westminster` | `expanded_consolidated` | `doctrinal` | 4 | 4705 |
| 2 | `canones-de-dort::chapter::quinto-capitulo-da-doutrina` | `canones-de-dort` | `expanded_consolidated` | `doctrinal` | 6 | 3545 |
| 3 | `confissao-batista-londres-1689::chapter::capitulo-18` | `confissao-batista-londres-1689` | `expanded` | `doctrinal` | 2 | 8374 |

### O que é regeneração?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `3`
- Total de caracteres: `16654`
- Parent keys selecionados: `['canones-de-dort::chapter::terceiro-e-quarto-capitulos-da-doutrina', 'confissao-batista-londres-1689::chapter::capitulo-13', 'confissao-batista-londres-1689::chapter::capitulo-15']`
- Parent keys removidos ou fundidos: `{'fused_count': 2, 'removed': {'removed_introductory_anchor_only': []}, 'dropped_by_limit': []}`
- Decisões sobre anchor_only: `{'not_anchor_only': 3}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `canones-de-dort::chapter::terceiro-e-quarto-capitulos-da-doutrina` | `canones-de-dort` | `expanded_consolidated` | `doctrinal` | 7 | 3813 |
| 2 | `confissao-batista-londres-1689::chapter::capitulo-13` | `confissao-batista-londres-1689` | `expanded` | `doctrinal` | 3 | 5988 |
| 3 | `confissao-batista-londres-1689::chapter::capitulo-15` | `confissao-batista-londres-1689` | `expanded` | `doctrinal` | 5 | 6853 |

### O que é expiação?

- Contextos recebidos da camada hierárquica: `5`
- Contextos finais: `2`
- Total de caracteres: `12442`
- Parent keys selecionados: `['confissao-batista-londres-1689::chapter::capitulo-11', 'confissao-batista-londres-1689::chapter::capitulo-15']`
- Parent keys removidos ou fundidos: `{'fused_count': 1, 'removed': {'removed_introductory_anchor_only': ['canones-de-dort::section::pagina-1']}, 'dropped_by_limit': ['confissao-batista-londres-1689::chapter::capitulo-2']}`
- Decisões sobre anchor_only: `{'not_anchor_only': 2}`
- Contextos introdutórios preservados: `[]`

| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | `confissao-batista-londres-1689::chapter::capitulo-11` | `confissao-batista-londres-1689` | `expanded_consolidated` | `doctrinal` | 5 | 5589 |
| 2 | `confissao-batista-londres-1689::chapter::capitulo-15` | `confissao-batista-londres-1689` | `expanded` | `doctrinal` | 5 | 6853 |

## Agregados

- Contextos hierárquicos recebidos: `40`
- Contextos finais após consolidação: `18`
- Contextos removidos ou fundidos: `16`
- Chunks deduplicados: `0`

Documentos preservados:

{
  "confissao-batista-londres-1689": 11,
  "confissao-fe-westminster": 3,
  "canones-de-dort": 3,
  "catecismo-heidelberg": 1
}

Tipos de chunk preservados:

{
  "confessional_paragraph": 19,
  "doctrinal_article": 7,
  "confessional_section": 4,
  "error_refutation": 3,
  "catechism_question_answer": 1
}

## Notas técnicas

- A deduplicação por `parent_key` reduz repetições de capítulo ou unidade documental.
- A deduplicação por `chunk_id` atua sobre os metadados do pacote final.
- Contextos introdutórios perdem prioridade quando a consulta é classificada como doutrinária.
- Contextos `anchor_only` são mantidos apenas quando passam pela ordenação e pelos limites do pacote.

## Limitações

- A pipeline não gera resposta textual ao usuário.
- A diversidade documental não força inclusão de documento com baixa pontuação.
- A consolidação usa metadados estruturais já presentes nos chunks.
