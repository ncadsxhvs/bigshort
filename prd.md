# BigShort — Quantamental Trading & Research Platform

## 1. Thesis

Traditional quant strategies treat macro fundamentals and technical signals as separate domains. BigShort fuses them: macro regime detection (Gold/Real-Yield correlation, volatility spreads) determines *when* to trade, while technical and sentiment signals determine *what* and *how*. The core hypothesis is that regime-aware signal filtering produces fewer but higher-quality trades than either approach alone.

**Target markets:** Gold (XAU) and NASDAQ 100 (NDX) — chosen for their inverse correlation during macro stress events.

---

## 2. Research Questions

1. Does the Gold/US 10Y Real Rate rolling correlation reliably predict risk-off environments?
2. Can HMM regime detection (Risk-On vs. Safe-Haven) improve risk-adjusted returns over buy-and-hold?
3. Does Fedspeak sentiment lead NDX price action by >24 hours (Granger causality)?
4. Does requiring Technical + Quantamental signal alignment reduce false positives without sacrificing returns?

---

## 3. Data Sources

| Source | Data | Frequency | Usage |
|--------|------|-----------|-------|
| yfinance | OHLCV for NDX, Gold, VIX, GVZ | Daily | Price series, volatility |
| FRED | 10Y Treasury, TIPS, CPI, GDP | Daily/Monthly | Real yield, macro features |
| NewsAPI | Financial news headlines | Daily | Fedspeak hawkishness scoring |
| Reddit (r/WSB) | Ticker mentions, sentiment | Daily | Retail sentiment indicator |

### Alignment Rules
- All daily data aligned to 4:00 PM EST NDX close
- Point-in-time index membership for survivorship-bias-free backtests
- 5bps minimum slippage assumption on all backtests

---

## 4. Analysis Framework

### 4.1 Macro Regime Detection

**Hidden Markov Model (HMM)** trained on:
- Rolling 60-day Gold vs. US 10Y Real Rate correlation
- VIX/GVZ volatility spread ratio
- Week-over-week Fedspeak hawkishness delta

Outputs two states: **Risk-On** (NDX alpha) and **Safe-Haven** (Gold alpha).

### 4.2 Technical Indicators

| Category | Indicators |
|----------|-----------|
| Trend | Kalman filter (price denoising), Heikin-Ashi smoothing |
| Momentum | MACD, Awesome Oscillator, RSI |
| Volatility | Custom VIX calculator, Bollinger squeeze/expansion |
| Causality | Granger causality test (sentiment → price) |

### 4.3 Sentiment Scoring

- **Fedspeak hawkishness:** Keyword-scored news headlines (hawkish/dovish lexicon)
- **Retail sentiment:** Reddit r/WSB ticker mention frequency and sentiment polarity
- **Sentiment delta:** Week-over-week change as a leading indicator

### 4.4 Signal Voting

Individual strategies (MACD, rotation, straddle) each produce directional signals (+1/0/−1). A consensus vote determines action — trades require alignment across multiple signal sources.

---

## 5. Strategies

### 5.1 Regime-Based Rotation
Long-only allocation between NDX and Gold based on HMM regime state. Rebalance on regime transitions.

### 5.2 Volatility Straddle
Enter straddles during low-vol regimes (VIX below rolling threshold) ahead of anticipated macro events. Exit on vol expansion.

### 5.3 MACD Momentum
Standard MACD crossover signals filtered by regime state — only take momentum trades aligned with the current regime direction.

---

## 6. Performance Measurement

- Sharpe ratio (annualized)
- Maximum drawdown
- Win rate and profit factor
- Comparison vs. buy-and-hold benchmarks (SPY, GLD)
- Survivorship-bias-free returns
- Transaction cost impact analysis (slippage sensitivity)

---

## 7. LLM-Assisted Research

A single LLM agent acts as an interpretive layer:
- **Trade gating:** Given signal votes + regime + sentiment, decide act/wait/hold
- **Anomaly explanation:** When correlations break or regimes shift unexpectedly
- **Backtest review:** Analyze results, suggest parameter adjustments, identify overfitting risk

The LLM receives a structured context summary (~2000 tokens) of current market state and responds with a structured trade decision including confidence and reasoning.

---

## 8. Constraints & Principles

- **Zero-Inference Rule:** Raw sourced data over inferred sentiment
- **Academic Rigor:** Survivorship bias correction, realistic slippage, point-in-time data
- **Signal Alignment:** No single indicator triggers a trade — consensus required
- **Human Oversight:** All live trades require human approval; paper trading runs autonomously

---

## 9. Scope & Future Work

**In scope:** Research backtesting, paper trading simulation, LLM-assisted analysis.

**Future:**
- Live brokerage execution (Alpaca integration)
- WRDS data (CRSP, Compustat, TAQ, RavenPack)
- Pair trading (mean reversion: NVDA/AMD)
- Oil/currency correlation engine (CAD/NOK vs. Crude)
- Agricultural commodity seasonality
- Monte Carlo drawdown/Risk-of-Ruin simulations
- Black-Litterman portfolio optimization
