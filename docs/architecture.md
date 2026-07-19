# Arquitetura

O AIA será organizado em três fluxos principais: o pipeline documental próprio, o pipeline de recuperação e ranqueamento, e a camada de orquestração RAG. Essa separação preserva o controle metodológico sobre o corpus e evita delegar a preparação dos documentos a componentes externos de orquestração.

## Pipeline documental

O pipeline documental será responsável por preparar os documentos confessionais antes da etapa de consulta. Ele incluirá extração de texto com PyMuPDF, normalização textual própria, chunking estrutural por documento, atribuição de metadados, auditoria e persistência de artefatos processados.

LangChain não controlará esse pipeline. Extração, normalização, chunking estrutural, metadados, auditoria, política de embeddings e avaliação serão módulos próprios do projeto, pois fazem parte da contribuição metodológica do TCC.

## Pipeline de retrieval

Após o processamento, os chunks alimentarão um índice vetorial para dense retrieval e um índice lexical BM25. A arquitetura deverá combinar os resultados por busca híbrida, aplicar Reciprocal Rank Fusion, prever Cross-Encoder Reranking e usar filtros por metadados de corpus, tradição, documento e namespace de recuperação.

Esse desenho ajuda a manter separação entre o corpus reformado principal e conjuntos confessionais usados em avaliação. A arquitetura também deverá prever Parent Document Retrieval, usando chunks menores para busca e trechos maiores ou hierárquicos para envio ao modelo de linguagem.

## Geração de resposta

A geração utilizará um prompt RAG contendo a pergunta do usuário, os chunks recuperados e as fontes correspondentes. O modelo de linguagem deverá responder com base no contexto fornecido e indicar as fontes utilizadas.

Quando não houver evidência documental suficiente, o sistema deverá ser capaz de recusar ou sinalizar limitação da resposta.

## Papel do LangChain

LangChain aparecerá explicitamente na arquitetura como camada de orquestração RAG. Ele poderá integrar retriever, contexto, template de prompt e chamada ao LLM, mas não substituirá o pipeline documental próprio do AIA.

## Corpus principal e conjuntos de avaliação

O corpus principal será reformado e controlado pela desenvolvedora/pesquisadora. No início, não há risco real de mistura entre tradições porque o corpus ativo conterá apenas documentos reformados.

Outros conjuntos documentais confessionais serão adicionados durante cenários controlados de avaliação para observar fidelidade documental, rastreabilidade, separação entre corpus e risco de mistura teológica quando o sistema for exposto a documentos de tradições diferentes da tradição reformada.

Esses conjuntos não representam upload livre do usuário final. Eles fazem parte do desenho experimental do projeto.

## Upload de documentos

Upload livre de documentos pelo usuário final não é escopo inicial. Nesta fase, o controle do corpus é importante para garantir rastreabilidade, qualidade dos metadados e validade da avaliação. Essa funcionalidade poderá ser considerada como trabalho futuro.

## Papel das tecnologias

- Python: linguagem principal do projeto;
- Streamlit: interface inicial do chatbot;
- PyMuPDF: extração de texto de PDFs;
- ChromaDB: armazenamento vetorial;
- OpenAI API: provedor inicial de LLM e embeddings, quando necessário;
- rank-bm25: busca lexical BM25;
- LangChain: orquestração RAG, prompts, retriever e integração com LLM;
- RAGAS/ARES: inspiração para métricas de avaliação RAG;
- python-dotenv: carregamento de variáveis de ambiente;
- pydantic: modelos de dados e validação;
- pytest: testes automatizados;
- ruff: lint e qualidade de código.
