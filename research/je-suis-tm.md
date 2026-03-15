# PRD: Project Alpha - Quantamental Trading Framework

## 1. Executive Summary
**Project Alpha** is a modular quantitative trading and research framework built in Python. It integrates the "Quantamental" philosophy—merging technical signals with macroeconomic drivers—to identify a statistical edge in the **Gold (XAU)** and **NASDAQ 100 (NDX)** markets. 

The goal is to move beyond simple indicators into automated strategy research, risk modeling, and options execution.

---

## 2. Core Modules & Strategies

### A. Options Strategy Suite
* **Options Straddle:** Automated detection of low-volatility regimes to enter long straddles/strangles ahead of high-impact events.
* **VIX Calculator:** Custom implementation of volatility indexing to gauge market fear/complacency for NDX hedging.
* **The "Wheel" & Butterfly:** Systematic strike selection for cash-secured puts (income) and neutral-bias Iron Butterflies.

### B. Quantamental & Macro Analysis
* **Oil Money Project:** Correlation engine tracking CAD/NOK and related equities against Crude Oil prices.
* **Monte Carlo Project:** 10,000+ path simulations to stress-test portfolio drawdowns and "Risk of Ruin."
* **Pair Trading:** Statistical arbitrage (Mean Reversion) between highly correlated assets (e.g., NVDA vs. AMD).
* **Portfolio Optimization:** Mean-Variance and Black-Litterman models for dynamic asset allocation.
* **Smart Farmers Project:** Predictive modeling for agricultural commodities based on seasonality and supply data.
* **Wisdom of the Crowd:** Sentiment analysis module scraping **Reddit (r/WallStreetBets)** and news via **NewsAPI**.

### C. Technical Indicator Engine (Pattern Recognition)
* **Momentum:** Awesome Oscillator, MACD, and RSI Pattern Recognition.
* **Volatility/Trend:** Bollinger Bands (Squeeze/Expansion), Parabolic SAR, and Dual Thrust.
* **Intraday:** London Breakout strategy for early-morning FX/Gold volatility.
* **Price Action:** Heikin-Ashi for trend smoothing and automated "Shooting Star" candle detection.

---

## 3. Data Engineering & Sourcing Architecture

| Tier | Source | Data Usage |
| :--- | :--- | :--- |
| **Institutional** | **WRDS / Bloomberg / Eikon** | High-fidelity fundamental and historical backtesting data. |
| **Exchange** | **CME / LME** | Futures and Commodities (Gold, Oil) pricing. |
| **Equity/FX** | **yfinance / Stooq / Quandl** | Daily OHLCV for NDX and Global Equities. |
| **Alternative** | **Reddit / Web Scraping** | Sentiment scores and ticker mention frequency. |
| **Macro** | **Macrotrends / FRED** | Interest rates, CPI, and GDP for "Quantamental" context. |
| **Historical** | **Histdata / FX Historical** | Tick-level data for high-resolution FX backtesting. |

---

## 4. Modeling & Research Pipeline

1.  **ETL Layer:** Airflow-managed DAGs to pull from multi-source APIs (yfinance, WRDS).
2.  **Denoising:** Kalman Filtering to extract "true" price trends from volatile assets like Gold.
3.  **Feature Engineering:** Conversion of raw OHLCV into Z-scores, RSI patterns, and Volatility buckets.
4.  **Backtesting:** * *Vectorized:* (Vectorbt) for rapid indicator optimization.
    * *Event-Driven:* For complex Options strategies (Straddles).
5.  **Execution Logic:** Signal voting system where trades trigger only when Technical + Quantamental modules align.

---

## 5. Technical Stack

* **Language:** Python 3.10+
* **Data Ops:** Apache Airflow, Docker, PostgreSQL (Metadata storage).
* **Analytics:** Pandas, NumPy, SciPy, Scikit-Learn.
* **Visualization:** Plotly Dash / Matplotlib.
* **Backtesting:** Vectorbt or Backtrader.

---

## 6. Development Roadmap
* **Phase 1:** Build the Multi-Source ETL connector (yfinance + WRDS).
* **Phase 2:** Implement the Kalman Filter and Heikin-Ashi smoothing modules.
* **Phase 3:** Deploy the VIX Calculator and Options Straddle logic.
* **Phase 4:** Integrate Reddit Sentiment (Wisdom of the Crowd) as a trade filter.