"""Streamlit UI for an explainable, action-oriented CRM priority queue."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from scoring import load_data, score_open_deals, train


st.set_page_config(page_title="Lead Focus", page_icon="🎯", layout="wide")
DATA_DIR = Path(__file__).parent / "data"


@st.cache_resource
def build():
    data = load_data(DATA_DIR)
    model = train(data)
    return data, model, score_open_deals(data, model)


data, bundle, ranked = build()

st.title("🎯 Lead Focus")
st.caption("A fila de trabalho que explica onde o vendedor deve agir — e por quê.")

with st.sidebar:
    st.header("Minha carteira")
    offices = sorted(ranked["regional_office"].unique())
    selected_offices = st.multiselect("Escritório", offices, default=offices)
    available_agents = sorted(
        ranked.loc[ranked["regional_office"].isin(selected_offices), "sales_agent"].unique()
    )
    selected_agents = st.multiselect("Vendedor", available_agents, default=available_agents)
    stages = st.multiselect(
        "Etapa", ["Prospecting", "Engaging"], default=["Prospecting", "Engaging"]
    )
    minimum = st.slider("Score mínimo", 0, 100, 0)
    st.divider()
    st.caption(f"Validação temporal · AUC {bundle.validation['roc_auc']:.2f} · Brier {bundle.validation['brier']:.3f}")
    if not bundle.use_predictive_model:
        st.warning("Modelo rejeitado: a fila usa fallback histórico transparente.")

filtered = ranked[
    ranked["regional_office"].isin(selected_offices)
    & ranked["sales_agent"].isin(selected_agents)
    & ranked["deal_stage"].isin(stages)
    & ranked["priority_score"].ge(minimum)
].copy()

top = filtered.head(20)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Deals ativos", f"{len(filtered):,}".replace(",", "."))
c2.metric("Prioridade alta", int(filtered["priority_score"].ge(70).sum()))
c3.metric("Valor esperado — top 20", f"US$ {top['estimated_value'].sum():,.0f}")
c4.metric("Deals parados", int(filtered["risk"].eq("Deal parado").sum()))

queue_tab, detail_tab, method_tab = st.tabs(
    ["Fila de ação", "Explorar carteira", "Como o score funciona"]
)

with queue_tab:
    st.subheader("Comece por estes deals")
    st.caption("A ordem combina chance de ganho, valor esperado e urgência acionável.")
    display = filtered[
        [
            "priority_score",
            "opportunity_id",
            "account",
            "sales_agent",
            "deal_stage",
            "product",
            "win_probability",
            "probability_source",
            "estimated_value",
            "days_open",
            "risk",
            "next_action",
            "why",
        ]
    ].rename(
        columns={
            "priority_score": "Score",
            "opportunity_id": "Oportunidade",
            "account": "Conta",
            "sales_agent": "Vendedor",
            "deal_stage": "Etapa",
            "product": "Produto",
            "win_probability": "Prob. ganho",
            "probability_source": "Fonte da estimativa",
            "estimated_value": "Valor esperado",
            "days_open": "Dias aberto",
            "risk": "Alerta",
            "next_action": "Próxima ação",
            "why": "Por que está aqui",
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Score": st.column_config.ProgressColumn(min_value=0, max_value=100),
            "Prob. ganho": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=1),
            "Valor esperado": st.column_config.NumberColumn(format="US$ %.0f"),
        },
        height=610,
    )
    st.download_button(
        "Baixar fila em CSV",
        display.to_csv(index=False).encode("utf-8"),
        "fila_priorizada.csv",
        "text/csv",
    )

with detail_tab:
    left, right = st.columns(2)
    with left:
        fig = px.scatter(
            filtered,
            x="win_probability",
            y="estimated_value",
            size="sales_price",
            color="priority_score",
            hover_name="account",
            hover_data=["opportunity_id", "sales_agent", "deal_stage", "next_action"],
            labels={
                "win_probability": "Probabilidade de ganho",
                "estimated_value": "Valor esperado (US$)",
                "priority_score": "Score",
            },
            color_continuous_scale="RdYlGn",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        by_agent = (
            filtered.groupby("sales_agent", as_index=False)
            .agg(deals=("opportunity_id", "count"), value=("estimated_value", "sum"))
            .sort_values("value", ascending=False)
            .head(12)
        )
        fig = px.bar(
            by_agent,
            x="value",
            y="sales_agent",
            orientation="h",
            labels={"value": "Valor esperado (US$)", "sales_agent": "Vendedor"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

with method_tab:
    st.markdown(
        """
        **Score = 55% conversão + 25% valor esperado + 20% urgência.**

        - **Conversão:** uma regressão logística foi validada nos fechamentos mais recentes.
          Como atingiu apenas AUC 0,50, ela foi **rejeitada para produção**. A aplicação usa
          taxas históricas suavizadas de vendedor, produto e setor, ancoradas na média global.
        - **Valor esperado:** preço do produto × probabilidade de ganho, convertido em percentil
          dentro da carteira ativa para não deixar apenas os produtos caros dominarem a fila.
        - **Urgência:** aumenta durante a negociação, mas cai quando o deal fica velho demais;
          um deal parado deve ser requalificado, não receber prioridade infinita.
        - **Sem vazamento:** etapa final, data/valor de fechamento e o próprio resultado não entram
          como preditores. A validação usa os 20% fechamentos mais recentes, simulando produção.

        O score **apoia**, mas não substitui o vendedor. Mudanças de contexto do cliente,
        atividade recente e dados de CRM ausentes ainda exigem julgamento humano.
        """
    )
    st.json(bundle.validation)
