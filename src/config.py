"""Settings: instruments, history window, pattern thresholds and research horizons."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"

# Continuous front-month futures (daily OHLC). Stooq symbol, Yahoo symbol (fallback)
INSTRUMENTS = {
    "crude_oil": {"stooq": "cl.f", "yahoo": "CL=F", "name": "WTI Crude Oil"},
    "gold":      {"stooq": "gc.f", "yahoo": "GC=F", "name": "Gold"},
    "sp500":     {"stooq": "es.f", "yahoo": "ES=F", "name": "E-mini S&P 500"},
    "tnote10":   {"stooq": "zn.f", "yahoo": "ZN=F", "name": "10-Year T-Note"},
}
START_DATE = "2010-01-01"

# Pattern thresholds (fractions of the candle's high-low range or body)
DOJI_BODY_MAX = 0.10          # doji: body at most 10% of the range
MARUBOZU_SHADOW_MAX = 0.05    # marubozu: each shadow at most 5% of the range
HAMMER_LOWER_MIN = 2.0        # hammer: lower shadow at least 2x the body
HAMMER_UPPER_MAX = 0.25       # hammer: upper shadow at most 25% of the range
TREND_LOOKBACK = 5            # hammer / reversal context: prior 5-day return
STAR_SMALL_BODY = 0.30        # star: middle body at most 30% of the first body
SOLDIER_UPPER_MAX = 0.30      # soldiers/crows: shadow at the close end at most 30% of the body
LONG_BODY = 0.50              # "long" first candle: body at least 50% of its range

HORIZONS = [1, 5, 10]         # forward returns measured after each pattern (trading days)
MIN_SIGNALS = 30              # minimum occurrences before a result is called significant
