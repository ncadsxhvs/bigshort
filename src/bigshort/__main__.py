"""CLI entry point: python -m bigshort"""

from __future__ import annotations

from bigshort.etl.pipeline import run_daily_pull
from bigshort.features.correlation import rolling_correlation, volatility_spread


def main() -> None:
    print("BigShort — running daily pull …")
    data = run_daily_pull()

    print(f"Assets loaded: {list(data.keys())}")
    print(f"Date range: {data['ndx'].index[0].date()} → {data['ndx'].index[-1].date()}")

    gold_close = data["gold"]["close"]
    ndx_close = data["ndx"]["close"]
    vix_close = data["vix"]["close"]
    gvz_close = data["gvz"]["close"]

    # Gold / NDX rolling correlation
    corr = rolling_correlation(gold_close, ndx_close)
    print(f"\nGold ↔ NDX 60-day rolling correlation (latest): {corr.iloc[-1]:.4f}")

    # Vol spread
    vs = volatility_spread(vix_close, gvz_close)
    print(f"VIX/GVZ vol spread (latest): {vs.iloc[-1]:.4f}")


if __name__ == "__main__":
    main()
