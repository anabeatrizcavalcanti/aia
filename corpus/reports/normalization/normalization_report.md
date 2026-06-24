# Normalização do corpus reformado

## Status

PASS

## Resumo

Os quatro documentos extraídos foram normalizados mantendo a página como unidade de rastreabilidade. A normalização foi mecânica: espaços, quebras de linha excessivas, caracteres de controle e hifenização segura.

## Documentos

### Cânones de Dort

- Páginas normalizadas: 33
- Caracteres normalizados: 72297
- Ações: `normalized_excess_blank_lines`, `normalized_whitespace`, `recomposed_safe_hyphenation`
- Zonas preliminares: corpo confessional, material introdutório e páginas sem classificação segura
- Marcadores preservados: `Capítulo da Doutrina`, `Artigo`, `Rejeição de Erros`, `Refutação`
- Avisos: nenhum

### Catecismo de Heidelberg

- Páginas normalizadas: 29
- Caracteres normalizados: 61661
- Ações: `normalized_excess_blank_lines`, `normalized_whitespace`, `recomposed_safe_hyphenation`
- Zonas preliminares: corpo confessional e material introdutório
- Marcadores preservados: `Dia do Senhor`, `P.`, `R.`
- Avisos: nenhum

### Confissão Batista de Londres de 1689

- Páginas normalizadas: 81
- Caracteres normalizados: 282900
- Ações: `normalized_excess_blank_lines`, `normalized_whitespace`, `recomposed_safe_hyphenation`
- Zonas preliminares: corpo confessional, material introdutório, layout especial e páginas sem classificação segura
- Marcadores preservados: `CAPÍTULO`, `AS SAGRADAS ESCRITURAS`, `1.`
- Avisos: nenhum

### Confissão de Fé de Westminster

- Páginas normalizadas: 60
- Caracteres normalizados: 129667
- Ações: `normalized_excess_blank_lines`, `normalized_whitespace`, `recomposed_safe_hyphenation`
- Zonas preliminares: corpo confessional, material introdutório, sumário, layout especial e páginas sem classificação segura
- Marcadores preservados: `CAPÍTULO`, `DA ESCRITURA SAGRADA`, `I.`
- Avisos: página 1

## Arquivos gerados

Para cada documento foram criados:

- `<document_id>.normalized.json`
- `<document_id>.normalized.txt`

Diretório: `corpus/processed/normalized/reformed/`.

## Observações

A normalização não corrigiu conteúdo doutrinário, não resumiu texto e não removeu referências bíblicas. O zoneamento ainda é preliminar e serve apenas como apoio para o chunking estrutural.
