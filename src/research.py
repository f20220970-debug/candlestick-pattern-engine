"""Step 3 - Do the patterns predict anything?

For every pattern occurrence we measure the forward return over 1, 5 and 10 trading
days (close of the pattern candle to the close h days later) and compare with ALL days:
  * hit rate: share of signals where price moved in the pattern's predicted direction
    (bullish: up, bearish: down; doji has no direction, so 'up' is reported)
  * base rate: the same share across all days, i.e. what you'd get with no signal
  * edge = hit rate - base rate, in percentage points
  * t-stat of the mean forward return versus the all-days mean
A result is flagged only if there are at least MIN_SIGNALS occurrences, |t| >= 2 and the
move is in the predicted direction. Caveat: 5- and 10-day windows overlap when signals
are close together, which makes t-stats look better than they are.
"""
import numpy as np
import pandas as pd

import config as C
from patterns import DIRECTION, PATTERNS


def forward_returns(d: pd.DataFrame) -> pd.DataFrame:
    for h in C.HORIZONS:
        d[f"fwd_{h}d"] = d["Close"].shift(-h) / d["Close"] - 1
    return d


def pattern_stats(d: pd.DataFrame, instrument: str) -> pd.DataFrame:
    rows = []
    for h in C.HORIZONS:
        f = d[f"fwd_{h}d"].dropna()
        mu_all, sd_all = f.mean(), f.std()
        up_all = (f > 0).mean()
        for name in PATTERNS:
            direction = DIRECTION[name]
            r = d.loc[d[name], f"fwd_{h}d"].dropna()
            n = len(r)
            if n == 0:
                rows.append({"instrument": instrument, "pattern": name, "horizon_days": h, "signals": 0})
                continue
            hit = (r < 0).mean() if direction < 0 else (r > 0).mean()
            base = 1 - up_all if direction < 0 else up_all
            t = (r.mean() - mu_all) / (sd_all / np.sqrt(n))
            significant = n >= C.MIN_SIGNALS and abs(t) >= 2 and (direction == 0 or np.sign(t) == direction)
            rows.append({
                "instrument": instrument, "pattern": name, "horizon_days": h, "signals": n,
                "avg_fwd_return_pct": round(100 * r.mean(), 3),
                "all_days_avg_pct": round(100 * mu_all, 3),
                "hit_rate_pct": round(100 * hit, 1), "base_rate_pct": round(100 * base, 1),
                "edge_pp": round(100 * (hit - base), 1), "t_stat": round(t, 2),
                "significant": bool(significant),
            })
    return pd.DataFrame(rows)


def pooled(stats: pd.DataFrame) -> pd.DataFrame:
    """Across all instruments: signal-weighted hit rate and edge per pattern and horizon."""
    s = stats[stats["signals"] > 0].copy()
    s["w_hit"] = s["hit_rate_pct"] * s["signals"]
    s["w_base"] = s["base_rate_pct"] * s["signals"]
    g = s.groupby(["pattern", "horizon_days"]).agg(signals=("signals", "sum"),
                                                   w_hit=("w_hit", "sum"), w_base=("w_base", "sum"))
    g["hit_rate_pct"] = (g["w_hit"] / g["signals"]).round(1)
    g["base_rate_pct"] = (g["w_base"] / g["signals"]).round(1)
    g["edge_pp"] = (g["hit_rate_pct"] - g["base_rate_pct"]).round(1)
    return g.drop(columns=["w_hit", "w_base"]).reset_index()
