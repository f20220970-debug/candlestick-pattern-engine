"""Draw the last N candles of an instrument with detected patterns marked."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from patterns import DIRECTION, PATTERNS


def draw(d, title: str, path, last: int = 120) -> None:
    x = d.tail(last).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(13, 5.5))
    for i, r in x.iterrows():
        colour = "#2E8B57" if r["Close"] >= r["Open"] else "#C0392B"
        ax.vlines(i, r["Low"], r["High"], color=colour, linewidth=0.8)
        ax.vlines(i, min(r["Open"], r["Close"]), max(r["Open"], r["Close"]), color=colour, linewidth=4)
    span = x["High"].max() - x["Low"].min()
    for i, r in x.iterrows():
        found = [n for n in PATTERNS if r[n] and n != "doji"]
        if not found:
            continue
        bull = sum(DIRECTION[n] for n in found) >= 0
        y = r["Low"] - 0.03 * span if bull else r["High"] + 0.03 * span
        ax.scatter(i, y, marker="^" if bull else "v", color="#2E8B57" if bull else "#C0392B", s=40, zorder=3)
        ax.annotate(found[0].replace("_", " "), (i, y), fontsize=6.5, rotation=90,
                    xytext=(0, -38 if bull else 6), textcoords="offset points", ha="center")
    step = max(1, last // 10)
    ax.set_xticks(range(0, len(x), step))
    ax.set_xticklabels([dt.strftime("%Y-%m-%d") for dt in x["Date"].iloc[::step]], rotation=30, fontsize=8)
    ax.set_title(f"{title}: last {last} daily candles with detected patterns", fontsize=11)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
