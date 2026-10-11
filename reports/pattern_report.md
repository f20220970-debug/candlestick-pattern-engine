# Candlestick Pattern Report

## 1. Data
| instrument | source | candles | from | to | invalid_dropped |
| --- | --- | --- | --- | --- | --- |
| WTI Crude Oil | Yahoo | 4216 | 2010-01-04 | 2026-10-09 | 2 |
| Gold | Yahoo | 4193 | 2010-01-04 | 2026-10-09 | 25 |
| E-mini S&P 500 | Yahoo | 4217 | 2010-01-04 | 2026-10-09 | 2 |
| 10-Year T-Note | Yahoo | 4212 | 2010-01-04 | 2026-10-09 | 5 |

16,838 daily candles labelled; 4,436 directional pattern signals (excluding doji).

## 2. Pattern counts
| pattern | WTI Crude Oil | Gold | E-mini S&P 500 | 10-Year T-Note |
| --- | --- | --- | --- | --- |
| doji | 428 | 493 | 487 | 404 |
| hammer | 107 | 105 | 102 | 94 |
| bullish_marubozu | 7 | 129 | 36 | 17 |
| bearish_marubozu | 8 | 137 | 10 | 35 |
| bullish_engulfing | 210 | 149 | 287 | 264 |
| bearish_engulfing | 228 | 188 | 233 | 223 |
| bullish_harami | 189 | 162 | 123 | 144 |
| bearish_harami | 145 | 138 | 175 | 165 |
| morning_star | 78 | 84 | 71 | 67 |
| evening_star | 59 | 73 | 82 | 71 |
| three_white_soldiers | 5 | 3 | 11 | 3 |
| three_black_crows | 5 | 5 | 2 | 7 |

## 3. Does each pattern predict the next 5 days? (all instruments pooled)
Hit rate = share of signals followed by a move in the predicted direction; base rate = the same share on all days;
edge = hit rate - base rate (percentage points).

| pattern | direction | signals | hit_rate_pct | base_rate_pct | edge_pp |
| --- | --- | --- | --- | --- | --- |
| three_black_crows | bearish | 19 | 68.4 | 47.1 | 21.3 |
| bearish_marubozu | bearish | 190 | 52.1 | 45.8 | 6.3 |
| doji | neutral | 1810 | 56.7 | 54.6 | 2.1 |
| bearish_harami | bearish | 623 | 44.9 | 45.6 | -0.7 |
| bearish_engulfing | bearish | 870 | 44.8 | 45.7 | -0.9 |
| bullish_harami | bullish | 618 | 52.7 | 54.0 | -1.3 |
| hammer | bullish | 407 | 52.3 | 54.4 | -2.1 |
| bullish_engulfing | bullish | 910 | 52.2 | 54.5 | -2.3 |
| morning_star | bullish | 300 | 52.0 | 54.3 | -2.3 |
| evening_star | bearish | 285 | 40.4 | 45.4 | -5.0 |
| bullish_marubozu | bullish | 189 | 50.3 | 55.4 | -5.1 |
| three_white_soldiers | bullish | 22 | 45.4 | 56.3 | -10.9 |

## 4. Statistically notable results (per instrument, any horizon)
Rule: at least 30 signals, |t| >= 2, and the move in the predicted direction.

| instrument | pattern | horizon_days | signals | avg_fwd_return_pct | hit_rate_pct | base_rate_pct | edge_pp | t_stat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E-mini S&P 500 | bullish_harami | 5 | 123 | 0.685 | 65.0 | 60.3 | 4.7 | 2.14 |
| 10-Year T-Note | bearish_marubozu | 5 | 35 | -0.266 | 65.7 | 50.2 | 15.5 | -2.05 |

Out of 108 pattern/instrument/horizon tests with enough signals, 2 passed.
With a 2-sigma rule, about 5% would pass by chance alone, so a handful of passes is not evidence of an edge.

### Analyst commentary
<!-- COMMENTARY -->
Across 16,838 daily candles and 4,436 signals, classic candlestick patterns showed no reliable edge: only 2 of 108 pattern-instrument-horizon tests passed the |t| >= 2 rule, fewer than the roughly 5 expected by chance. Bullish patterns such as hammers and bullish engulfings were followed by up-moves about 52% of the time, slightly below the 54-55% base rate, because these markets drift upwards anyway. The largest edges (three black crows +21 points, three white soldiers -11 points) come from only 19-22 signals and are not trustworthy. The two passing results (S&P 500 bullish harami and T-Note bearish marubozu over 5 days) are borderline and appear for a single instrument and horizon, so I would test them out of sample before using them. Gold shows far more marubozus than the other markets and had 25 invalid candles, which points to data-quality issues in the source rather than a real pattern. Conclusion: patterns on their own are not a trading signal; they might add value only combined with trend, volatility or news context.
<!-- COMMENTARY -->

## 5. Method
- Rules use candle anatomy (body, range, upper and lower shadows); thresholds are in `src/config.py`.
- A 2- or 3-candle pattern is stamped on the candle where it completes; hammers require a prior 5-day decline.
- Forward return = close of the signal candle to the close h trading days later (h = 1, 5, 10).
- Caveats: continuous front-month futures include roll jumps; overlapping 5/10-day windows inflate t-stats;
  testing many patterns at once makes some false positives likely; no transaction costs are included.
