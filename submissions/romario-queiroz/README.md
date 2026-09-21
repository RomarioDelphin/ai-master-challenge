# Submissão — Romário Queiroz — Challenge 003

## Sobre mim

- **Nome:** Romário Queiroz Delphin Martins
- **LinkedIn:** https://www.linkedin.com/in/romariodelphin
- **Challenge escolhido:** 003 — Lead Scorer

## Executive Summary

Construí o **Lead Focus**, uma aplicação Streamlit que transforma 2.089 oportunidades ativas em uma fila de ação explicável para os 35 vendedores. O score combina estimativa histórica de conversão (55%), valor esperado (25%) e urgência (20%), sempre mostrando o motivo e a próxima ação. Uma regressão logística candidata foi validada fora do tempo, mas obteve AUC 0,50; em vez de colocar um modelo sem sinal em produção, a solução o rejeita automaticamente e usa taxas históricas suavizadas. Assim, a ferramenta entrega utilidade operacional sem vender falsa precisão.

## Solução

### Abordagem

1. Uni as quatro tabelas reais do CRM, normalizei a divergência `GTXPro`/`GTX Pro` e preservei todas as 8.800 oportunidades.
2. Separei os 6.711 negócios fechados dos 2.089 ativos.
3. Treinei uma regressão logística sem variáveis que vazam o resultado.
4. Validei nos 20% fechamentos cronologicamente mais recentes.
5. Como o modelo não generalizou, implementei um fallback histórico com suavização bayesiana simples.
6. Combinei conversão, valor e urgência em uma fila filtrável, com alertas e ações recomendadas.

### O que o vendedor recebe

- ranking por regional, vendedor, etapa e score mínimo;
- explicação legível para cada prioridade;
- recomendação de próxima ação, não apenas um número;
- alerta de deal parado, baixa conversão ou conta ausente;
- valor esperado da carteira e exportação da fila em CSV;
- visão visual da relação entre conversão e valor.

### Resultados verificáveis

| Verificação | Resultado |
|---|---:|
| Registros carregados | 8.800 |
| Negócios fechados usados na análise | 6.711 |
| Oportunidades ativas ranqueadas | 2.089 |
| Linhas na validação temporal | 1.343 |
| AUC do modelo candidato | 0,500 |
| Brier score | 0,259 |
| Testes automatizados | 3 aprovados |

O AUC baixo é um finding, não algo escondido: as variáveis disponíveis não sustentam uma previsão individual confiável fora do tempo. A aplicação informa isso na interface e mantém o componente de conversão conservador, ancorado na média global e suavizado por vendedor, produto e setor.

### Lógica do score

`score = 100 × (0,55 × conversão + 0,25 × percentil do valor esperado + 0,20 × urgência)`

- **Conversão:** média global com pequenos ajustes por taxas históricas suavizadas de agente, produto e setor. A suavização reduz conclusões extremas em grupos pequenos.
- **Valor esperado:** preço de lista do produto × estimativa de conversão. O percentil evita que apenas produtos caros dominem a carteira.
- **Urgência:** cresce até aproximadamente 60 dias de negociação e depois cai. Deals muito antigos são sinalizados para requalificação, não premiados indefinidamente.

Os pesos são uma política operacional inicial, explicitamente visível e fácil de ajustar. Em produção, seriam calibrados em conjunto com RevOps e testados por experimento controlado.

### Como rodar

Requer Python 3.11 ou superior.

```bash
cd submissions/romario-queiroz/solution
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra `http://localhost:8501`.

Para validar:

```bash
python -m pytest -q
```

### Limitações e caminho para escala

- O dataset não contém atividades recentes, número de contatos, decisores, data do próximo passo, fonte do lead, desconto ou valor informado do deal. Essas variáveis provavelmente carregariam mais sinal preditivo.
- `sales_price` é usado como proxy de valor para oportunidades abertas; em um CRM real, deve ser substituído pelo valor estimado pelo vendedor.
- As taxas históricas mostram associação, não causalidade.
- O score ainda não foi validado por experimento com vendedores. O próximo passo é um piloto de quatro semanas, medindo avanço de etapa, tempo até próxima atividade e receita ganha contra um grupo-controle.
- Para produção, incluiria autenticação, integração incremental com CRM, monitoramento de drift, auditoria de decisões e feedback do vendedor.

## Process Log — Como usei IA

O registro detalhado está em [`process-log/PROCESS.md`](process-log/PROCESS.md).

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| ChatGPT Codex | Aceleração de exploração, código, testes e revisão, seguindo critérios e decisões definidos por mim |
| scikit-learn | Modelo candidato e validação temporal |
| Streamlit + Plotly | Aplicação e visualizações interativas |

## Evidências

- [x] [Narrativa detalhada do processo](process-log/PROCESS.md)
- [x] [Registro das interações que mudaram a solução](evidence/AI_INTERACTION_LOG.md)
- [x] Commits da implementação e da auditoria final
- [x] [Testes automatizados](evidence/test-results.txt)
- [x] [Métricas de validação reproduzíveis](evidence/validation-report.json)
- [x] [Auditoria de armadilhas e riscos](evidence/AUDIT.md)
- [x] [Hashes dos dados originais](evidence/data-integrity.sha256)
- [x] [Captura da pasta de evidências publicada](evidence/screenshots/github-evidence-folder.jpg)

_Submissão preparada em 21/09/2026._
