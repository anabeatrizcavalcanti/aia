# Fundamentação Teórica

## Retrieval-Augmented Generation

Retrieval-Augmented Generation será a arquitetura principal do AIA. O modelo de linguagem deverá responder a partir de trechos recuperados do corpus documental ativo, e não apenas com base em seu conhecimento paramétrico.

## Chunking Estrutural em Documentos Confessionais

O chunking deverá respeitar a estrutura interna dos documentos confessionais. Confissões organizadas por capítulos e seções, catecismos organizados por perguntas e respostas, e documentos com artigos e rejeições de erro exigem divisões que preservem contexto doutrinário.

## Dense Retrieval e Embeddings

Dense retrieval permitirá recuperar trechos semanticamente próximos da pergunta do usuário. Cada chunk será representado por embeddings, e a pergunta também será vetorizada para busca por similaridade.

## BM25 e Busca Lexical

BM25 será usado como estratégia lexical para preservar termos técnicos importantes em teologia, como eleição, justificação, regeneração, aliança, batismo e perseverança dos santos. Essa busca é relevante quando a precisão terminológica importa.

## Busca Híbrida e Reciprocal Rank Fusion

A busca híbrida combinará resultados de dense retrieval e BM25. Reciprocal Rank Fusion será usada como estratégia preferencial para fundir rankings e equilibrar similaridade semântica com precisão lexical.

## Cross-Encoder Reranking

Cross-Encoder Reranking deverá reordenar os candidatos recuperados avaliando conjuntamente o par pergunta + chunk. Essa etapa será prevista para aumentar a precisão do contexto enviado ao modelo de linguagem.

## Metadata Filtering e Controle de Escopo Confessional

Cada chunk deverá conter metadados como `corpus_id`, `tradition`, `document_id`, `section_title`, `page_start`, `page_end`, `source_path` e `retrieval_namespace`. Esses metadados permitirão filtrar o corpus ativo e controlar o escopo confessional da resposta.

## Parent Document Retrieval e Recuperação Hierárquica

Parent Document Retrieval será previsto para recuperar chunks pequenos durante a busca e enviar ao LLM trechos maiores ou hierárquicos. Isso é importante porque um artigo, seção ou resposta de catecismo pode depender de seu contexto documental.

## Recusa Baseada em Evidência

O AIA deverá recusar ou limitar respostas quando os trechos recuperados não forem suficientes para sustentar uma conclusão. A resposta deverá informar a ausência de base documental suficiente no corpus ativo.

## Avaliação de Sistemas RAG

A avaliação deverá considerar métricas inspiradas em RAGAS e ARES, incluindo fidelidade ao contexto, relevância da resposta, precisão do contexto e recuperação correta dos trechos relevantes.

## Métricas Específicas para Consulta Doutrinária

Além das métricas gerais de RAG, o projeto deverá prever métricas próprias, como fidelidade documental, acurácia das citações, taxa de mistura teológica, taxa de resposta sem evidência, taxa de recusa correta, qualidade dos chunks e separação entre corpus reformado e conjuntos confessionais de avaliação.
