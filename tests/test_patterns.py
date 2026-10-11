"""Each pattern rule is tested on hand-made candles where the answer is known."""
import pandas as pd
import pytest

from data import clean
from patterns import detect

PAD = [(100, 100.6, 99.6, 100.3)] * 3          # neutral candles so shifts have history
DECLINE = [(106 - i, 106.2 - i, 104.8 - i, 105 - i) for i in range(6)]   # falling closes for hammer context


def frame(candles):
    rows = [{"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i), "Open": o, "High": h, "Low": l, "Close": c}
            for i, (o, h, l, c) in enumerate(candles)]
    return detect(pd.DataFrame(rows))


CASES = {
    "doji":                 PAD + [(100, 101, 99, 100.05)],
    "hammer":               DECLINE + [(100, 100.6, 98.5, 100.5)],
    "bullish_marubozu":     PAD + [(100, 102, 100, 102)],
    "bearish_marubozu":     PAD + [(102, 102, 100, 100)],
    "bullish_engulfing":    PAD + [(101, 101.1, 99.9, 100), (99.8, 101.6, 99.7, 101.5)],
    "bearish_engulfing":    PAD + [(100, 101.1, 99.9, 101), (101.2, 101.3, 99.4, 99.5)],
    "bullish_harami":       PAD + [(103, 103.2, 99.8, 100), (100.5, 102.1, 100.4, 102)],
    "bearish_harami":       PAD + [(100, 103.2, 99.8, 103), (102.5, 102.6, 100.9, 101)],
    "morning_star":         PAD + [(105, 105.2, 99.8, 100), (99.8, 100.0, 99.6, 99.9), (100, 103.1, 99.9, 103)],
    "evening_star":         PAD + [(100, 105.2, 99.8, 105), (105.2, 105.4, 105.0, 105.1), (105, 105.1, 100.9, 101)],
    "three_white_soldiers": PAD + [(100, 102.2, 99.9, 102), (101, 103.6, 100.9, 103.5), (102.5, 105.2, 102.4, 105)],
    "three_black_crows":    PAD + [(105, 105.1, 102.8, 103), (104, 104.1, 101.4, 101.5), (102.5, 102.6, 99.8, 100)],
}


@pytest.mark.parametrize("name", CASES)
def test_pattern_detected_on_last_candle(name):
    d = frame(CASES[name])
    assert d[name].iloc[-1], f"{name} not detected"


def test_opposite_patterns_not_detected():
    d = frame(CASES["bullish_engulfing"])
    assert not d["bearish_engulfing"].iloc[-1]
    d = frame(CASES["three_white_soldiers"])
    assert not d["three_black_crows"].iloc[-1]


def test_hammer_needs_prior_decline():
    rising = [(95 + i, 95.2 + i, 94.8 + i, 95.1 + i) for i in range(6)]
    d = frame(rising + [(100, 100.6, 98.5, 100.5)])
    assert not d["hammer"].iloc[-1]


def test_every_candle_gets_a_type():
    d = frame(CASES["morning_star"])
    assert set(d["candle_type"]) <= {"bullish", "bearish", "doji", "flat"}
    assert d["candle_type"].notna().all()


def test_clean_drops_impossible_candles():
    raw = pd.DataFrame({"Date": ["2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04"],
                        "Open": [100, 100, 100, 100], "High": [101, 99, 101, 101],
                        "Low": [99, 100, 99, 99], "Close": [100.5, 100, 100.5, 102]})
    df, dropped = clean(raw)
    assert dropped == 2          # high below low; close above high
    assert df["Date"].is_unique
