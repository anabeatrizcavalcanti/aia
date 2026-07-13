# Índice vetorial ChromaDB e validação de retrieval

## Status

PASS

## Objetivo da etapa

Criar uma collection ChromaDB persistente para o corpus doutrinário e normativo da Aliança e validar retrieval básico sem gerar respostas com LLM.

## Entradas utilizadas

- `corpus/processed/embeddings/alliance/openai_embeddings.jsonl`
- `corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/alliance/embedding_manifest.json`
- `reports/specs/openai-embeddings.md`

## Índice ChromaDB

- Collection: `solabot_alliance_v1`
- Diretório persistente: `corpus/indexes/chroma/alliance`
- Métrica: `cosine`
- Embeddings lidos: 1115
- Chunks indexados: 1115
- Documentos na collection: 1115
- Modelo usado para consultas: `text-embedding-3-large`

## Metadados preservados

`chunk_id`, `corpus_id`, `retrieval_namespace`, `document_id`, `doc_id`, `document`, `document_title`, `document_type`, `source_category`, `denomination`, `tradition`, `tradition_family`, `tradition_branch`, `language`, `chunk_type`, `content_role`, `is_doctrinal`, `document_structure_type`, `section_title`, `section_reference`, `subsection_title`, `chapter_title`, `chapter_reference`, `article_number`, `paragraph_number`, `paragraph_label`, `paragraph_number_roman`, `inciso`, `alinea`, `full_reference`, `biblical_references`, `page_start`, `page_end`, `source_path`, `normalized_source`, `text_hash`

## Consultas de validação

### O que a Confissão de Fé Congregacional ensina sobre justificação?

- Resultados retornados: 5
- Observação: A consulta recuperou a Confissão de Fé Congregacional para um tema doutrinário.
- `confissao-fe-congregacional-alianca_capitulo-xii_paragrafo-i` | `confissao-fe-congregacional-alianca` | `confession_paragraph` | páginas 16-16 | distância 0.24271273612976074
- `confissao-fe-congregacional-alianca_capitulo-xii_paragrafo-ii` | `confissao-fe-congregacional-alianca` | `confession_paragraph` | páginas 16-16 | distância 0.284932017326355
- `confissao-fe-congregacional-alianca_capitulo-xii_paragrafo-vi` | `confissao-fe-congregacional-alianca` | `confession_paragraph` | páginas 17-17 | distância 0.3167968988418579

### Quais documentos uma igreja precisa apresentar para se filiar à Aliança?

- Resultados retornados: 5
- Observação: A consulta normativa recuperou Constituição e/ou Regimento Interno.
- `regimento-interno-alianca-2022_artigo-007` | `regimento-interno-alianca-2022` | `normative_article` | páginas 3-3 | distância 0.2965828776359558
- `regimento-interno-alianca-2022_artigo-008` | `regimento-interno-alianca-2022` | `normative_article` | páginas 3-3 | distância 0.3051018714904785
- `constituicao-alianca-2022_artigo-005_paragrafo-1o_inciso-v` | `constituicao-alianca-2022` | `inciso` | páginas 4-4 | distância 0.30510807037353516

### Quais são os deveres de uma igreja local?

- Resultados retornados: 5
- Observação: A consulta normativa recuperou Constituição e/ou Regimento Interno.
- `regimento-interno-alianca-2022_artigo-020` | `regimento-interno-alianca-2022` | `normative_article` | páginas 6-7 | distância 0.3338603377342224
- `confissao-batista-londres-1689_capitulo-26_paragrafo-14` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 71-71 | distância 0.37936270236968994
- `confissao-batista-londres-1689_capitulo-26_paragrafo-12` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 70-70 | distância 0.38181984424591064

### Como funciona o processo de ordenação de ministros?

- Resultados retornados: 5
- Observação: A consulta recuperou documentos normativos sobre ordenação ou emancipação.
- `regimento-interno-alianca-2022_artigo-036` | `regimento-interno-alianca-2022` | `normative_article` | páginas 10-10 | distância 0.5065830945968628
- `regimento-interno-alianca-2022_artigo-026` | `regimento-interno-alianca-2022` | `normative_article` | páginas 8-8 | distância 0.5338952541351318
- `regimento-interno-alianca-2022_artigo-023` | `regimento-interno-alianca-2022` | `normative_article` | páginas 7-7 | distância 0.5544495582580566

### Quais são os deveres éticos do pastor em relação à Aliança?

- Resultados retornados: 5
- Observação: A consulta recuperou o Código de Ética do Ministro Congregacional.
- `codigo-etica-ministro-alianca_artigo-011` | `codigo-etica-ministro-alianca` | `ethics_article` | páginas 5-5 | distância 0.2763436436653137
- `codigo-etica-ministro-alianca_artigo-012` | `codigo-etica-ministro-alianca` | `ethics_article` | páginas 5-6 | distância 0.3495140075683594
- `codigo-etica-ministro-alianca_artigo-009` | `codigo-etica-ministro-alianca` | `ethics_article` | páginas 3-4 | distância 0.3536621332168579

### Quais os critérios para emancipação de campos missionários?

- Resultados retornados: 5
- Observação: A consulta recuperou documentos normativos sobre ordenação ou emancipação.
- `resolucao-alianca-01-2020_considerando-01` | `resolucao-alianca-01-2020` | `resolution_considerando` | páginas 2-2 | distância 0.40881526470184326
- `resolucao-alianca-01-2020_considerando-02` | `resolucao-alianca-01-2020` | `resolution_considerando` | páginas 2-2 | distância 0.429107666015625
- `resolucao-alianca-01-2020_artigo-002` | `resolucao-alianca-01-2020` | `resolution_article` | páginas 3-3 | distância 0.44365960359573364

## Validações executadas

```bash
python scripts/pipeline/build_reformed_chroma_index.py --reset
python -m py_compile scripts/pipeline/build_reformed_chroma_index.py
python -m pytest tests/test_chroma_vector_index.py
```

Problemas de validação: nenhuma ocorrência.
Erro de retrieval: nenhuma ocorrência.

## Pontos de atenção

- As consultas desta etapa avaliam apenas recuperação de chunks, sem composição de resposta.
- O modelo de consulta foi lido do manifesto de embeddings para manter compatibilidade dimensional com os embeddings indexados.

## O que não foi feito nesta etapa

- não foram gerados novos embeddings dos chunks;
- não foi implementado chatbot;
- não houve geração de respostas com LLM;
- não foi feita avaliação com documentos externos ao corpus da Aliança;
- não houve upload de documentos pelo usuário;
- não houve alteração manual de texto doutrinário;
- não houve nova extração, normalização ou chunking.
