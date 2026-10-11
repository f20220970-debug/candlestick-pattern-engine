"""Step 1 - Get daily OHLC prices.

Order of sources for each instrument:
  1. a CSV you saved yourself in data/raw/<instrument>.csv (Date,Open,High,Low,Close)
  2. Stooq's free CSV download
  3. Yahoo Finance via the yfinance package, if installed
Every source is cleaned the same way: sorted by date, duplicates removed, and
impossible candles (high below low, open/close outside the high-low range,
non-positive prices) dropped and counted.
"""
import io

import pandas as pd
import requests

import config as C


def from_stooq(symbol: str) -> pd.DataFrame:
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    if "Close" not in df.columns:
        raise ValueError(f"Stooq returned no data for {symbol}")
    return df


def from_yahoo(symbol: str) -> pd.DataFrame:
    import yfinance as yf  # optional dependency
    df = yf.download(symbol, start=C.START_DATE, progress=False, auto_adjust=False)
    if df.empty:
        raise ValueError(f"Yahoo returned no data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.reset_index()


def clean(df: pd.DataFrame) -> tuple:
    df = df.rename(columns=str.title)[["Date", "Open", "High", "Low", "Close"]].copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    df = df.dropna().drop_duplicates("Date").sort_values("Date")
    df = df[df["Date"] >= C.START_DATE]
    ok = ((df["High"] >= df["Low"]) & (df[["Open", "Close"]].max(axis=1) <= df["High"])
          & (df[["Open", "Close"]].min(axis=1) >= df["Low"]) & (df["Low"] > 0))
    return df[ok].reset_index(drop=True), int((~ok).sum())


def load(key: str) -> tuple:
    spec = C.INSTRUMENTS[key]
    local = C.RAW_DIR / f"{key}.csv"
    if local.exists():
        raw, source = pd.read_csv(local), "local CSV"
    else:
        try:
            raw, source = from_stooq(spec["stooq"]), "Stooq"
        except Exception as e1:
            try:
                raw, source = from_yahoo(spec["yahoo"]), "Yahoo"
            except Exception as e2:
                raise SystemExit(f"No data for {key}: Stooq ({e1}); Yahoo ({e2}). "
                                 f"Save a CSV to {local} with Date,Open,High,Low,Close.")
        C.RAW_DIR.mkdir(parents=True, exist_ok=True)
        raw.to_csv(local, index=False)
    df, dropped = clean(raw)
    print(f"  {spec['name']}: {len(df):,} candles from {source} "
          f"({df['Date'].min():%Y-%m-%d} to {df['Date'].max():%Y-%m-%d}), {dropped} invalid dropped")
    return df, source, dropped
