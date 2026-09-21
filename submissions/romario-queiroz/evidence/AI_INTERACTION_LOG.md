# Evidências de interação com IA

Este registro resume as interações que realmente mudaram a solução. Não é uma transcrição inventada nem uma lista de prompts genéricos.

## Como conduzi o trabalho com IA

Usei a IA como ferramenta de execução e revisão. Eu mantive a responsabilidade pelas hipóteses, pelos critérios de qualidade, pelas decisões de produto e pelo que seria ou não colocado na entrega. A IA acelerou tarefas que eu já havia decomposto: leitura de arquivos, exploração, geração de código, testes e revisão de inconsistências.

## Interação 1 — escolha do desafio

**Minha análise:** comparei os quatro desafios, as regras de submissão e os critérios de avaliação, usando a IA para organizar rapidamente as diferenças entre eles.

**Minha decisão:** escolhi o Challenge 003 porque ele permitia demonstrar análise de dados, construção de software e utilidade prática para o time comercial na mesma entrega. A escolha final e o critério foram meus.

## Interação 2 — primeira hipótese de scoring

**Meu direcionamento:** o vendedor precisava entender não apenas qual deal priorizar, mas também por que ele estava no topo e qual seria a próxima ação.

**Como usei a IA:** pedi apoio para implementar e testar uma hipótese de regressão logística utilizando apenas variáveis disponíveis antes do fechamento.

**Validação:** usei os 20% fechamentos mais recentes como teste fora do tempo. O resultado foi AUC 0,5002 e Brier 0,2584.

**Minha decisão:** rejeitei o uso da probabilidade do modelo em produção. Não aceitei um número apenas porque o código funcionava. Determinei que a aplicação deveria usar um fallback conservador com taxas históricas suavizadas e deixar essa limitação visível na interface.

## Interação 3 — auditoria dos joins

**Meu critério de revisão:** antes de aceitar o ranking, exigi uma checagem de cobertura dos joins e dos dados ausentes.

**Problema encontrado:** 1.480 oportunidades ficaram sem preço porque o pipeline registrava `GTXPro`, enquanto o catálogo registrava `GTX Pro`.

**Minha decisão:** normalizei a chave antes do join e defini que o teste deveria exigir preço preenchido em todas as oportunidades, evitando que a falha voltasse silenciosamente.

## Interação 4 — revisão contra falsa precisão

**Problema que identifiquei:** ordenar deals somente pelo valor ou por uma probabilidade fraca criaria uma fila enganosa.

**Minha decisão:** o score final combina conversão histórica, valor esperado e urgência. Determinei que deals muito antigos deixassem de ganhar prioridade infinita e recebessem alerta de requalificação.

## Interação 5 — testes e documentação

**Minha orientação final:** usei a IA como revisora adversarial, procurando falhas e armadilhas antes da submissão.

**Resultado:** foram verificados cardinalidade, IDs duplicados, cobertura de preço, cobertura das equipes, limites do score, ordenação, explicações, próximas ações e ausência de resultados fechados na carteira ativa.

Os três testes automatizados passaram. As métricas completas estão em `validation-report.json`, e a saída dos testes está em `test-results.txt`.

## Decisões que permaneceram sob minha responsabilidade

- A decisão de não colocar um modelo sem sinal em produção.
- A definição de que a tela principal deveria ser uma fila de trabalho, não apenas um dashboard.
- A escolha de tornar limitações visíveis em vez de esconder um resultado estatístico ruim.
- A priorização de próxima ação, requalificação e qualidade do CRM.
- A revisão final do que seria defensável diante de RevOps e dos vendedores.
