import pytest

THRESHOLD = 10.0


def is_anomaly(current, baseline, threshold=THRESHOLD):
    if baseline is None or baseline <= 0:
        return False

    difference_pct = (current - baseline) / baseline * 100
    return difference_pct >= threshold


@pytest.mark.parametrize(
    "current, baseline, expected",
    [
        (110, 100, True),
        (111, 100, True),
        (109, 100, False),
        (100, 100, False),
        (90, 100, False),
        (100, None, False),
        (100, 0, False),
        (100, -10, False),
    ],
)
def test_anomaly_rule(current, baseline, expected):
    assert is_anomaly(current, baseline) is expected


def test_either_baseline_can_trigger_flag():
    history_flag = is_anomaly(115, 100)
    peer_flag = is_anomaly(105, 100)

    assert history_flag or peer_flag


def test_neither_baseline_triggers_flag():
    history_flag = is_anomaly(105, 100)
    peer_flag = is_anomaly(108, 100)

    assert not (history_flag or peer_flag)