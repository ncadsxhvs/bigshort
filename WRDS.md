## Product Requirements Document (PRD): Quant Research Analyst Bot

**Status:** Draft | **Version:** 1.0 | **Author:** Quantitative Research Lead

---

### 1. Project Overview

The **Quant Research Analyst Bot** is a long-term research tool designed to analyze macro-assets (Gold/XAU) and growth indices (NASDAQ 100) using high-fidelity data from **Wharton Research Data Services (WRDS)**. The goal is to move beyond simple technical indicators into "Quantamental" modeling, integrating structural economic data with high-frequency market dynamics.

### 2. Target Data Suites (WRDS)

To fulfill the research requirements, the bot will interface with the following primary datasets via the WRDS API:

| Dataset | Research Purpose | Key Data Points |
| --- | --- | --- |
| **CRSP (Daily/Intraday)** | Benchmarking & Backtesting | Adjusted returns, prices, and shares outstanding for NDX constituents. |
| **Compustat (IDXCST)** | Universe Management | Historical NASDAQ 100 index constituents to avoid **survivorship bias**. |
| **Refinitiv Datastream** | Macro-Asset Analysis | Historical Gold (XAU/USD) spot prices, real yields (TIPS), and USD Index. |
| **NYSE TAQ** | Market Microstructure | Intraday tick data for analyzing slippage and liquidity cascades in NDX. |
| **RavenPack/SEC Analytics** | Sentiment/Narrative | Sentiment scores for FOMC minutes and "Fedspeak" (Central Bank Alpha). |

---

### 3. Functional Requirements

#### 3.1 Data Engineering Pipeline

* **Multi-Asset Synchronization:** The bot must align daily Gold prices with the 4:00 PM EST close of the NASDAQ 100.
* **Survivorship Bias Correction:** Queries must use `comp.idxcst_his` to ensure backtests only use companies that were actually in the NDX at the time.
* **Feature Engineering:**
* **Macro-Regime:** Rolling 60-day correlation between Gold and US 10Y Real Rates.
* **Volatility Spreads:** Ratio of NDX Implied Volatility (VIX) vs. Gold Volatility (GVZ).
* **Sentiment Delta:** Week-over-week change in "Hawkishness" scores from RavenPack.



#### 3.2 Modeling & Analysis

* **Regime Switching:** Implement a Hidden Markov Model (HMM) to detect "Risk-On" (NDX Alpha) vs. "Safe Haven" (Gold Alpha) environments.
* **Factor Sensitivity:** Measure NDX constituent sensitivity to interest rate shocks using CRSP return data.
* **Execution Research:** Use TAQ data to simulate "VWAP" (Volume Weighted Average Price) entry and exit to estimate realistic transaction costs.

---

### 4. Technical Specifications

* **Environment:** Python 3.11+ running on **WRDS Cloud** (to minimize latency when querying TAQ data).
* **Core Libraries:** * `wrds`: For direct PostgreSQL access to data.
* `pandas`: For vectorised time-series manipulation.
* `statsmodels`: For GARCH and regime-switching models.
* `scikit-learn / XGBoost`: For non-linear signal processing.


* **Authentication:** MFA-enabled connection via `.pgpass` file for automated script execution.

---

### 5. Research Milestones

1. **Phase 1 (The Foundation):** Automate the daily pull of NDX constituents and Gold prices. Calculate the rolling correlation.
2. **Phase 2 (The Macro Trigger):** Integrate FRED (Federal Reserve) data through WRDS to layer in Real Yields as a predictive feature for Gold.
3. **Phase 3 (The Narrative):** Connect to RavenPack to test if "Fedspeak" sentiment leads price action in the NASDAQ 100 by $>24$ hours.
4. **Phase 4 (The Strategy):** Backtest a "Long-Only" strategy that rotates between NDX and Gold based on the HMM regime detector.

---

### 6. User Constraints (Professor's Notes)

* **Zero-Inference Rule:** The bot should prioritize raw WRDS data over inferred "market mood" unless sentiment scores are sourced directly from RavenPack/SEC.
* **Academic Rigor:** All backtests must include a 5bps slippage assumption and utilize the WRDS `delist` tables from CRSP to handle failed companies.

---

**Next Step:** Would you like me to generate the specific **SQL Join queries** that merge the CRSP returns with the RavenPack sentiment scores for this bot?