# Avaliação do RAG com RAGAS

Este projeto usa uma avaliação em duas etapas:

1. executar perguntas controladas no chatbot RAG e salvar respostas, contextos e fontes;
2. executar RAGAS sobre o dataset gerado, sem chamar novamente o chatbot.

## CSV de perguntas

O arquivo recomendado é:

```text
data/evaluation/perguntas_avaliacao.csv
```

O CSV deve conter uma linha de cabeçalho e as colunas:

```text
id
categoria
pergunta
documentos_esperados
escopo_esperado
mistura_permitida
referencia_esperada
resposta_esperada_ground_truth
deve_responder
observacao
```

O separador preferencial é `;`. O script também aceita `,` quando o arquivo tiver sido exportado assim.

## Gerar Dataset

Para executar localmente o pipeline RAG do projeto:

```bash
python scripts/evaluation/run_rag_evaluation_questions.py \
  --input data/evaluation/perguntas_avaliacao.csv \
  --output-jsonl reports/evaluation/rag_eval_run.jsonl \
  --output-csv reports/evaluation/rag_eval_run.csv
```

Para avaliar um endpoint HTTP já em execução:

```bash
python scripts/evaluation/run_rag_evaluation_questions.py \
  --input data/evaluation/perguntas_avaliacao.csv \
  --endpoint http://localhost:8000/api/chat \
  --output-jsonl reports/evaluation/rag_eval_run.jsonl \
  --output-csv reports/evaluation/rag_eval_run.csv
```

Essa etapa salva:

```text
reports/evaluation/rag_eval_run.jsonl
reports/evaluation/rag_eval_run.csv
```

O JSONL preserva a resposta exata do chatbot, os textos dos contextos recuperados, as fontes recuperadas e os campos de escopo documental.

## Executar RAGAS

Antes de rodar a avaliação automática, instale as dependências de avaliação:

```bash
pip install -r requirements-eval.txt
```

Esse arquivo fixa uma combinação compatível com `ragas==0.4.3`, que aceita `show_progress` e `batch_size`. O pin de `langchain-community==0.2.19` evita a combinação quebrada com `langchain-community` 0.4.x, que removeu um módulo legado de VertexAI ainda importado pelo RAGAS.

Depois que o JSONL já existir, execute:

```bash
python scripts/evaluation/run_ragas_evaluation.py \
  --input-jsonl reports/evaluation/rag_eval_run.jsonl \
  --output-csv reports/evaluation/ragas_results.csv \
  --output-json reports/evaluation/ragas_results.json \
  --summary-json reports/evaluation/ragas_summary.json
```

Essa etapa não chama o chatbot. Ela avalia apenas o dataset salvo.

## Arquivos Gerados

`rag_eval_run.jsonl`: dataset completo, uma linha JSON por pergunta.

`rag_eval_run.csv`: versão resumida para conferência manual.

`ragas_results.csv`: resultados por pergunta com métricas RAGAS e razões de linhas ignoradas.

`ragas_results.json`: resultados completos por pergunta, incluindo metadados preservados.

`ragas_summary.json`: totais, médias gerais e médias por categoria.

## Campos Necessários Para RAGAS

O dataset precisa conter:

```text
question
answer
contexts
ground_truth
```

O script usa este mapeamento:

```text
question = pergunta original
answer = resposta exata do chatbot
contexts = lista de textos dos chunks recuperados
ground_truth = resposta esperada da planilha
```

Em versões do RAGAS que usam nomes novos, esses campos correspondem a:

```text
question -> user_input
answer -> response
contexts -> retrieved_contexts
ground_truth -> reference
```

## Configuração do Avaliador

Não coloque chave de API no código. Use variáveis de ambiente:

```text
OPENAI_API_KEY
RAGAS_LLM_MODEL
RAGAS_EMBEDDING_MODEL
```

Se `RAGAS_LLM_MODEL` ou `RAGAS_EMBEDDING_MODEL` não forem definidos, o script tenta reaproveitar:

```text
OPENAI_CHAT_MODEL
OPENAI_EMBEDDING_MODEL
```

## Métricas

`faithfulness`: mede se a resposta é sustentada pelos contextos recuperados.

`answer_relevancy`: mede se a resposta atende à pergunta.

`context_precision`: mede se os contextos recuperados são relevantes para a resposta/pergunta.

`context_recall`: mede se os contextos recuperados cobrem o que era esperado no ground truth.

As métricas automáticas são auxiliares. A etapa manual continua necessária para avaliar fidelidade documental, qualidade das citações, uso do documento esperado, resposta ou recusa adequada e possível mistura indevida entre documentos batistas, congregacionais e reformados.
