"""Step 2 - Label every candle and detect classic candlestick patterns.

Anatomy of a candle (all in price units):
    body  = |close - open|           range = high - low
    upper = high - max(open, close)  lower = min(open, close) - low
Each pattern is a clear numeric rule on these quantities (thresholds in config.py),
so results are reproducible and testable. A pattern is stamped on the candle
where it completes (the last candle of a 2- or 3-candle pattern).
"""
import numpy as np
import pandas as pd

import config as C

# Direction each pattern is expected to predict (+1 bullish, -1 bearish, 0 neutral)
DIRECTION = {
    "doji": 0, "hammer": 1, "bullish_marubozu": 1, "bearish_marubozu": -1,
    "bullish_engulfing": 1, "bearish_engulfing": -1, "bullish_harami": 1, "bearish_harami": -1,
    "morning_star": 1, "evening_star": -1, "three_white_soldiers": 1, "three_black_crows": -1,
}


def anatomy(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    o, h, l, c = d["Open"], d["High"], d["Low"], d["Close"]
    d["body"] = (c - o).abs()
    d["range"] = (h - l).replace(0, np.nan)          # a zero-range candle can't be classified
    d["upper"] = h - np.maximum(o, c)
    d["lower"] = np.minimum(o, c) - l
    d["bull"] = c > o
    d["bear"] = c < o
    d["prior_return"] = c.shift(1) / c.shift(1 + C.TREND_LOOKBACK) - 1   # trend before this candle
    return d


def detect(df: pd.DataFrame) -> pd.DataFrame:
    d = anatomy(df)
    body, rng, up, lo, bull, bear = d["body"], d["range"], d["upper"], d["lower"], d["bull"], d["bear"]
    o, c = d["Open"], d["Close"]
    p = {}  # pattern name -> boolean Series

    # ---- single-candle ----
    p["doji"] = body <= C.DOJI_BODY_MAX * rng
    p["hammer"] = (~p["doji"] & (lo >= C.HAMMER_LOWER_MIN * body) & (up <= C.HAMMER_UPPER_MAX * rng)
                   & (d["prior_return"] < 0))                                   # after a decline
    maru = (up <= C.MARUBOZU_SHADOW_MAX * rng) & (lo <= C.MARUBOZU_SHADOW_MAX * rng)
    p["bullish_marubozu"] = maru & bull
    p["bearish_marubozu"] = maru & bear

    # ---- two-candle (previous = shift(1)) ----
    po, pc, pbody, prng = o.shift(1), c.shift(1), body.shift(1), rng.shift(1)
    pbull, pbear = bull.shift(1, fill_value=False), bear.shift(1, fill_value=False)
    p["bullish_engulfing"] = pbear & bull & (o <= pc) & (c >= po) & (body > pbody)
    p["bearish_engulfing"] = pbull & bear & (o >= pc) & (c <= po) & (body > pbody)
    long_prev = pbody >= C.LONG_BODY * prng
    p["bullish_harami"] = pbear & long_prev & bull & (o > pc) & (c < po)       # inside previous body
    p["bearish_harami"] = pbull & long_prev & bear & (o < pc) & (c > po)

    # ---- three-candle (1 = two candles ago, 2 = previous, 3 = current) ----
    o1, c1, b1, r1 = o.shift(2), c.shift(2), body.shift(2), rng.shift(2)
    b2 = body.shift(1)
    bull1, bear1 = bull.shift(2, fill_value=False), bear.shift(2, fill_value=False)
    long1 = b1 >= C.LONG_BODY * r1
    small2 = b2 <= C.STAR_SMALL_BODY * b1
    mid1 = (o1 + c1) / 2
    p["morning_star"] = bear1 & long1 & small2 & bull & (c > mid1)
    p["evening_star"] = bull1 & long1 & small2 & bear & (c < mid1)

    o2, c2 = o.shift(1), c.shift(1)
    bull2, bear2 = bull.shift(1, fill_value=False), bear.shift(1, fill_value=False)
    up1, up2 = d["upper"].shift(2), d["upper"].shift(1)
    lo1, lo2 = d["lower"].shift(2), d["lower"].shift(1)
    b1_, b2_ = body.shift(2), body.shift(1)
    p["three_white_soldiers"] = (
        bull1 & bull2 & bull & (c2 > c1) & (c > c2)
        & (o2 > o1) & (o2 < c1) & (o > o2) & (o < c2)                          # each opens inside prior body
        & (up1 <= C.SOLDIER_UPPER_MAX * b1_) & (up2 <= C.SOLDIER_UPPER_MAX * b2_) & (up <= C.SOLDIER_UPPER_MAX * body))
    p["three_black_crows"] = (
        bear1 & bear2 & bear & (c2 < c1) & (c < c2)
        & (o2 < o1) & (o2 > c1) & (o < o2) & (o > c2)
        & (lo1 <= C.SOLDIER_UPPER_MAX * b1_) & (lo2 <= C.SOLDIER_UPPER_MAX * b2_) & (lo <= C.SOLDIER_UPPER_MAX * body))

    for name, s in p.items():
        d[name] = s.fillna(False).astype(bool)
    names = list(p)
    d["patterns"] = d[names].apply(lambda r: ", ".join(n for n in names if r[n]), axis=1)
    d["candle_type"] = np.select([p["doji"].fillna(False), d["bull"], d["bear"]],
                                 ["doji", "bullish", "bearish"], default="flat")
    return d


PATTERNS = list(DIRECTION)
