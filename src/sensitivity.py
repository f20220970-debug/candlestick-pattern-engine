"""Sensitivity check: does the conclusion survive different thresholds?

Reruns detection and the forward-return tests under several threshold settings
(using the price files already saved in data/raw by run.py) and reports, for each:
  * tests with enough signals, and how many pass |t| >= 2 in the predicted direction
  * how many survive Bonferroni and Benjamini-Hochberg (5% level) corrections
  * pooled 5-day edge for the bullish and bearish pattern groups
Also tries a "relative long body" rule: the first candle of harami/star patterns must
have a body larger than the average body of the previous 10 days, instead of a fixed
share of its own range.
Writes outputs/sensitivity.csv and appends nothing to the main report.
"""
import math
from contextlib import contextmanager

import pandas as pd

import config as C
import patterns as P
from data import load
from patterns import DIRECTION, PATTERNS
from research import forward_returns, pattern_stats

SETTINGS = {
    "strict":  {"DOJI_BODY_MAX": 0.05, "MARUBOZU_SHADOW_MAX": 0.02, "HAMMER_LOWER_MIN": 2.5,
                "HAMMER_UPPER_MAX": 0.15, "STAR_SMALL_BODY": 0.20, "SOLDIER_UPPER_MAX": 0.20, "LONG_BODY": 0.60},
    "base":    {},
    "loose":   {"DOJI_BODY_MAX": 0.15, "MARUBOZU_SHADOW_MAX": 0.10, "HAMMER_LOWER_MIN": 1.5,
                "HAMMER_UPPER_MAX": 0.35, "STAR_SMALL_BODY": 0.40, "SOLDIER_UPPER_MAX": 0.40, "LONG_BODY": 0.40},
    "relative_long_body": {"RELATIVE_LONG": True},
}


@contextmanager
def thresholds(overrides):
    saved = {k: getattr(C, k, None) for k in overrides}
    for k, v in overrides.items():
        setattr(C, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                delattr(C, k)
            else:
                setattr(C, k, v)


def detect_relative(df):
    """Same rules, but 'long' first candle = body above its own 10-day average body."""
    d = P.detect(df)
    body = (df["Close"] - df["Open"]).abs()
    avg10 = body.rolling(10).mean().shift(1)
    long_now = body > avg10
    long_prev, long_2ago = long_now.shift(1, fill_value=False), long_now.shift(2, fill_value=False)
    with thresholds({"LONG_BODY": 0.0}):          # remove the shape rule, then apply the size rule
        d0 = P.detect(df)
    for name, mask in [("bullish_harami", long_prev), ("bearish_harami", long_prev),
                       ("morning_star", long_2ago), ("evening_star", long_2ago)]:
        d[name] = d0[name] & mask.fillna(False)
    return d


def p_value(t: float) -> float:
    return math.erfc(abs(t) / math.sqrt(2))          # two-sided, normal approximation


def summarise(stats: pd.DataFrame, label: str) -> dict:
    s = stats[stats["signals"] >= C.MIN_SIGNALS].copy()
    s["p"] = s["t_stat"].apply(p_value)
    s["right_way"] = s.apply(lambda r: DIRECTION[r["pattern"]] == 0 or
                             (r["t_stat"] > 0) == (DIRECTION[r["pattern"]] > 0), axis=1)
    m = len(s)
    passed = int(((s["t_stat"].abs() >= 2) & s["right_way"]).sum())
    bonf = int(((s["p"] <= 0.05 / m) & s["right_way"]).sum()) if m else 0
    ranked = s.sort_values("p").reset_index(drop=True)
    k = 0
    for i, p in enumerate(ranked["p"], start=1):          # Benjamini-Hochberg
        if p <= 0.05 * i / m:
            k = i
    bh = int(ranked.head(k)["right_way"].sum()) if k else 0
    s5 = stats[(stats["horizon_days"] == 5) & (stats["signals"] > 0)].copy()
    s5["dir"] = s5["pattern"].map(DIRECTION)
    def pooled_edge(direction):
        g = s5[s5["dir"] == direction]
        return round(float((g["edge_pp"] * g["signals"]).sum() / g["signals"].sum()), 2) if len(g) else None
    return {"setting": label, "tests_with_enough_signals": m, "passed_|t|>=2": passed,
            "expected_by_chance_~5pct": round(0.05 * m, 1), "survive_bonferroni": bonf,
            "survive_benjamini_hochberg": bh, "bullish_edge_5d_pp": pooled_edge(1),
            "bearish_edge_5d_pp": pooled_edge(-1)}


def main() -> None:
    prices = {k: load(k)[0] for k in C.INSTRUMENTS}
    rows = []
    for label, overrides in SETTINGS.items():
        with thresholds({k: v for k, v in overrides.items() if k != "RELATIVE_LONG"}):
            stats = []
            for key, df in prices.items():
                d = detect_relative(df) if overrides.get("RELATIVE_LONG") else P.detect(df)
                stats.append(pattern_stats(forward_returns(d), C.INSTRUMENTS[key]["name"]))
            rows.append(summarise(pd.concat(stats, ignore_index=True), label))
    out = pd.DataFrame(rows)
    out.to_csv(C.OUTPUTS / "sensitivity.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
