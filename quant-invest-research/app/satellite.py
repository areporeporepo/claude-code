"""Alternative data: satellite imagery.

Watching a company's *physical* footprint is a classic quant "alt-data" edge:
for a property developer, the fastest-moving real-world signal is construction
itself — land clearing, new roads, rising buildings, and finished units you can
literally count from orbit. For Vinhomes (Vingroup's real-estate arm), the
anchor site is Vinhomes Royal Island on Vũ Yên Island, Hải Phòng, Vietnam — a
large greenfield development whose build-out pace is a proxy for delivery risk
and future revenue recognition.

This module gives you:
  * verifiable, hard-coded coordinates for the sites of interest (so the
    "where" is auditable), and
  * a Sentinel Hub client that fetches a true-colour image for a site and a
    date range. Sentinel Hub has a free tier; supply SENTINELHUB_CLIENT_ID /
    SENTINELHUB_CLIENT_SECRET to enable it.

Without credentials the fetch is skipped and the module still returns the
site metadata, so the rest of the app keeps working offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import settings


@dataclass(frozen=True)
class Site:
    key: str
    name: str
    lat: float
    lon: float
    note: str


# Verifiable, auditable points of interest. Coordinates are approximate site
# centroids and are meant to be checked against public maps, not treated as
# survey-grade. Cross-check before relying on any of them.
SITES: dict[str, Site] = {
    "vinhomes_vu_yen": Site(
        key="vinhomes_vu_yen",
        name="Vinhomes Royal Island (Vu Yen Island), Hai Phong, Vietnam",
        lat=20.8550,
        lon=106.7600,
        note="Vinhomes' Vu Yen Island 'Royal Island' development. "
        "Construction pace here — land clearing, roads, rising buildings, "
        "finished units — is a proxy for delivery progress and revenue "
        "recognition. VERIFY the centroid against public maps before use.",
    ),
}


@dataclass
class SatelliteResult:
    site: Site
    fetched: bool
    image_bytes: Optional[bytes] = None
    reason: str = ""


def _bbox(lat: float, lon: float, half_deg: float = 0.02) -> list[float]:
    """A small WGS84 bounding box around the point (minLon, minLat, maxLon, maxLat)."""
    return [lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg]


def fetch_true_color(site_key: str, date_from: str, date_to: str,
                     width: int = 512, height: int = 512) -> SatelliteResult:
    """Fetch a true-colour PNG for a site over [date_from, date_to] (YYYY-MM-DD).

    Returns SatelliteResult with fetched=False and a reason when credentials
    are missing or the request fails — never raises for missing config.
    """
    site = SITES.get(site_key)
    if site is None:
        return SatelliteResult(site=None, fetched=False,
                               reason=f"unknown site '{site_key}'")

    if not (settings.sentinelhub_client_id and settings.sentinelhub_client_secret):
        return SatelliteResult(
            site=site, fetched=False,
            reason="SENTINELHUB_CLIENT_ID/SECRET not set; skipping live fetch.",
        )

    try:
        import requests
    except ImportError:
        return SatelliteResult(site=site, fetched=False,
                               reason="`requests` not installed")

    try:
        # 1) OAuth2 client-credentials token
        token_resp = requests.post(
            "https://services.sentinel-hub.com/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.sentinelhub_client_id,
                "client_secret": settings.sentinelhub_client_secret,
            },
            timeout=20,
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]

        # 2) Process API request for a true-colour image
        evalscript = (
            "//VERSION=3\n"
            "function setup(){return{input:['B02','B03','B04'],"
            "output:{bands:3}};}\n"
            "function evaluatePixel(s){return [2.5*s.B04,2.5*s.B03,2.5*s.B02];}"
        )
        body = {
            "input": {
                "bounds": {"bbox": _bbox(site.lat, site.lon)},
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {"timeRange": {
                        "from": f"{date_from}T00:00:00Z",
                        "to": f"{date_to}T23:59:59Z",
                    }},
                }],
            },
            "output": {"width": width, "height": height,
                       "responses": [{"identifier": "default",
                                      "format": {"type": "image/png"}}]},
            "evalscript": evalscript,
        }
        img_resp = requests.post(
            "https://services.sentinel-hub.com/api/v1/process",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
            timeout=60,
        )
        img_resp.raise_for_status()
        return SatelliteResult(site=site, fetched=True, image_bytes=img_resp.content)
    except Exception as e:
        return SatelliteResult(site=site, fetched=False,
                               reason=f"fetch failed: {e}")
