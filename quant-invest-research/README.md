# Quant Investment Research API

A small, honest **backend service** for researching an asset the way a quant
would: pull **verifiable market data**, compute **quant indicators**, and layer
in **satellite / alternative data** to cross-check the story on the ground.

The worked example is **Vinhomes** (Vingroup's real-estate arm, ticker **`VHM`**
on the Ho Chi Minh Stock Exchange), with the physical anchor site being
**Vinhomes Royal Island on Vũ Yên Island, Hải Phòng** — but every ticker and
site is configurable.

> ⚠️ **Not financial advice.** This is an educational/research tool. It reports
> what the numbers *are* — it does **not** tell you whether to buy, sell, or
> whether "now is a good/bad time." It cannot, and it won't. Personalized advice
> requires a licensed professional who knows your full situation. See
> [Responsible use](#responsible-use).

---

## Why this exists

You asked, in effect: *"What's the best way to invest right now?"* The honest
answer is that no tool — and no one who doesn't know your finances, horizon, and
risk tolerance — can responsibly answer that for you. What a tool *can* do is
give you the **framework and the evidence** a professional would use, so you can
reason for yourself. That's what this backend is.

## What it does

| Layer | What you get | Source |
|-------|--------------|--------|
| **Market data** | Daily closing prices | Alpha Vantage / Finnhub (your key), or an offline synthetic stub |
| **Quant indicators** | Total return, annualized volatility, Sharpe ratio, max drawdown, SMA/EMA, RSI, trend label | Computed locally, pure Python |
| **Alt-data (satellite)** | True-colour imagery of a tracked physical site (e.g. the Vũ Yên construction footprint) + auditable coordinates | Sentinel Hub (your key) |

## Quick start

```bash
cd quant-invest-research
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Runs offline out of the box with SYNTHETIC data (PRICE_PROVIDER=stub):
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs
```

To use real data, copy the env template and add your keys:

```bash
cp .env.example .env      # then edit .env — never commit it
# set PRICE_PROVIDER=alphavantage (or finnhub) and paste your key
```

### Endpoints

- `GET /snapshot?ticker=VHM.VN` — full quant snapshot
- `GET /satellite/sites` — verifiable coordinates of tracked sites
- `GET /satellite/image?site=vinhomes_vu_yen&date_from=2024-01-01&date_to=2024-03-01` — true-colour PNG (or a JSON explainer if no Sentinel Hub key)
- `GET /health`, `GET /` — service info

## About the API keys you offered

Please **do not paste keys into chat or commit them.** The service only ever
reads them from environment variables (`.env`, which is git-ignored). You keep
control of your own credentials. Free tiers are enough to start:

- **Market data:** [Alpha Vantage](https://www.alphavantage.co/support/#api-key) or [Finnhub](https://finnhub.io/register)
- **Satellite:** [Sentinel Hub](https://www.sentinel-hub.com/) (Sentinel-2, free tier)

> Note on Vietnamese equities: HOSE tickers like `VHM` have thinner coverage on
> global free APIs than US tickers. If your provider returns nothing for
> `VHM.VN`, that's a data-coverage gap, not a bug — you may need a vendor with
> Vietnam/HOSE coverage. The `stub` provider always works for testing the
> pipeline.

## Reading the numbers (quick quant glossary)

- **Annualized volatility** — how much the price bounces around per year. Higher = riskier/more uncertain.
- **Sharpe ratio** — return earned per unit of risk, above the risk-free rate. Higher is better; it says nothing about *future* returns.
- **Max drawdown** — the worst peak-to-trough drop in the window. How bad it has historically felt to hold.
- **RSI (14)** — momentum oscillator, 0–100. Conventionally >70 "overbought", <30 "oversold". A heuristic, not a signal.
- **SMA/EMA + trend** — moving-average relationships summarizing whether price is above/below its recent averages.

All of these are **descriptive of the past**. None of them predict the future,
and none of them constitute advice.

## Satellite / alternative data

For a property developer, construction *is* the fundamental. Comparing satellite
images of Vũ Yên Island across dates lets you see land clearing, new roads, and
rising buildings — a real-world check on whether delivery is on pace with what
management reports. Coordinates in `app/satellite.py` are approximate centroids
and are meant to be **verified against public maps** before you rely on them.

## Testing

```bash
pytest -q          # pure, offline unit tests for the indicator math
```

## Responsible use

- Research and education only. **Not** investment advice or a recommendation.
- Nothing here says whether to invest, or whether the timing is good or bad.
- Data may be synthetic (stub), delayed, or incomplete — verify independently.
- Past performance and historical indicators do not predict future results.
- For decisions about your money, consult a licensed financial professional.

## Project layout

```
quant-invest-research/
├── app/
│   ├── config.py          # env-only configuration (no secrets in code)
│   ├── data_providers.py  # market data: stub | alphavantage | finnhub
│   ├── indicators.py      # pure quant math (tested)
│   ├── analysis.py        # assemble a snapshot
│   ├── satellite.py       # Sentinel Hub alt-data + verifiable coordinates
│   └── main.py            # FastAPI app
├── tests/test_indicators.py
├── requirements.txt
├── .env.example
└── README.md
```
