
import pandas as pd


THRESHOLD = 10.0


def is_anomaly(history_pct, peer_pct):
    history_flag = (
        pd.notna(history_pct) and history_pct >= THRESHOLD
    )
    peer_flag = (
        pd.notna(peer_pct) and peer_pct >= THRESHOLD
    )
    return history_flag or peer_flag


def test_small_increase_is_not_flagged():
    assert is_anomaly(4.0, 3.0) is False


def test_large_historical_increase_is_flagged():
    assert is_anomaly(12.0, 2.0) is True


def test_large_peer_difference_is_flagged():
    assert is_anomaly(2.0, 15.0) is True


def test_either_baseline_can_trigger_flag():
    assert is_anomaly(11.0, 12.0) is True


def test_missing_baselines_do_not_trigger_flag():
    assert is_anomaly(float("nan"), float("nan")) is False
