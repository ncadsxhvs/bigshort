"""ContextBuilder — assembles structured LLM context (~2000 tokens)."""

from __future__ import annotations

from bigshort.core.events import RegimeEvent, SignalEvent, SentimentEvent
from bigshort.core.stores import FeatureStore, SignalStore


class ContextBuilder:
    """Builds a text summary for the StrategistAgent LLM prompt."""

    def __init__(self, feature_store: FeatureStore, signal_store: SignalStore) -> None:
        self._features = feature_store
        self._signals = signal_store

    def build(
        self,
        regime: RegimeEvent | None = None,
        signal: SignalEvent | None = None,
        sentiment: SentimentEvent | None = None,
    ) -> str:
        sections: list[str] = ["# Market Context\n"]

        # Regime
        if regime and regime.new_regime >= 0:
            label = "Risk-On" if regime.new_regime == 0 else "Safe-Haven"
            sections.append(
                f"## Regime: {label} (state={regime.new_regime}, "
                f"confidence={regime.confidence:.2f})"
            )
        else:
            sections.append("## Regime: Unknown")

        # Signals
        if signal:
            sections.append(f"\n## Signal Vote: {signal.vote}")
            for name, val in signal.signals_dict.items():
                label = {1: "BUY", -1: "SELL", 0: "FLAT"}.get(val, str(val))
                sections.append(f"  - {name}: {label}")
        else:
            sections.append("\n## Signals: None")

        # Features snapshot
        snap = self._features.snapshot()
        if not snap.empty:
            sections.append("\n## Latest Features")
            for col in snap.columns:
                sections.append(f"  - {col}: {snap[col].iloc[0]:.4f}")

        # Sentiment
        if sentiment and sentiment.scores:
            sections.append("\n## Sentiment")
            for k, v in sentiment.scores_dict.items():
                sections.append(f"  - {k}: {v:.4f}")

        # Portfolio
        portfolio = self._signals.get_portfolio()
        if portfolio:
            sections.append("\n## Portfolio")
            for ticker, pos in portfolio.items():
                sections.append(f"  - {ticker}: {pos:+.2f}")

        # Recent trades
        trades = self._signals.get_trades(n=5)
        if not trades.empty:
            sections.append("\n## Last 5 Trades")
            for _, row in trades.iterrows():
                sections.append(
                    f"  - {row.get('side', '?')} {row.get('ticker', '?')} "
                    f"@ {row.get('price', 0):.2f}"
                )

        return "\n".join(sections)
