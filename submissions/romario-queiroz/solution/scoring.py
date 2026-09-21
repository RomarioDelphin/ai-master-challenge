"""Training and explainable prioritisation logic for the Lead Focus app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CATEGORICAL_FEATURES = [
    "sales_agent",
    "product",
    "account",
    "sector",
    "office_location",
    "manager",
    "regional_office",
    "engage_month",
]
NUMERIC_FEATURES = ["revenue", "employees", "year_established", "sales_price"]


@dataclass
class ModelBundle:
    model: Pipeline
    validation: dict[str, float | str]
    reference_date: pd.Timestamp
    benchmarks: dict[str, pd.Series]
    use_predictive_model: bool


def load_data(data_dir: str | Path) -> pd.DataFrame:
    """Load and join the four CRM tables without mutating the source files."""
    data_dir = Path(data_dir)
    pipeline = pd.read_csv(data_dir / "sales_pipeline.csv")
    accounts = pd.read_csv(data_dir / "accounts.csv")
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")

    # The source dataset spells the same SKU as "GTXPro" in the pipeline and
    # "GTX Pro" in the catalogue. Normalise before joining; otherwise 1,480
    # opportunities silently lose their list price and expected value.
    pipeline["product"] = pipeline["product"].replace({"GTXPro": "GTX Pro"})

    frame = (
        pipeline.merge(accounts, on="account", how="left", validate="many_to_one")
        .merge(products, on="product", how="left", validate="many_to_one")
        .merge(teams, on="sales_agent", how="left", validate="many_to_one")
    )
    for col in ["engage_date", "close_date"]:
        frame[col] = pd.to_datetime(frame[col], errors="coerce")
    frame["engage_month"] = frame["engage_date"].dt.month.astype("Int64").astype(str)
    frame["engage_month"] = frame["engage_month"].replace("<NA>", "Unknown")
    frame[CATEGORICAL_FEATURES] = frame[CATEGORICAL_FEATURES].fillna("Unknown")
    return frame


def _pipeline() -> Pipeline:
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    preprocess = ColumnTransformer(
        [("cat", categorical, CATEGORICAL_FEATURES), ("num", numeric, NUMERIC_FEATURES)]
    )
    return Pipeline(
        [
            ("preprocess", preprocess),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000, class_weight="balanced", C=0.7, random_state=42
                ),
            ),
        ]
    )


def _smoothed_rates(closed: pd.DataFrame, column: str, strength: int = 20) -> pd.Series:
    global_rate = closed["won"].mean()
    grouped = closed.groupby(column, dropna=False)["won"].agg(["sum", "count"])
    return (grouped["sum"] + strength * global_rate) / (grouped["count"] + strength)


def train(frame: pd.DataFrame) -> ModelBundle:
    """Validate out-of-time, then refit on every closed opportunity."""
    closed = frame[frame["deal_stage"].isin(["Won", "Lost"])].copy()
    closed["won"] = (closed["deal_stage"] == "Won").astype(int)
    closed = closed.sort_values("close_date", na_position="first")

    split = max(int(len(closed) * 0.8), 1)
    train_set, valid_set = closed.iloc[:split], closed.iloc[split:]
    validation_model = _pipeline().fit(
        train_set[CATEGORICAL_FEATURES + NUMERIC_FEATURES], train_set["won"]
    )
    probability = validation_model.predict_proba(
        valid_set[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    )[:, 1]
    validation = {
        "roc_auc": float(roc_auc_score(valid_set["won"], probability)),
        "brier": float(brier_score_loss(valid_set["won"], probability)),
        "validation_rows": float(len(valid_set)),
        "base_win_rate": float(valid_set["won"].mean()),
    }

    final_model = _pipeline().fit(
        closed[CATEGORICAL_FEATURES + NUMERIC_FEATURES], closed["won"]
    )
    latest = pd.concat([frame["engage_date"], frame["close_date"]]).max()
    benchmarks = {
        "agent": _smoothed_rates(closed, "sales_agent"),
        "product": _smoothed_rates(closed, "product"),
        "sector": _smoothed_rates(closed, "sector"),
    }
    # A weak model is more dangerous than an honest heuristic. Below 0.55 AUC,
    # production scoring falls back to smoothed historical rates while retaining
    # the validation result as an explicit diagnostic.
    use_predictive_model = validation["roc_auc"] >= 0.55
    validation["production_mode"] = "predictive" if use_predictive_model else "historical_fallback"
    return ModelBundle(
        final_model,
        validation,
        latest + pd.Timedelta(days=1),
        benchmarks,
        use_predictive_model,
    )


def _percentile(values: pd.Series) -> pd.Series:
    if len(values) <= 1:
        return pd.Series(0.5, index=values.index)
    return values.rank(pct=True, method="average")


def _reason(row: pd.Series, bundle: ModelBundle, global_win_rate: float) -> str:
    reasons: list[str] = []
    product_rate = bundle.benchmarks["product"].get(row["product"], global_win_rate)
    agent_rate = bundle.benchmarks["agent"].get(row["sales_agent"], global_win_rate)
    sector_rate = bundle.benchmarks["sector"].get(row["sector"], global_win_rate)

    comparisons = [
        (product_rate - global_win_rate, f"produto com histórico de {product_rate:.0%} de ganho"),
        (agent_rate - global_win_rate, f"agente com histórico de {agent_rate:.0%} de ganho"),
        (sector_rate - global_win_rate, f"setor com histórico de {sector_rate:.0%} de ganho"),
    ]
    strongest = sorted(comparisons, key=lambda item: abs(item[0]), reverse=True)[:2]
    reasons.extend(text for _, text in strongest)
    if row["deal_stage"] == "Engaging":
        reasons.append(f"{int(row['days_open'])} dias em negociação")
    else:
        reasons.append("ainda precisa ser qualificado")
    return "; ".join(reasons).capitalize() + "."


def _next_action(row: pd.Series) -> str:
    if row["deal_stage"] == "Prospecting":
        return "Qualificar conta e confirmar decisor, dor e prazo"
    if row["days_open"] >= 75:
        return "Revalidar urgência e agendar próximo passo em 24h"
    if row["win_probability"] >= 0.65:
        return "Avançar proposta e confirmar critérios de decisão"
    return "Descobrir objeção principal e combinar próximo contato"


def score_open_deals(frame: pd.DataFrame, bundle: ModelBundle) -> pd.DataFrame:
    """Score only active deals using probability, value and time-sensitive urgency."""
    open_deals = frame[frame["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
    features = open_deals[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    if bundle.use_predictive_model:
        open_deals["win_probability"] = bundle.model.predict_proba(features)[:, 1]
        open_deals["probability_source"] = "Modelo validado fora do tempo"
    else:
        closed = frame[frame["deal_stage"].isin(["Won", "Lost"])]
        global_rate = float(closed["deal_stage"].eq("Won").mean())
        agent_rate = open_deals["sales_agent"].map(bundle.benchmarks["agent"]).fillna(global_rate)
        product_rate = open_deals["product"].map(bundle.benchmarks["product"]).fillna(global_rate)
        sector_rate = open_deals["sector"].map(bundle.benchmarks["sector"]).fillna(global_rate)
        # Shrink segment history toward the global rate to avoid false precision.
        open_deals["win_probability"] = (
            0.50 * global_rate + 0.20 * agent_rate + 0.20 * product_rate + 0.10 * sector_rate
        ).clip(0.05, 0.95)
        open_deals["probability_source"] = "Fallback histórico suavizado (modelo rejeitado)"
    open_deals["estimated_value"] = (
        open_deals["win_probability"] * open_deals["sales_price"].fillna(0)
    )
    open_deals["days_open"] = (
        bundle.reference_date - open_deals["engage_date"]
    ).dt.days.fillna(0).clip(lower=0)

    # Urgency peaks around 60 days, then declines after 120: stale deals should be
    # requalified rather than blindly ranked first forever.
    age = open_deals["days_open"].astype(float)
    urgency = np.where(
        open_deals["deal_stage"].eq("Prospecting"),
        0.35,
        np.where(age <= 60, 0.4 + age / 100, np.maximum(0.25, 1 - (age - 60) / 120)),
    )
    open_deals["urgency"] = np.clip(urgency, 0, 1)
    open_deals["priority_score"] = (
        100
        * (
            0.55 * open_deals["win_probability"]
            + 0.25 * _percentile(open_deals["estimated_value"])
            + 0.20 * open_deals["urgency"]
        )
    ).round().astype(int)

    global_win_rate = float(
        frame["deal_stage"].eq("Won").sum()
        / frame["deal_stage"].isin(["Won", "Lost"]).sum()
    )
    open_deals["why"] = open_deals.apply(
        _reason, axis=1, bundle=bundle, global_win_rate=global_win_rate
    )
    open_deals["next_action"] = open_deals.apply(_next_action, axis=1)
    open_deals["risk"] = np.select(
        [
            open_deals["days_open"].ge(120),
            open_deals["win_probability"].lt(0.4),
            open_deals["account"].eq("Unknown"),
        ],
        ["Deal parado", "Baixa conversão", "Conta não identificada"],
        default="Sem alerta crítico",
    )
    return open_deals.sort_values(
        ["priority_score", "estimated_value"], ascending=False
    ).reset_index(drop=True)
