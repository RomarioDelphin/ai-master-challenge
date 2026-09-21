from pathlib import Path

from scoring import load_data, score_open_deals, train


DATA = Path(__file__).parents[1] / "data"


def test_loads_and_joins_every_pipeline_row():
    frame = load_data(DATA)
    assert len(frame) == 8_800
    assert {"sector", "sales_price", "manager", "regional_office"}.issubset(frame.columns)
    assert frame["opportunity_id"].is_unique
    assert frame["sales_price"].notna().all()
    assert frame["manager"].notna().all()


def test_model_validation_and_scores_are_sane():
    frame = load_data(DATA)
    bundle = train(frame)
    scored = score_open_deals(frame, bundle)

    assert bundle.validation["validation_rows"] > 1_000
    assert 0.5 <= bundle.validation["roc_auc"] <= 1
    assert len(scored) == 2_089
    assert scored["priority_score"].between(0, 100).all()
    assert scored["win_probability"].between(0, 1).all()
    assert scored["why"].str.len().gt(20).all()
    assert scored["next_action"].notna().all()


def test_ranking_is_descending_and_export_has_no_outcomes():
    frame = load_data(DATA)
    scored = score_open_deals(frame, train(frame))
    assert scored["priority_score"].is_monotonic_decreasing
    assert set(scored["deal_stage"]) == {"Prospecting", "Engaging"}
    assert scored["close_date"].isna().all()
