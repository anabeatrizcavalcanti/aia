# Metodologia de Avaliação

A avaliação do SolaBot será feita a partir de um dataset de perguntas doutrinárias, respostas esperadas ou trechos documentais esperados, e critérios específicos para retrieval e geração.

## Dados de avaliação

O conjunto de avaliação deverá conter perguntas doutrinárias recorrentes, perguntas que exigem distinções confessionais e casos em que o sistema deve recusar resposta por falta de evidência documental suficiente.

## Avaliação do retrieval

A etapa de retrieval será avaliada pela capacidade de recuperar os trechos confessionais corretos, respeitar filtros de corpus ativo e preservar contexto documental suficiente para a geração.

## Avaliação da resposta gerada

As respostas serão avaliadas quanto à fidelidade ao contexto recuperado, relevância para a pergunta, clareza, indicação correta de fontes e ausência de afirmações não sustentadas pelos documentos.

## Métricas RAG e métricas próprias

RAGAS e ARES serão usados como inspiração para métricas de sistemas RAG, como fidelidade ao contexto, relevância da resposta, precisão do contexto e recuperação de trechos relevantes.

Além disso, serão definidas métricas próprias para o domínio doutrinário, incluindo fidelidade documental, acurácia das citações, taxa de mistura teológica, taxa de resposta sem evidência, taxa de recusa correta, qualidade dos chunks e separação entre corpus reformado e conjuntos confessionais de avaliação.

## Cenários de avaliação

A avaliação será realizada com o corpus reformado principal e também com conjuntos documentais de outras tradições adicionados em cenários controlados. Esses cenários fazem parte da avaliação planejada do TCC e permitirão testar o comportamento do sistema quando exposto a documentos de tradições diferentes da tradição reformada.
