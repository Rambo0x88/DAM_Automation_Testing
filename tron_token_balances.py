"""
tron_token_balances.py — Fetch all token balances for a TRON wallet address.

Data sources:
  - TronGrid API   : TRX balance + TRC10 + TRC20 token balances (official TRON API, free)
  - Tronscan API   : Token symbol / decimals for unknown TRC20 contracts (free, no key)
  - CoinGecko API  : Current price + 24h change % for known tokens (no key required)

Usage:
    python tron_token_balances.py
    python tron_token_balances.py --address <TRON_ADDRESS>
    python tron_token_balances.py --address <ADDR> --json
    python tron_token_balances.py --address <ADDR> --trongrid-key <API_KEY>
    python tron_token_balances.py --address <ADDR> --no-price
    python tron_token_balances.py --address <ADDR> --min-value 1.0
"""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ─── Config ──────────────────────────────────────────────────────────────────

TRONGRID_BASE   = "https://api.trongrid.io"
TRONSCAN_BASE   = "https://apilist.tronscan.org"
COINGECKO_BASE  = "https://api.coingecko.com/api/v3"
DEFAULT_ADDRESS = "TWd4WrZ9wn84f5x1hZhL4DHvk738ns5jwb"

# ─── Known TRC20 contract → (symbol, decimals) ───────────────────────────────
# Covers the most common TRON-ecosystem tokens; unknown contracts are fetched live.
KNOWN_TRC20: dict[str, tuple[str, int]] = {
    "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t": ("USDT",   6),
    "TUpMhErZL2fhh4sVNULAbNKLokS4GjC1F4": ("TUSD",   18),
    "TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn": ("USDDOLD",18),
    "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8":  ("USDC",   6),
    "TMwFHYXLJaRUPeW6421aqXL4ZEzPRFGkGT": ("USDJ",   18),
    "TLBaRhANQoJFTqre9Nf1mjuwNWjCJeYqUL": ("USDD",   18),
    "TSSMHYeV2uE9qYH95DqyoCuNCzEL1NvU3S": ("SUN",    18),
    "TKkeiboTkxXKJpbmVFbv4a8ov5rAfRDMf9": ("SUNOLD", 18),
    "TXL6rJbvmjD46zeN1JssfgxvSo99qC8MRT": ("SUNDOG", 18),
    "TCFLL5dx5ZJdKnWuesXxi1VPwjLVmWZZy9": ("JST",    18),
    "TAFjULxiVgT4qWk6UZwjqwZXTSaGaqnVp4": ("BTT",    18),
    "TLa2f6VPqDgRE67v1736s7bJ8Ray5wYjU7": ("WIN",    6),
    "TFczxzPhnThNSqr5by8tvxsdCFRRz6cPNq": ("NFT",    0),
    "TUPM7K8REVzD2UdV4R5fe5M8XbnR2DdoJ6": ("HTX",    18),
    "TThzxNRLrW2Brp9DcTQU8i4Wd9udCWEdZ3": ("STUSDT", 18),
    "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9": ("BTC",    8),
    "THb4CqiFdwNHsWsQCs4JhzwjMWys4aqCbF": ("ETH",    18),
    "TRAq5NVtTAFwueRYDrmj1J4u2nGFvxbAMD": ("TINZ",   18),
    "TMacq4TDUw5q8NFBwmbY4RLXvzvG5JTkvi": ("PEPE",   18),
    "TXpw6aBgMJnm3sMPa49Hd3FpBZkWmFBpAR": ("BTST",   18),
    "TGBr8uh9jBVHJhhkwSJvQN2ZAKzVkxDmno": ("USDD",   18),
    "TVoF17RVnN2iMBGjnBqFdwGFGYxeUXirDU": ("JUSDT",  6),
}

# ─── CoinGecko token ID mapping ───────────────────────────────────────────────
# Maps token symbol → CoinGecko coin ID.
# NOTE: HTX on TRON is a community token priced at ~$0.0000017 and is NOT
# the same as Huobi Token (HT) on CoinGecko (~$0.095) — excluded intentionally.
COINGECKO_IDS: dict[str, str] = {
    "TRX":    "tron",
    "USDT":   "tether",
    "USDC":   "usd-coin",
    "TUSD":   "true-usd",
    "USDD":   "usdd",
    "USDDOLD":"usdd",       # old USDD contract — same price as USDD
    "USDJ":   "just-stablecoin",
    "BTT":    "bittorrent",
    "JST":    "just",
    "SUN":    "sun-token",
    "SUNOLD": "sun-token",  # old SUN contract — same price as SUN
    "SUNDOG": "sundog",
    "WIN":    "wink",
    "NFT":    "apenft",
    "STUSDT": "staked-usdt",
    "ETH":    "ethereum",
    "BTC":    "bitcoin",
    "PEPE":   "pepe",
}


# ─── TronGrid helpers ─────────────────────────────────────────────────────────

def _tg_headers(api_key: str | None) -> dict:
    h = {"Accept": "application/json"}
    if api_key:
        h["TRON-PRO-API-KEY"] = api_key
    return h


def fetch_account(address: str, api_key: str | None = None) -> dict:
    """Fetch account object containing TRX balance, TRC10 assetV2, and TRC20 list."""
    url = f"{TRONGRID_BASE}/v1/accounts/{address}"
    resp = requests.get(url, headers=_tg_headers(api_key), timeout=15)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data[0] if data else {}


# ─── Tronscan helpers ─────────────────────────────────────────────────────────

def _fetch_trc20_info_single(contract: str) -> tuple[str, int] | None:
    """Fetch (symbol, decimals) for one TRC20 contract from Tronscan."""
    try:
        resp = requests.get(
            f"{TRONSCAN_BASE}/api/token_trc20",
            params={"contract": contract},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        tokens = resp.json().get("trc20_tokens", [])
        if not tokens:
            return None
        t = tokens[0]
        return t.get("symbol", contract[:6]), int(t.get("decimals", 6))
    except Exception:
        return None


def fetch_trc20_infos(contracts: list[str], max_workers: int = 10) -> dict[str, tuple[str, int]]:
    """Fetch (symbol, decimals) for multiple unknown contracts in parallel."""
    result: dict[str, tuple[str, int]] = {}
    if not contracts:
        return result

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_trc20_info_single, c): c for c in contracts}
        for future in as_completed(futures):
            contract = futures[future]
            info = future.result()
            if info:
                result[contract] = info
    return result


# ─── CoinGecko helpers ───────────────────────────────────────────────────────

def fetch_coingecko_prices(symbols: list[str]) -> dict[str, dict]:
    """Return {SYMBOL: {price, change_24h_pct}} for all recognisable tokens.

    Multiple symbols can share the same CoinGecko ID (e.g. SUN / SUNOLD both
    map to "sun-token") — all of them receive the same price data.
    """
    # id → list of symbols that share it
    id_to_syms: dict[str, list[str]] = {}
    for sym in symbols:
        cg_id = COINGECKO_IDS.get(sym.upper())
        if cg_id:
            id_to_syms.setdefault(cg_id, []).append(sym.upper())

    if not id_to_syms:
        return {}

    resp = requests.get(
        f"{COINGECKO_BASE}/coins/markets",
        params={
            "vs_currency": "usd",
            "ids": ",".join(id_to_syms),
            "per_page": 250,
            "page": 1,
            "price_change_percentage": "24h",
        },
        timeout=15,
    )
    resp.raise_for_status()

    result: dict[str, dict] = {}
    for item in resp.json():
        price_data = {
            "price":          item.get("current_price"),
            "change_24h_pct": item.get("price_change_percentage_24h"),
        }
        for sym in id_to_syms.get(item["id"], []):
            result[sym] = price_data
    return result


# ─── Formatters ───────────────────────────────────────────────────────────────

def fmt_amount(v: float) -> str:
    if v == 0:
        return "0"
    if v >= 1_000_000_000:
        return f"{v:,.0f}"
    if v >= 1_000_000:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.6f}"
    return f"{v:.10f}"


def fmt_price(v) -> str:
    if v is None:
        return "—"
    if v >= 1_000:
        return f"${v:,.2f}"
    if v >= 1:
        return f"${v:,.4f}"
    if v >= 0.000_001:
        return f"${v:.8f}"
    return f"${v:.3e}"


def fmt_value(v) -> str:
    if v is None:
        return "—"
    if v >= 1_000_000:
        return f"${v:,.0f}"
    if v >= 1_000:
        return f"${v:,.2f}"
    if v >= 0.01:
        return f"${v:.4f}"
    if v > 0:
        return f"${v:.8f}"
    return "$0.00"


def fmt_change(v) -> str:
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tron Token Balance Fetcher")
    parser.add_argument(
        "--address", default=DEFAULT_ADDRESS,
        help=f"TRON wallet address (default: {DEFAULT_ADDRESS})",
    )
    parser.add_argument(
        "--trongrid-key", default=None, metavar="KEY",
        help="TronGrid Pro API key (optional — increases rate limits)",
    )
    parser.add_argument(
        "--no-price", action="store_true",
        help="Skip CoinGecko price fetch",
    )
    parser.add_argument(
        "--min-value", type=float, default=0.0, metavar="USD",
        help="Hide tokens with value below this threshold (default: 0 = show all)",
    )
    parser.add_argument(
        "--json", dest="export_json", action="store_true",
        help="Export full results to JSON file",
    )
    parser.add_argument(
        "--out", default="tron_balances.json",
        help="Output JSON filename (default: tron_balances.json)",
    )
    args = parser.parse_args()
    address = args.address

    print("=" * 95)
    print("  Tron Token Balance Fetcher")
    print("=" * 95)
    print(f"  Address   : {address}")
    print(f"  Min value : ${args.min_value:.2f}" if args.min_value > 0 else f"  Min value : (show all)")
    print()

    # ── 1. Fetch account ─────────────────────────────────────────────────────
    print("  [1/4] Fetching account from TronGrid...")
    account = fetch_account(address, args.trongrid_key)
    if not account:
        print(f"  ERROR: Address not found on TronGrid — check that the address is correct.")
        return

    raw_tokens: list[dict] = []

    # Native TRX
    trx_amount = account.get("balance", 0) / 1_000_000
    raw_tokens.append({
        "symbol": "TRX", "name": "TRON", "type": "Native",
        "contract": "native", "amount": trx_amount,
    })

    # TRC10
    for asset in account.get("assetV2", []):
        raw_tokens.append({
            "symbol": asset.get("key", ""), "name": asset.get("key", ""),
            "type": "TRC10", "contract": asset.get("key", ""),
            "amount": int(asset.get("value", 0)),
        })

    # TRC20 — gather contracts + raw balances
    trc20_raw: dict[str, int] = {}
    for entry in account.get("trc20", []):
        for contract, raw_bal in entry.items():
            trc20_raw[contract] = int(raw_bal)

    print(f"         TRX: 1 | TRC10: {len(account.get('assetV2', []))} | "
          f"TRC20: {len(trc20_raw)} contract(s) found")

    # ── 2. Resolve TRC20 symbols + decimals ─────────────────────────────────
    print("  [2/4] Resolving TRC20 token info...")
    known_contracts   = {c: KNOWN_TRC20[c] for c in trc20_raw if c in KNOWN_TRC20}
    unknown_contracts = [c for c in trc20_raw if c not in KNOWN_TRC20]

    print(f"         Known mapping: {len(known_contracts)} | "
          f"Fetching from Tronscan: {len(unknown_contracts)}")
    fetched = fetch_trc20_infos(unknown_contracts)
    trc20_info = {**known_contracts, **fetched}

    for contract, raw_bal in trc20_raw.items():
        info = trc20_info.get(contract)
        if info:
            symbol, decimals = info
        else:
            symbol   = contract[:8] + "…"
            decimals = 6  # safe fallback
        amount = raw_bal / (10 ** decimals)
        raw_tokens.append({
            "symbol": symbol, "name": symbol, "type": "TRC20",
            "contract": contract, "amount": amount,
        })

    # Filter zero-balance
    nonzero = [t for t in raw_tokens if t["amount"] > 0]
    print(f"         Non-zero balance: {len(nonzero)} token(s) "
          f"({len(raw_tokens) - len(nonzero)} zero hidden)")

    # ── 3. Prices from CoinGecko ─────────────────────────────────────────────
    prices: dict[str, dict] = {}
    if not args.no_price:
        print("  [3/4] Fetching prices from CoinGecko...")
        symbols = list({t["symbol"].upper() for t in nonzero})
        prices  = fetch_coingecko_prices(symbols)
        known_p   = [s for s in symbols if s in prices]
        unknown_p = [s for s in symbols if s not in prices]
        print(f"         Prices found: {len(known_p)} | "
              f"No CoinGecko match: {unknown_p if unknown_p else 'none'}")
    else:
        print("  [3/4] Price fetch skipped (--no-price)")

    # ── 4. Build + display results ───────────────────────────────────────────
    print("  [4/4] Building results table...")
    print()

    results = []
    total_value = 0.0

    for t in nonzero:
        sym = t["symbol"].upper()
        price_info = prices.get(sym, {})
        price  = price_info.get("price")
        change = price_info.get("change_24h_pct")
        value  = (t["amount"] * price) if price is not None else None
        if value:
            total_value += value
        results.append({
            "symbol":         t["symbol"],
            "name":           t["name"],
            "type":           t["type"],
            "contract":       t["contract"],
            "amount":         t["amount"],
            "price_usd":      price,
            "value_usd":      value,
            "change_24h_pct": change,
        })

    # Sort by value desc, unknowns at bottom
    results.sort(key=lambda r: r["value_usd"] or 0, reverse=True)

    # Apply min-value filter
    display = [r for r in results if (r["value_usd"] or 0) >= args.min_value]

    # Print table
    W = {"sym": 10, "type": 7, "amt": 28, "prc": 18, "val": 18, "chg": 10}
    divider = "  " + "─" * (sum(W.values()) + len(W) * 2)

    print(
        f"  {'Token':<{W['sym']}} {'Type':<{W['type']}} {'Amount':>{W['amt']}} "
        f"{'Price (USD)':>{W['prc']}} {'Value (USD)':>{W['val']}} {'24h %':>{W['chg']}}"
    )
    print(divider)

    for r in display:
        print(
            f"  {r['symbol']:<{W['sym']}} {r['type']:<{W['type']}} "
            f"{fmt_amount(r['amount']):>{W['amt']}} "
            f"{fmt_price(r['price_usd']):>{W['prc']}} "
            f"{fmt_value(r['value_usd']):>{W['val']}} "
            f"{fmt_change(r['change_24h_pct']):>{W['chg']}}"
        )

    print(divider)
    pad = W["sym"] + W["type"] + W["amt"] + W["prc"] + 6
    print(f"  {'TOTAL VALUE (with known price)':<{pad}} {fmt_value(total_value):>{W['val']}}")
    if len(display) < len(results):
        print(f"  ({len(results) - len(display)} token(s) hidden by --min-value ${args.min_value:.2f})")
    print()

    # ── JSON export ──────────────────────────────────────────────────────────
    if args.export_json:
        output = {
            "address":         address,
            "fetched_at":      time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_value_usd": total_value,
            "token_count":     len(results),
            "tokens":          results,
        }
        with open(args.out, "w") as f:
            json.dump(output, f, indent=2)
        print(f"  Exported → {args.out}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
