"""CLI entry point: python -m bigshort research|paper|live"""

from __future__ import annotations

import argparse
import asyncio
import logging

from bigshort import config
from bigshort.core.stores import MarketStore, FeatureStore, SignalStore
from bigshort.core.orchestrator import run_research, run_live
from bigshort.core.bus import EventBus
from bigshort.agents.data_agent import DataAgent
from bigshort.agents.feature_agent import FeatureAgent
from bigshort.agents.sentiment_agent import SentimentAgent
from bigshort.agents.regime_agent import RegimeAgent
from bigshort.agents.signal_agent import SignalAgent
from bigshort.agents.strategist import StrategistAgent
from bigshort.agents.execution_agent import ExecutionAgent
from bigshort.agents.human_gate import HumanGate


def _parse_tickers(raw: str | None) -> dict[str, str]:
    """Parse 'key=TICKER,key=TICKER' into a dict, merged with defaults."""
    tickers = dict(config.DEFAULT_TICKERS)
    if not raw:
        return tickers
    for pair in raw.split(","):
        pair = pair.strip()
        if "=" in pair:
            key, val = pair.split("=", 1)
            tickers[key.strip()] = val.strip()
    return tickers


def _build_agents(
    market: MarketStore,
    features: FeatureStore,
    signals: SignalStore,
    tickers: dict[str, str],
    gate_mode: str,
    poll_interval: float,
) -> list:
    gate = HumanGate(mode=gate_mode)
    return [
        DataAgent(market, tickers=tickers, poll_interval=poll_interval),
        FeatureAgent(market, features),
        SentimentAgent(poll_interval=config.SENTIMENT_INTERVAL),
        RegimeAgent(features),
        SignalAgent(market, features, signals),
        StrategistAgent(features, signals, gate=gate),
        ExecutionAgent(market, signals),
    ]


def _print_results(
    results: dict,
    tickers: dict[str, str],
    feature_store: FeatureStore,
) -> None:
    regime_result = results.get("regime", {})
    signal_result = results.get("signal", {})
    strat_result = results.get("strategist", {})
    exec_result = results.get("execution", {})

    # Header
    ticker_list = ", ".join(f"{k.upper()} ({v})" for k, v in tickers.items())
    print(f"\n{'='*60}")
    print(f"  BigShort Research Report")
    print(f"{'='*60}")
    print(f"\n  Tickers: {ticker_list}")

    # Regime
    regime = regime_result.get("regime", -1)
    confidence = regime_result.get("confidence", 0)
    regime_label = {0: "Risk-On", 1: "Safe-Haven"}.get(regime, "Unknown")
    print(f"\n--- Regime ---")
    print(f"  State:      {regime_label} ({regime})")
    print(f"  Confidence: {confidence:.2%}")

    # Features snapshot
    snap = feature_store.snapshot()
    if not snap.empty:
        print(f"\n--- Features (latest) ---")
        for col in snap.columns:
            val = snap[col].iloc[0]
            print(f"  {col:.<30s} {val:>12.4f}")

    # Signals
    sigs = signal_result.get("signals", {})
    vote = signal_result.get("vote", 0)
    vote_label = {1: "BUY", -1: "SELL", 0: "HOLD"}.get(vote, str(vote))
    print(f"\n--- Signals ---")
    for name, val in sigs.items():
        label = {1: "BUY", -1: "SELL", 0: "FLAT"}.get(val, str(val))
        print(f"  {name:.<20s} {label}")
    print(f"  {'consensus':.<20s} {vote_label}")

    # Decision
    proposal = strat_result.get("proposal")
    side = strat_result.get("side", "hold")
    print(f"\n--- Decision ---")
    print(f"  Action:     {side.upper()}")
    if proposal and hasattr(proposal, "reasoning"):
        print(f"  Reasoning:  {proposal.reasoning}")
        print(f"  Confidence: {proposal.confidence:.2%}")

    # Execution
    if exec_result.get("filled"):
        print(f"\n--- Execution ---")
        print(f"  Price:    {exec_result['price']:.2f}")
        print(f"  Slippage: {exec_result['slippage']:.4f}")
    else:
        print(f"\n--- Execution ---")
        print(f"  No trade executed")

    print(f"\n{'='*60}\n")


STAGES = {
    "data":       lambda m, f, s, t: [DataAgent(m, tickers=t)],
    "features":   lambda m, f, s, t: [DataAgent(m, tickers=t), FeatureAgent(m, f)],
    "sentiment":  lambda m, f, s, t: [SentimentAgent()],
    "regime":     lambda m, f, s, t: [DataAgent(m, tickers=t), FeatureAgent(m, f), RegimeAgent(f)],
    "signals":    lambda m, f, s, t: [
        DataAgent(m, tickers=t), FeatureAgent(m, f), RegimeAgent(f),
        SignalAgent(m, f, s),
    ],
    "strategies": lambda m, f, s, t: [
        DataAgent(m, tickers=t), FeatureAgent(m, f), RegimeAgent(f),
        SignalAgent(m, f, s),
        StrategistAgent(f, s, gate=HumanGate(mode="observe")),
        ExecutionAgent(m, s),
    ],
}


def cmd_research(args: argparse.Namespace) -> None:
    tickers = _parse_tickers(args.tickers)
    market = MarketStore()
    features = FeatureStore()
    signals = SignalStore()
    stage = args.stage

    if stage and stage not in STAGES:
        print(f"Unknown stage: {stage}")
        print(f"Available: {', '.join(STAGES.keys())}")
        return

    if stage:
        agents = STAGES[stage](market, features, signals, tickers)
    else:
        agents = [
            DataAgent(market, tickers=tickers),
            FeatureAgent(market, features),
            SentimentAgent(),
            RegimeAgent(features),
            SignalAgent(market, features, signals),
            StrategistAgent(features, signals, gate=HumanGate(mode="observe")),
            ExecutionAgent(market, signals),
        ]

    data = {"start": args.start, "end": args.end}
    results = run_research(agents, data)

    signals.flush()

    _print_results(results, tickers, features)


def _print_strategy_report(name: str, report: dict) -> None:
    print(f"  Total return:     {report['total_return']:>8.2%}")
    print(f"  Annualized:       {report['annualized_return']:>8.2%}")
    print(f"  Sharpe ratio:     {report['sharpe_ratio']:>8.2f}")
    print(f"  Max drawdown:     {report['max_drawdown']:>8.2%}")
    if "n_trades" in report and report["n_trades"] > 0:
        print(f"  Trades:           {report['n_trades']:>8d}")
        print(f"  Win rate:         {report['win_rate']:>8.2%}")
        print(f"  Profit factor:    {report['profit_factor']:>8.2f}")
        print(f"  Avg win:          {report['avg_win']:>8.4%}")
        print(f"  Avg loss:         {report['avg_loss']:>8.4%}")


def cmd_backtest(args: argparse.Namespace) -> None:
    import pandas as pd
    from datetime import datetime, timedelta
    from bigshort.data.yfinance import YFinanceSource
    from bigshort.strategy.macd_backtest import run_macd_backtest, macd_signals
    from bigshort.strategy.straddle import detect_low_vol_entries
    from bigshort.strategy.execution import simulate_execution
    from bigshort.strategy.voting import signal_vote
    from bigshort.features.correlation import rolling_correlation
    from bigshort.features.vix_calc import realized_vol_index
    from bigshort.features.kalman import kalman_smooth
    from bigshort.features.heikin_ashi import heikin_ashi
    from bigshort.features.macd import macd
    from bigshort.strategy.report import backtest_report

    ticker = args.ticker
    years = args.years
    end = datetime.now()
    start = end - timedelta(days=int(years * 365.25))
    slippage = args.slippage

    print(f"\n{'='*60}")
    print(f"  Backtest: {ticker}")
    print(f"  Period:   {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}")
    print(f"  Slippage: {slippage}bps")
    print(f"{'='*60}")

    # ── Fetch data ──
    src = YFinanceSource()
    print(f"\n  Fetching {ticker}...")
    df = src.fetch(ticker, start=start.strftime("%Y-%m-%d"))
    close = df["close"]
    print(f"  Loaded {len(close)} trading days")
    print(f"  Price range: {close.min():.2f} → {close.max():.2f}")

    # ── Features ──
    vol = realized_vol_index(close)
    smoothed = kalman_smooth(close)
    macd_df = macd(close)

    has_ohlc = {"open", "high", "low", "close"} <= set(df.columns)
    ha_df = heikin_ashi(df) if has_ohlc else None

    # Fetch benchmark for correlation (Gold as safe-haven proxy)
    try:
        gold_df = src.fetch("GC=F", start=start.strftime("%Y-%m-%d"))
        gold_close = gold_df["close"].reindex(close.index).ffill()
        corr = rolling_correlation(close, gold_close)
    except Exception:
        gold_close = None
        corr = None

    # ── 1. Buy & Hold ──
    bh_returns = close.pct_change().fillna(0)
    bh_report = backtest_report(bh_returns)

    # ── 2. MACD Crossover ──
    macd_result = run_macd_backtest(close, slippage_bps=slippage)
    macd_sigs = macd_result["signals"]
    # Reconstruct held position for trade stats
    macd_pos = pd.Series(0, index=close.index)
    p = 0
    for i, s in enumerate(macd_sigs):
        if s == 1: p = 1
        elif s == -1: p = 0
        macd_pos.iloc[i] = p
    macd_returns = macd_result["returns"]
    macd_report = backtest_report(macd_returns, macd_pos)

    # ── 3. Straddle (low-vol entry → hold until vol expands) ──
    vol_clean = vol.dropna()
    low_vol = detect_low_vol_entries(vol_clean)
    straddle_pos = pd.Series(0, index=close.index, name="straddle")
    vol_median = vol_clean.median()
    in_pos = False
    for i in range(len(close)):
        date = close.index[i]
        if date in low_vol.index and low_vol.loc[date]:
            in_pos = True
        elif date in vol_clean.index and vol_clean.loc[date] > vol_median:
            in_pos = False
        straddle_pos.iloc[i] = 1 if in_pos else 0
    straddle_returns = simulate_execution(close, straddle_pos, slippage_bps=slippage)
    straddle_report = backtest_report(straddle_returns, straddle_pos)

    # ── 4. Kalman Trend Following ──
    kalman_pos = (close > smoothed).astype(int)
    kalman_returns = simulate_execution(close, kalman_pos, slippage_bps=slippage)
    kalman_report = backtest_report(kalman_returns, kalman_pos)

    # ── 5. Heikin-Ashi Trend ──
    if ha_df is not None:
        ha_pos = (ha_df["ha_close"] > ha_df["ha_open"]).astype(int)
        ha_returns = simulate_execution(close, ha_pos, slippage_bps=slippage)
        ha_report = backtest_report(ha_returns, ha_pos)
    else:
        ha_report = None

    # ── 6. Signal Voting (consensus of all strategies) ──
    vote_signals: dict[str, pd.Series] = {
        "macd": macd_sigs.clip(-1, 1),
        "straddle": straddle_pos.map({1: 1, 0: 0}),
        "kalman": kalman_pos.map({1: 1, 0: -1}),
    }
    if ha_df is not None:
        vote_signals["heikin_ashi"] = ha_pos.map({1: 1, 0: -1})
    consensus = signal_vote(vote_signals, threshold=0.5)
    vote_pos = pd.Series(0, index=close.index)
    pos = 0
    for i, v in enumerate(consensus):
        if v == 1: pos = 1
        elif v == -1: pos = 0
        vote_pos.iloc[i] = pos
    vote_returns = simulate_execution(close, vote_pos, slippage_bps=slippage)
    vote_report = backtest_report(vote_returns, vote_pos)

    # ── Print Results ──
    print(f"\n--- Buy & Hold ---")
    _print_strategy_report("Buy & Hold", bh_report)

    print(f"\n--- MACD Crossover ---")
    _print_strategy_report("MACD", macd_report)

    print(f"\n--- Straddle (low-vol entry) ---")
    _print_strategy_report("Straddle", straddle_report)

    print(f"\n--- Kalman Trend Following ---")
    _print_strategy_report("Kalman", kalman_report)

    if ha_report is not None:
        print(f"\n--- Heikin-Ashi Trend ---")
        _print_strategy_report("Heikin-Ashi", ha_report)

    print(f"\n--- Signal Voting (consensus) ---")
    _print_strategy_report("Consensus", vote_report)

    # ── Comparison Table ──
    strategies = [
        ("Buy & Hold", bh_report),
        ("MACD", macd_report),
        ("Straddle", straddle_report),
        ("Kalman", kalman_report),
        ("Consensus", vote_report),
    ]
    if ha_report is not None:
        strategies.insert(4, ("Heikin-Ashi", ha_report))

    print(f"\n--- Strategy Comparison ---")
    print(f"  {'Strategy':<14s} {'Return':>8s} {'Sharpe':>7s} {'MaxDD':>8s} {'Trades':>7s} {'WinRate':>8s} {'PF':>6s}")
    print(f"  {'-'*14} {'-'*8} {'-'*7} {'-'*8} {'-'*7} {'-'*8} {'-'*6}")
    for name, rpt in strategies:
        n = rpt.get("n_trades", "-")
        wr = f"{rpt['win_rate']:.0%}" if "win_rate" in rpt else "-"
        pf = f"{rpt['profit_factor']:.2f}" if "profit_factor" in rpt else "-"
        n_str = str(n) if isinstance(n, int) else n
        print(
            f"  {name:<14s} {rpt['total_return']:>7.2%} "
            f"{rpt['sharpe_ratio']:>7.2f} {rpt['max_drawdown']:>8.2%} "
            f"{n_str:>7s} {wr:>8s} {pf:>6s}"
        )

    best = max(strategies, key=lambda x: x[1]["sharpe_ratio"])
    print(f"\n  Best risk-adjusted: {best[0]} (Sharpe {best[1]['sharpe_ratio']:.2f})")

    # ── Current State ──
    trend = "UP" if smoothed.iloc[-1] > smoothed.iloc[-20] else "DOWN"
    macd_mom = "BULLISH" if macd_df["histogram"].iloc[-1] > 0 else "BEARISH"
    ha_trend = ""
    if ha_df is not None:
        ha_trend = "BULLISH" if ha_df["ha_close"].iloc[-1] > ha_df["ha_open"].iloc[-1] else "BEARISH"

    print(f"\n--- Current State ---")
    print(f"  Kalman trend:     {trend}")
    print(f"  MACD momentum:    {macd_mom}")
    if ha_trend:
        print(f"  Heikin-Ashi:      {ha_trend}")
    print(f"  Realized vol:     {vol.iloc[-1]:.2f}%")
    if corr is not None:
        print(f"  Gold correlation: {corr.iloc[-1]:.4f}")
    print(f"  Consensus vote:   {int(consensus.iloc[-1]):+d}")

    print(f"\n{'='*60}\n")

    # Save data
    store = MarketStore()
    store.append(ticker.lower().replace("^", "").replace("=", ""), df)


def cmd_paper(args: argparse.Namespace) -> None:
    tickers = _parse_tickers(args.tickers)
    market = MarketStore()
    features = FeatureStore()
    signals = SignalStore()
    agents = _build_agents(market, features, signals, tickers, "auto", args.poll_interval)

    bus = EventBus()
    print(f"Paper trading — polling every {args.poll_interval}s (Ctrl+C to stop)")
    try:
        asyncio.run(run_live(agents, bus))
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        signals.flush()


def cmd_live(args: argparse.Namespace) -> None:
    tickers = _parse_tickers(args.tickers)
    market = MarketStore()
    features = FeatureStore()
    signals = SignalStore()
    agents = _build_agents(market, features, signals, tickers, "approve", args.poll_interval)

    bus = EventBus()
    print(f"Live trading — polling every {args.poll_interval}s (Ctrl+C to stop)")
    try:
        asyncio.run(run_live(agents, bus))
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        signals.flush()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")

    parser = argparse.ArgumentParser(prog="bigshort", description="BigShort trading platform")
    sub = parser.add_subparsers(dest="command")

    # shared ticker arg for all subcommands
    ticker_help = (
        "Comma-separated key=TICKER pairs to override defaults. "
        "e.g. 'ndx=^NDX,gold=GC=F' or 'ndx=AAPL,gold=GLD,vix=^VIX,gvz=^GVZ'"
    )

    # research
    p_research = sub.add_parser("research", help="Run batch research backtest")
    p_research.add_argument("--start", default=config.DEFAULT_START)
    p_research.add_argument("--end", default=config.DEFAULT_END)
    p_research.add_argument("--tickers", default=None, help=ticker_help)
    p_research.add_argument(
        "--stage", default=None,
        help="Run a single stage: data, features, sentiment, regime, signals, strategies",
    )

    # backtest
    p_bt = sub.add_parser("backtest", help="Backtest strategies on a single ticker")
    p_bt.add_argument("ticker", help="Yahoo Finance ticker (e.g. AAPL, ^NDX, GC=F)")
    p_bt.add_argument("--years", type=float, default=3.0, help="Lookback in years (default: 3)")
    p_bt.add_argument("--slippage", type=int, default=5, help="Slippage in bps (default: 5)")

    # paper
    p_paper = sub.add_parser("paper", help="Paper trading with simulated execution")
    p_paper.add_argument("--poll-interval", type=float, default=config.POLL_INTERVAL)
    p_paper.add_argument("--tickers", default=None, help=ticker_help)

    # live
    p_live = sub.add_parser("live", help="Live trading (requires broker)")
    p_live.add_argument("--poll-interval", type=float, default=config.POLL_INTERVAL)
    p_live.add_argument("--broker", default="alpaca")
    p_live.add_argument("--tickers", default=None, help=ticker_help)

    args = parser.parse_args()

    if args.command == "research":
        cmd_research(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "paper":
        cmd_paper(args)
    elif args.command == "live":
        cmd_live(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
