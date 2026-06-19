"""
CoinGecko Price Fetcher — current price + 24h stats (no API key required)

Fetches from /api/v3/coins/markets for:
  - Current price (USD)
  - 24h price change (USD and %)
  - 24h high / low
  - 24h volume

Usage:
    python coingecko_price.py              # Fetch prices for hardcoded COINS
    python coingecko_price.py --list-coins # List all supported CoinGecko IDs
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = os.environ.get("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")

# ─────────────────────────────────────────────────────────────────────────────
# COINS — CoinGecko coin IDs mapped from Matrixport symbol names.
# Run with --list-coins to search for IDs you need.
# ─────────────────────────────────────────────────────────────────────────────
COINS = {
    "1INCHUSDT":  "1inch",
    "AAVEUSDT":   "aave",
    "APEUSDT":    "apecoin",
    "ARBUSDT":    "arbitrum",
    "AVAXUSDT":   "avalanche-2",
    "AXSUSDT":    "axie-infinity",
    "BATUSDT":    "basic-attention-token",
    "BCHUSDT":    "bitcoin-cash",
    "BNBUSDT":    "binancecoin",
    "BONKUSDT":   "bonk",
    "BTCUSDT":    "bitcoin",
    "CAKEUSDT":   "pancakeswap-token",
    "CHZUSDT":    "chiliz",
    "COMPUSDT":   "compound-governance-token",
    "CRVUSDT":    "curve-dao-token",
    "DCRUSDT":    "decred",
    "DOGEUSDT":   "dogecoin",
    "DOTUSDT":    "polkadot",
    "EIGENUSDT":  "eigenlayer",
    "ENSUSDT":    "ethereum-name-service",
    "ETCUSDT":    "ethereum-classic",
    "ETHUSDT":    "ethereum",
    "FETUSDT":    "fetch-ai",
    "FLOKIUSDT":  "floki",
    "FTTUSDT":    "ftx-token",
    "GALAUSDT":   "gala",
    "GMXUSDT":    "gmx",
    "GRTUSDT":    "the-graph",
    "LINKUSDT":   "chainlink",
    "LTCUSDT":    "litecoin",
    "NEARUSDT":   "near",
    "OPUSDT":     "optimism",
    "ORDIUSDT":   "ordinals",
    "PEOPLEUSDT": "constitutiondao",
    "PEPEUSDT":   "pepe",
    "POLUSDT":    "polygon-ecosystem-token",
    "PYTHUSDT":   "pyth-network",
    "RENDERUSDT": "render-token",
    "SANDUSDT":   "the-sandbox",
    "SHIBUSDT":   "shiba-inu",
    "SOLUSDT":    "solana",
    "SUSHIUSDT":  "sushi",
    "TONUSDT":    "the-open-network",
    "TRXUSDT":    "tron",
    "UNIUSDT":    "uniswap",
    "USDCUSDT":   "usd-coin",
    "WLDUSDT":    "worldcoin-wld",
    # XAGMUSDT / XAUMUSDT are Matrixport-specific precious metal tokens — not listed on CoinGecko
    "XECUSDT":    "ecash",
    "XLMUSDT":    "stellar",
    "XRPUSDT":    "ripple",
    "ZECUSDT":    "zcash",
}


def fetch_markets(coin_ids: list[str]) -> list[dict]:
    """Fetch market data for a list of CoinGecko IDs in one request."""
    url = BASE_URL + "/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "price_change_percentage": "24h",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_coin_list() -> list[dict]:
    """Fetch the full CoinGecko coin list (id + symbol + name)."""
    url = BASE_URL + "/coins/list"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fmt_price(value) -> str:
    if value is None:
        return "N/A"
    if abs(value) >= 1:
        return f"{value:,.4f}"
    return f"{value:.8f}"


def fmt_change(value) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CoinGecko Price Fetcher")
    parser.add_argument(
        "--list-coins",
        metavar="QUERY",
        nargs="?",
        const="",
        help="Search CoinGecko coin list by symbol or name (e.g. --list-coins sol)",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("  CoinGecko Price Fetcher — Current Price + 24h Stats")
    print("=" * 80)
    print()

    if args.list_coins is not None:
        query = args.list_coins.lower()
        print(f"  Fetching full CoinGecko coin list{f' (filter: {query!r})' if query else ''}...")
        coin_list = fetch_coin_list()
        matches = [
            c for c in coin_list
            if not query or query in c["symbol"].lower() or query in c["id"].lower() or query in c["name"].lower()
        ]
        print(f"  {len(matches)} result(s):\n")
        print(f"  {'ID':<30} {'Symbol':<12} {'Name'}")
        print("  " + "-" * 60)
        for c in matches[:100]:
            print(f"  {c['id']:<30} {c['symbol'].upper():<12} {c['name']}")
        if len(matches) > 100:
            print(f"  ... and {len(matches) - 100} more. Narrow your query.")
        print()
        print("  Add the ID to the COINS dict at the top of this script.")
        return

    coin_ids = list(COINS.values())
    symbol_by_id = {v: k for k, v in COINS.items()}

    print(f"  Fetching market data for {len(coin_ids)} coins from CoinGecko...")
    print()

    market_data = fetch_markets(coin_ids)

    # Index by id
    by_id = {item["id"]: item for item in market_data}

    # Print table
    print(f"  {'Symbol':<12} {'Price (USD)':>16} {'24h Change':>12} {'24h High':>16} {'24h Low':>16} {'24h Volume (USD)':>20}")
    print("  " + "-" * 96)

    results = []
    for coin_id in coin_ids:
        symbol = symbol_by_id[coin_id]
        item = by_id.get(coin_id)
        if item is None:
            print(f"  {symbol:<12} {'NOT FOUND':>16}")
            results.append({"symbol": symbol, "coin_id": coin_id, "error": "not found"})
            continue

        price        = item.get("current_price")
        change_pct   = item.get("price_change_percentage_24h")
        change_usd   = item.get("price_change_24h")
        high_24h     = item.get("high_24h")
        low_24h      = item.get("low_24h")
        volume       = item.get("total_volume")

        change_str = fmt_change(change_pct)
        vol_str = f"{volume:,.0f}" if volume else "N/A"

        print(
            f"  {symbol:<12} {fmt_price(price):>16} {change_str:>12} "
            f"{fmt_price(high_24h):>16} {fmt_price(low_24h):>16} {vol_str:>20}"
        )

        results.append({
            "symbol": symbol,
            "coin_id": coin_id,
            "price_usd": price,
            "change_24h_pct": change_pct,
            "change_24h_usd": change_usd,
            "high_24h": high_24h,
            "low_24h": low_24h,
            "volume_24h_usd": volume,
            "last_updated": item.get("last_updated"),
        })

    # Export to JSON
    print()
    out_file = "coingecko_prices.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Raw data -> {out_file}")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
