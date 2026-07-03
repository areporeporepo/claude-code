"""FastAPI backend exposing the quant snapshot and alt-data endpoints.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs

Every response that carries market numbers also carries an explicit disclaimer
and a flag telling you whether the data is real or synthetic. This service is
for research and education. It does not provide personalized financial advice
or buy/sell recommendations.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse

from .analysis import snapshot_dict
from .config import settings
from .data_providers import ProviderError, get_price_series
from .satellite import SITES, fetch_true_color

DISCLAIMER = (
    "Educational/research use only. Not investment advice, not a recommendation "
    "to buy or sell any security, and not a statement about whether now is a good "
    "or bad time to invest. Data may be synthetic or delayed. Verify independently "
    "and consult a licensed professional before making decisions."
)

app = FastAPI(
    title="Quant Investment Research API",
    version="0.1.0",
    description="Backend for market-data quant indicators + satellite alt-data. "
    + DISCLAIMER,
)


@app.get("/")
def root():
    return {
        "service": "quant-invest-research",
        "price_provider": settings.price_provider,
        "default_ticker": settings.default_ticker,
        "endpoints": ["/health", "/snapshot", "/satellite/sites",
                      "/satellite/image", "/docs"],
        "disclaimer": DISCLAIMER,
    }


@app.get("/health")
def health():
    return {"status": "ok", "price_provider": settings.price_provider}


@app.get("/snapshot")
def snapshot(ticker: str | None = None):
    """Quant snapshot (returns, volatility, Sharpe, drawdown, MAs, RSI, trend)."""
    try:
        series = get_price_series(ticker)
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=f"data provider error: {e}")
    data = snapshot_dict(series, risk_free=settings.risk_free_rate)
    return JSONResponse({"snapshot": data, "disclaimer": DISCLAIMER})


@app.get("/satellite/sites")
def satellite_sites():
    """Verifiable, auditable coordinates for the physical sites we track."""
    return {
        "sites": {k: vars(v) for k, v in SITES.items()},
        "note": "Coordinates are approximate site centroids; verify against "
        "public maps before relying on them.",
    }


@app.get("/satellite/image")
def satellite_image(site: str = "vinhomes_vu_yen",
                    date_from: str = "2024-01-01",
                    date_to: str = "2024-03-01"):
    """Fetch a true-colour satellite image (PNG) for a tracked site.

    Returns image/png on success. If Sentinel Hub credentials are missing or
    the fetch fails, returns 200 JSON explaining why (so the pipeline never
    hard-fails just because a key is absent).
    """
    result = fetch_true_color(site, date_from, date_to)
    if result.fetched and result.image_bytes:
        return Response(content=result.image_bytes, media_type="image/png")
    return JSONResponse({
        "fetched": False,
        "site": vars(result.site) if result.site else None,
        "reason": result.reason,
        "how_to_enable": "Set SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET "
        "(free tier at https://www.sentinel-hub.com/).",
    })
