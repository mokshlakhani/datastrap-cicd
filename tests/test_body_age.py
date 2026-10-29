"""Tests for body_age.py: the body (physiological) age estimate."""
import copy

import body_age


def test_bounded_never_goes_below_the_floor():
    assert body_age.bounded(20, -50) == body_age.FLOOR


def test_bounded_caps_the_difference():
    assert body_age.bounded(30, 50) == 40.0   # 30 and over: at most +10 years
    assert body_age.bounded(30, -50) == 20.0  # ... and at most -10 years
    assert body_age.bounded(20, 50) == 28.0   # under 30: at most +8 years


def test_no_drivers_means_no_change():
    delta, sigma, per_driver = body_age.evaluate({}, 30, "male")
    assert delta == 0 and per_driver == {} and sigma > 0


def test_fitter_vo2_makes_you_younger_and_unfit_older():
    fit_years, _ = body_age.driver_years("vo2", 60, 30, "male")
    unfit_years, _ = body_age.driver_years("vo2", 25, 30, "male")
    assert fit_years < 0 < unfit_years


def test_peer_values_fall_with_age():
    assert body_age.peer_vo2(60, "male") < body_age.peer_vo2(30, "male")
    assert body_age.peer_rhr(30, "male") > 0


def test_apply_sets_bio_age_for_every_demo_day(demo):
    records = copy.deepcopy(demo["days"])
    for r in records:
        r.pop("bio_age", None)
    body_age.apply(records, demo["profile"])
    assert all("bio_age" in r for r in records)
    assert any(r["bio_age"] and r["bio_age"].get("status") == "ok" for r in records)
