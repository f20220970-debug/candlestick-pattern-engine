"""Run everything: get prices -> label candles and detect patterns -> measure forward
returns -> write CSVs, charts and reports/pattern_report.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd  # noqa: E402

import config as C  # noqa: E402
from chart import draw  # noqa: E402
from data import load  # noqa: E402
from patterns import DIRECTION, PATTERNS, detect  # noqa: E402
from research import forward_returns, pattern_stats, pooled  # noqa: E402

MARK = "<!-- COMMENTARY -->"


def md(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    return "\n".join([head, sep] + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])


def kept_commentary(path: Path) -> str:
    default = "_Write 3-5 sentences in your own words: which patterns showed an edge, whether it held across instruments and horizons, and what you'd conclude for trading._"
    if path.exists():
        parts = path.read_text(encoding="utf-8").split(MARK)
        if len(parts) == 3:
            return parts[1].strip()
    return default


def main() -> None:
    C.OUTPUTS.mkdir(exist_ok=True)
    C.REPORTS.mkdir(exist_ok=True)
    print("Data")
    all_stats, counts, info = [], [], []
    for key, spec in C.INSTRUMENTS.items():
        df, source, dropped = load(key)
        d = forward_returns(detect(df))
        cols = ["Date", "Open", "High", "Low", "Close", "candle_type", "patterns"]
        d[cols].to_csv(C.OUTPUTS / f"labelled_{key}.csv", index=False)
        draw(d, spec["name"], C.OUTPUTS / f"chart_{key}.png")
        all_stats.append(pattern_stats(d, spec["name"]))
        counts.append({"instrument": spec["name"], **{n: int(d[n].sum()) for n in PATTERNS}})
        info.append({"instrument": spec["name"], "source": source, "candles": len(d),
                     "from": f"{d['Date'].min():%Y-%m-%d}", "to": f"{d['Date'].max():%Y-%m-%d}",
                     "invalid_dropped": dropped})

    stats = pd.concat(all_stats, ignore_index=True)
    pool = pooled(stats)
    stats.to_csv(C.OUTPUTS / "pattern_stats.csv", index=False)
    pool.to_csv(C.OUTPUTS / "pattern_stats_pooled.csv", index=False)
    cnt = pd.DataFrame(counts)
    cnt.to_csv(C.OUTPUTS / "pattern_counts.csv", index=False)

    sig = stats[stats["significant"] == True]  # noqa: E712
    p5 = pool[pool["horizon_days"] == 5].copy()
    p5["direction"] = p5["pattern"].map(lambda n: {1: "bullish", -1: "bearish", 0: "neutral"}[DIRECTION[n]])
    p5 = p5[["pattern", "direction", "signals", "hit_rate_pct", "base_rate_pct", "edge_pp"]].sort_values("edge_pp", ascending=False)
    total_signals = int(cnt[[n for n in PATTERNS if n != "doji"]].sum().sum())
    candles = sum(i["candles"] for i in info)

    out = C.REPORTS / "pattern_report.md"
    commentary = kept_commentary(out)
    text = f"""# Candlestick Pattern Report

## 1. Data
{md(pd.DataFrame(info))}

{candles:,} daily candles labelled; {total_signals:,} directional pattern signals (excluding doji).

## 2. Pattern counts
{md(cnt.set_index("instrument").T.reset_index().rename(columns={"index": "pattern"}))}

## 3. Does each pattern predict the next 5 days? (all instruments pooled)
Hit rate = share of signals followed by a move in the predicted direction; base rate = the same share on all days;
edge = hit rate - base rate (percentage points).

{md(p5)}

## 4. Statistically notable results (per instrument, any horizon)
Rule: at least {C.MIN_SIGNALS} signals, |t| >= 2, and the move in the predicted direction.

{md(sig[["instrument", "pattern", "horizon_days", "signals", "avg_fwd_return_pct", "hit_rate_pct", "base_rate_pct", "edge_pp", "t_stat"]]) if len(sig) else "_None: no pattern passed the significance rule._"}

Out of {int((stats["signals"] >= C.MIN_SIGNALS).sum())} pattern/instrument/horizon tests with enough signals, {len(sig)} passed.
With a 2-sigma rule, about 5% would pass by chance alone, so a handful of passes is not evidence of an edge.

### Analyst commentary
{MARK}
{commentary}
{MARK}

## 5. Method
- Rules use candle anatomy (body, range, upper and lower shadows); thresholds are in `src/config.py`.
- A 2- or 3-candle pattern is stamped on the candle where it completes; hammers require a prior 5-day decline.
- Forward return = close of the signal candle to the close h trading days later (h = {", ".join(map(str, C.HORIZONS))}).
- Caveats: continuous front-month futures include roll jumps; overlapping 5/10-day windows inflate t-stats;
  testing many patterns at once makes some false positives likely; no transaction costs are included.
"""
    out.write_text(text, encoding="utf-8")
    print(f"Done: {candles:,} candles, {total_signals:,} signals, {len(sig)} notable results -> {out.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
