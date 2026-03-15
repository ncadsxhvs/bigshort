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


def cmd_research(args: argparse.Namespace) -> None:
    tickers = _parse_tickers(args.tickers)
    market = MarketStore()
    features = FeatureStore()
    signals = SignalStore()

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
    elif args.command == "paper":
        cmd_paper(args)
    elif args.command == "live":
        cmd_live(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
