# Auditoria final da submissão

## Armadilhas e riscos verificados

| Risco | Evidência | Tratamento |
|---|---|---|
| `submissions/` é ignorada pelo repositório | `.gitignore` raiz contém `submissions/` | Arquivos adicionados explicitamente com `git add -f`; presença confirmada no commit |
| Join de produto silenciosamente incompleto | `GTXPro` no pipeline e `GTX Pro` no catálogo afetavam 1.480 linhas | Normalização antes do join e teste exigindo 100% de cobertura de preço |
| Data leakage | `close_date`, `close_value` e resultado só existem após o desfecho | Campos excluídos das features |
| Validação otimista | Split aleatório misturaria passado e futuro | Split cronológico; 20% fechamentos mais recentes usados como validação |
| Modelo sem capacidade de generalização | AUC fora do tempo = 0,5002 | Gate mínimo de 0,55 rejeita o modelo e aciona fallback transparente |
| Falsa precisão | Probabilidades individuais pareceriam mais confiáveis que os dados permitem | Taxas históricas suavizadas e fonte da estimativa exibida em cada linha |
| Deals antigos dominando a fila | Urgência monotônica premiaria pipeline morto | Urgência cai após 60 dias e deals com 120+ dias recebem alerta de requalificação |
| Evidência genérica de uso de IA | Um texto poderia apenas afirmar que a IA foi usada | Process log registra hipótese, erro detectado, correção, decisões humanas e testes reproduzíveis |

## Escopo de arquivos

A submissão altera somente `submissions/romario-queiroz/`, conforme a regra do desafio. Os arquivos originais do desafio não foram modificados.

## Pendências anteriores ao Pull Request

1. Criar/confirmar o fork e enviar a branch pela conta GitHub conectada.
2. Anexar ao PR uma gravação curta ou screenshot da aplicação, se desejado. O guia aceita a narrativa escrita já incluída, portanto isso é reforço e não requisito formal.
