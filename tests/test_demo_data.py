"""Tests for the demo data: the shipped demo_data.json and the generator behind it."""
from datetime import date

import make_demo_data

PERSONAL_KEYS = {"google_tokens", "access_token", "refresh_token", "email"}


def test_demo_file_has_the_expected_shape(demo):
    assert demo["demo"] is True
    assert set(demo) >= {"profile", "overview", "days"}
    assert len(demo["days"]) == make_demo_data.DAYS
    assert demo["profile"]["name"] == "Sample data"


def test_demo_days_are_in_order_and_recovery_is_a_percentage(demo):
    dates = [d["date"] for d in demo["days"]]
    assert dates == sorted(dates)
    for d in demo["days"]:
        rec = d["recovery"]
        score = rec.get("score") if isinstance(rec, dict) else rec
        assert score is None or 0 <= score <= 100


def test_demo_file_holds_no_secrets(demo):
    text = str(demo).lower()
    assert not any(k in text for k in PERSONAL_KEYS)


def test_generator_builds_the_requested_number_of_days():
    src = make_demo_data.build_src(days=5, end=date(2026, 1, 10))
    assert set(src["rhr"]) == {"2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09", "2026-01-10"}
    assert all(len(src["intraday_hr"][d]) == 1440 for d in src["intraday_hr"])  # one reading per minute
    assert all(40 <= v <= 80 for v in src["rhr"].values())


def test_generator_output_runs_through_the_real_analytics(tmp_path):
    from process_fitbit_openstrap import assemble
    src = make_demo_data.build_src(days=40, end=date(2026, 3, 1))
    out = assemble(src, make_demo_data.PROFILE, str(tmp_path / "no_labels.csv"))
    assert len(out["days"]) == 40
    assert out["overview"]["total_days_analyzed"] == 40
