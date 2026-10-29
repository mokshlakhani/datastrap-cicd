"""Tests for sleep_score.py: the sleep score estimate."""
import copy

import sleep_score


def good_night(**over):
    night = {
        "stage_source": "api", "duration_minutes": 420, "rem_min": 90, "deep_min": 80, "wake_min": 20,
        "hypnogram": [{"time": "2026-01-01T00:00:00.000", "stage": "light", "seconds": 600}],
    }
    night.update(over)
    return night


def test_night_features_for_a_normal_night():
    f = sleep_score.night_features(good_night())
    assert f == {"asleep": 420.0, "rem": 90.0, "deep": 80.0, "awake": 20.0}


def test_night_features_skips_nights_it_cannot_score():
    assert sleep_score.night_features(None) is None
    assert sleep_score.night_features(good_night(stage_source="takeout-legacy")) is None  # old staging
    assert sleep_score.night_features(good_night(duration_minutes=60)) is None  # too short
    assert sleep_score.night_features(good_night(hypnogram=[{"stage": "asleep"}])) is None  # unstaged
    assert sleep_score.night_features(good_night(rem_min=None)) is None  # missing data


def test_to_score_stays_between_0_and_100():
    assert sleep_score.to_score(-12.4) == 0
    assert sleep_score.to_score(140) == 100
    assert sleep_score.to_score(76.6) == 77


def test_more_deep_sleep_never_lowers_the_score():
    model = sleep_score.DEFAULT_MODEL
    base = sleep_score.night_features(good_night(deep_min=60))
    better = sleep_score.night_features(good_night(deep_min=100))
    assert sleep_score.predict(model, better) >= sleep_score.predict(model, base)


def test_more_awake_time_never_raises_the_score():
    model = sleep_score.DEFAULT_MODEL
    calm = sleep_score.night_features(good_night(wake_min=5))
    restless = sleep_score.night_features(good_night(wake_min=60))
    assert sleep_score.predict(model, restless) <= sleep_score.predict(model, calm)


def test_load_labels_reads_csv_and_ignores_notes(tmp_path):
    f = tmp_path / "labels.csv"
    f.write_text("# a note\ndate,score\n2026-01-01,81\nbad,row\n2026-01-02,not-a-number\n")
    assert sleep_score.load_labels(str(f)) == {"2026-01-01": 81.0}


def test_load_labels_missing_file_is_empty(tmp_path):
    assert sleep_score.load_labels(str(tmp_path / "nope.csv")) == {}


def test_fit_recovers_a_known_relationship():
    # Scores made from a known formula should be reproduced closely by fit().
    nights = [sleep_score.night_features(good_night(duration_minutes=m, deep_min=d, rem_min=r, wake_min=w))
              for m, d, r, w in [(300, 50, 60, 40), (360, 60, 70, 30), (420, 70, 90, 20), (450, 90, 100, 10),
                                 (400, 80, 80, 25), (380, 65, 75, 35)]]
    scores = [60 + 0.05 * f["asleep"] for f in nights]
    model = sleep_score.fit(nights, scores)
    assert len(model["coef"]) == 5
    assert model["coef"][1] >= 0 and model["coef"][4] <= 0  # constraints respected


def test_apply_fills_every_demo_night(demo, tmp_path):
    records = copy.deepcopy(demo["days"])
    summary = sleep_score.apply(records, str(tmp_path / "no_labels.csv"))
    assert summary["method"] == "default"  # fewer than 15 app scores -> default weights
    scored = [r["sleep"]["score"] for r in records if r["sleep"]["score"] is not None]
    assert scored, "expected at least one scored night in the demo data"
    assert all(0 <= s <= 100 for s in scored)
