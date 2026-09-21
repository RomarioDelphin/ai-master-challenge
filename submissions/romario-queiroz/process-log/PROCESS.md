# Process log — Challenge 003

## 1. Decomposição antes de construir

Transformei o pedido “diga onde focar” em quatro decisões que a ferramenta precisava apoiar:

1. qual oportunidade atender primeiro;
2. quanto valor pode existir nela;
3. por que ela está acima das demais;
4. qual ação concreta executar agora.

Também defini dois limites: não usar informações conhecidas apenas depois do fechamento e não apresentar uma probabilidade como confiável sem validação fora do tempo.

## 2. Uso da IA no workflow

### Iteração 1 — descoberta e desenho

Usei o Codex para acelerar a leitura comparativa dos quatro challenges, das regras de submissão e do template. Escolhi o Challenge 003 porque ele permitia demonstrar análise, julgamento e software utilizável na mesma entrega. Mantive o foco no usuário desde o início: a tela principal deveria ser uma fila de ação, não um dashboard de vaidade.

### Iteração 2 — dados e hipótese de modelo

Usei a IA para acelerar o download, a leitura do esquema e as verificações de cardinalidade, ausências e estágios. Defini como primeira hipótese uma regressão logística explicável com atributos disponíveis antes do desfecho. Excluí deliberadamente `close_value`, `close_date` e o resultado do negócio para evitar data leakage.

Na auditoria final, uma checagem de cobertura dos joins revelou que o pipeline escrevia `GTXPro`, enquanto o catálogo escrevia `GTX Pro`. Isso retirava silenciosamente o preço de 1.480 linhas. Normalizei a chave antes do join e acrescentei um teste que exige preço e equipe completos em todas as oportunidades.

### Iteração 3 — validação que mudou a solução

O modelo candidato foi validado nos 20% fechamentos mais recentes, e não em uma divisão aleatória. O resultado foi AUC 0,500 e Brier 0,259. A primeira interface ainda tratava a saída como probabilidade preditiva; a revisão mostrou que isso seria tecnicamente indefensável.

Corrigi a arquitetura: se AUC < 0,55, o modelo é rejeitado automaticamente. A estimativa usada passa a ser uma composição conservadora da taxa global e de taxas históricas suavizadas por vendedor, produto e setor. A interface exibe um aviso em vez de esconder a falha.

### Iteração 4 — utilidade operacional

O ranking foi além de “chance de fechar”:

- valor esperado em percentil, para equilibrar potencial e comparabilidade;
- urgência não monotônica, evitando colocar eternamente deals velhos no topo;
- alertas de estagnação e qualidade do dado;
- próxima ação baseada na etapa e no tempo aberto;
- filtros por regional e vendedor;
- exportação para CSV.

### Iteração 5 — verificação

Criei testes para garantir:

- join sem perda dos 8.800 registros;
- ausência de IDs duplicados e cobertura integral de preço/equipe após os joins;
- exatamente 2.089 oportunidades abertas ranqueadas;
- scores e estimativas em intervalos válidos;
- explicação e próxima ação em todas as linhas;
- ordenação decrescente e ausência de desfechos nas oportunidades ativas.

Todos os três testes passaram.

## 3. Onde a IA errou e como corrigi

O erro mais importante da primeira implementação apoiada pela IA foi conceitual: ela transformava automaticamente `predict_proba` em “probabilidade de ganho”, mesmo com AUC praticamente aleatório. Eu não aceitei essa saída. Código correto não significa decisão correta. Determinei a criação de um gate de qualidade, mantive as métricas visíveis e substituí a previsão por um fallback conservador.

Também evitei três sugestões comuns, mas inadequadas:

- usar `close_value` no treinamento, pois vazaria o resultado;
- validar aleatoriamente, pois superestimaria a estabilidade temporal;
- colocar deals mais antigos sempre no topo, pois isso recompensa pipeline morto.

## 4. Julgamento humano adicionado

- A ferramenta prioriza **ações**, não apenas probabilidades.
- Um modelo fraco é explicitamente rejeitado.
- Os pesos do score são tratados como política operacional testável, não como verdade estatística.
- A limitação do dataset é traduzida em requisitos concretos de CRM para a próxima versão.
- O sucesso futuro é definido por experimento: avanço de etapa, tempo até próxima atividade e receita incremental, em vez de somente AUC.

## 5. Reprodutibilidade

Os dados CC0 usados estão em `solution/data/`. O treino ocorre ao iniciar a aplicação, com `random_state=42`. As instruções e dependências fixadas estão no README e em `solution/requirements.txt`.
