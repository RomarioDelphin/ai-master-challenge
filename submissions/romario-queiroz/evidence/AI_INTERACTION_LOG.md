# Evidências de interação com IA

Este registro resume as interações que realmente mudaram a solução. Não é uma transcrição inventada nem uma lista de prompts genéricos.

## Interação 1 — escolha do desafio

**Meu pedido:** analisar o repositório, escolher um dos cases e entregar uma solução funcional.

**Uso da IA:** leitura comparativa dos quatro desafios, das regras de submissão e dos critérios de avaliação.

**Minha decisão:** escolhi o Challenge 003 porque ele permitia demonstrar análise de dados, construção de software e utilidade prática para o time comercial na mesma entrega.

## Interação 2 — primeira hipótese de scoring

**Meu direcionamento:** o vendedor precisava entender não apenas qual deal priorizar, mas também por que ele estava no topo e qual seria a próxima ação.

**Sugestão inicial da IA:** regressão logística utilizando vendedor, produto, conta, setor, porte, localização, regional e mês de entrada.

**Validação:** usei os 20% fechamentos mais recentes como teste fora do tempo. O resultado foi AUC 0,5002 e Brier 0,2584.

**Correção:** rejeitei o uso da probabilidade do modelo em produção. A aplicação passou a usar um fallback conservador com taxas históricas suavizadas, deixando essa limitação visível na interface.

## Interação 3 — auditoria dos joins

**Pergunta feita à análise:** existem registros sem correspondência depois da união das tabelas?

**Problema encontrado:** 1.480 oportunidades ficaram sem preço porque o pipeline registrava `GTXPro`, enquanto o catálogo registrava `GTX Pro`.

**Correção:** normalizei a chave antes do join e acrescentei um teste que exige preço preenchido em todas as oportunidades.

## Interação 4 — revisão contra falsa precisão

**Problema discutido:** ordenar deals somente pelo valor ou por uma probabilidade fraca criaria uma fila enganosa.

**Decisão aplicada:** o score final combina conversão histórica, valor esperado e urgência. Deals muito antigos deixam de ganhar prioridade infinita e passam a receber alerta de requalificação.

## Interação 5 — testes e documentação

**Pedido final:** revisar a solução como se fosse um avaliador procurando falhas e armadilhas.

**Resultado:** foram verificados cardinalidade, IDs duplicados, cobertura de preço, cobertura das equipes, limites do score, ordenação, explicações, próximas ações e ausência de resultados fechados na carteira ativa.

Os três testes automatizados passaram. As métricas completas estão em `validation-report.json`, e a saída dos testes está em `test-results.txt`.

## O que não deleguei à IA

- A decisão de não colocar um modelo sem sinal em produção.
- A definição de que a tela principal deveria ser uma fila de trabalho, não apenas um dashboard.
- A escolha de tornar limitações visíveis em vez de esconder um resultado estatístico ruim.
- A priorização de próxima ação, requalificação e qualidade do CRM.
- A revisão final do que seria defensável diante de RevOps e dos vendedores.
