"""
Mock API Server — Matrixport + CoinGecko emulator for offline/CI testing.

Runs a single HTTP server on localhost that handles both APIs by path prefix.

Matrixport paths  (/trader/v2/api/*, /mapi/v1/*, /flexible/api/v2/*):
  GET /trader/v2/api/symbols-info
  GET /trader/v2/api/rfq-price?symbol=BTCUSDT&qty=0.0001&side=1
  GET /mapi/v1/wallet/balance
  GET /flexible/api/v2/user/asset/summary

CoinGecko paths   (/api/v3/*):
  GET /api/v3/coins/markets?ids=bitcoin,ethereum,...&vs_currency=usd
  GET /api/v3/coins/list

Usage:
    python3 mock_server.py                  # port 8765, price jitter enabled
    python3 mock_server.py --port 9000
    python3 mock_server.py --no-jitter      # fixed prices for deterministic tests
    python3 mock_server.py --seed 42        # fixed seed for reproducible jitter

Connecting your scripts (no code changes needed, just set env vars):
    export MATRIXPORT_BASE_URL=http://localhost:8765
    export COINGECKO_BASE_URL=http://localhost:8765/api/v3
    python3 matrixport_price.py
    python3 coingecko_price.py
    python3 bit_breakdown_table_check.py --portfolio-id <ID>
"""

import argparse
import json
import random
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# ── Base prices and 24h changes ───────────────────────────────────────────────

_PRICES: dict[str, float] = {
    "BTCUSDT":    65279.00,
    "ETHUSDT":    1776.80,
    "BNBUSDT":    588.00,
    "SOLUSDT":    152.30,
    "XRPUSDT":    0.5210,
    "DOGEUSDT":   0.1145,
    "AVAXUSDT":   22.45,
    "DOTUSDT":    5.48,
    "LINKUSDT":   13.42,
    "LTCUSDT":    78.30,
    "TRXUSDT":    0.318431,
    "USDCUSDT":   0.99980,
    "USDTUSDT":   1.00000,
    "UNIUSDT":    8.23,
    "PEPEUSDT":   2.94e-06,
    "SHIBUSDT":   0.0000155,
    "AAVEUSDT":   185.20,
    "1INCHUSDT":  0.3120,
    "APEUSDT":    1.025,
    "ARBUSDT":    0.5820,
    "AXSUSDT":    3.45,
    "BATUSDT":    0.2150,
    "BCHUSDT":    408.00,
    "BONKUSDT":   0.0000212,
    "CAKEUSDT":   2.145,
    "CHZUSDT":    0.0782,
    "COMPUSDT":   48.30,
    "CRVUSDT":    0.3820,
    "DCRUSDT":    14.20,
    "EIGENUSDT":  2.35,
    "ENSUSDT":    18.40,
    "ETCUSDT":    22.80,
    "FETUSDT":    1.235,
    "FLOKIUSDT":  0.0000875,
    "FTTUSDT":    1.25,
    "GALAUSDT":   0.02250,
    "GMXUSDT":    18.70,
    "GRTUSDT":    0.1450,
    "NEARUSDT":   3.825,
    "OPUSDT":     0.9230,
    "ORDIUSDT":   4.20,
    "PEOPLEUSDT": 0.04820,
    "POLUSDT":    0.3120,
    "PYTHUSDT":   0.3450,
    "RENDERUSDT": 3.820,
    "SANDUSDT":   0.3210,
    "SUSHIUSDT":  0.8950,
    "TONUSDT":    3.245,
    "WLDUSDT":    1.245,
    "XECUSDT":    0.0000285,
    "XLMUSDT":    0.2820,
    "ZECUSDT":    32.50,
}

_CHANGE_24H: dict[str, float] = {
    "BTCUSDT":    -1.700, "ETHUSDT":    -0.008, "BNBUSDT":     0.450,
    "SOLUSDT":     1.230, "XRPUSDT":    -0.520, "DOGEUSDT":    2.150,
    "AVAXUSDT":   -0.830, "DOTUSDT":    -1.250, "LINKUSDT":    0.650,
    "LTCUSDT":    -0.320, "TRXUSDT":     0.238, "USDCUSDT":    0.006,
    "USDTUSDT":   -0.036, "UNIUSDT":     1.450, "PEPEUSDT":   -0.814,
    "SHIBUSDT":    1.250, "AAVEUSDT":    2.300, "1INCHUSDT":  -1.100,
    "APEUSDT":     0.750, "ARBUSDT":    -0.620, "AXSUSDT":    -2.100,
    "BATUSDT":     0.380, "BCHUSDT":    -0.920, "BONKUSDT":    3.450,
    "CAKEUSDT":    1.100, "CHZUSDT":    -0.450, "COMPUSDT":    1.820,
    "CRVUSDT":    -1.350, "DCRUSDT":     0.220, "EIGENUSDT":  -2.500,
    "ENSUSDT":     1.650, "ETCUSDT":    -0.780, "FETUSDT":     3.200,
    "FLOKIUSDT":   4.100, "FTTUSDT":    -0.550, "GALAUSDT":    2.750,
    "GMXUSDT":    -1.800, "GRTUSDT":     0.920, "NEARUSDT":    1.350,
    "OPUSDT":     -0.680, "ORDIUSDT":   -3.200, "PEOPLEUSDT":  5.400,
    "POLUSDT":    -0.920, "PYTHUSDT":    2.100, "RENDERUSDT":  1.750,
    "SANDUSDT":   -1.100, "SUSHIUSDT":   0.650, "TONUSDT":    -0.420,
    "WLDUSDT":    -2.800, "XECUSDT":     0.380, "XLMUSDT":    -0.750,
    "ZECUSDT":     1.200,
}

# ── CoinGecko data ────────────────────────────────────────────────────────────

_CG_ID_TO_SYM: dict[str, str] = {
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT", "ripple": "XRPUSDT", "dogecoin": "DOGEUSDT",
    "avalanche-2": "AVAXUSDT", "polkadot": "DOTUSDT", "chainlink": "LINKUSDT",
    "litecoin": "LTCUSDT", "tron": "TRXUSDT", "usd-coin": "USDCUSDT",
    "tether": "USDTUSDT", "uniswap": "UNIUSDT", "pepe": "PEPEUSDT",
    "shiba-inu": "SHIBUSDT", "aave": "AAVEUSDT", "1inch": "1INCHUSDT",
    "apecoin": "APEUSDT", "arbitrum": "ARBUSDT", "axie-infinity": "AXSUSDT",
    "basic-attention-token": "BATUSDT", "bitcoin-cash": "BCHUSDT", "bonk": "BONKUSDT",
    "pancakeswap-token": "CAKEUSDT", "chiliz": "CHZUSDT",
    "compound-governance-token": "COMPUSDT", "curve-dao-token": "CRVUSDT",
    "decred": "DCRUSDT", "eigenlayer": "EIGENUSDT",
    "ethereum-name-service": "ENSUSDT", "ethereum-classic": "ETCUSDT",
    "fetch-ai": "FETUSDT", "floki": "FLOKIUSDT", "ftx-token": "FTTUSDT",
    "gala": "GALAUSDT", "gmx": "GMXUSDT", "the-graph": "GRTUSDT",
    "near": "NEARUSDT", "optimism": "OPUSDT", "ordinals": "ORDIUSDT",
    "constitutiondao": "PEOPLEUSDT", "polygon-ecosystem-token": "POLUSDT",
    "pyth-network": "PYTHUSDT", "render-token": "RENDERUSDT",
    "the-sandbox": "SANDUSDT", "sushi": "SUSHIUSDT",
    "the-open-network": "TONUSDT", "worldcoin-wld": "WLDUSDT",
    "ecash": "XECUSDT", "stellar": "XLMUSDT", "zcash": "ZECUSDT",
}

_CG_COIN_LIST: list[dict] = [
    {"id": "bitcoin",                   "symbol": "btc",    "name": "Bitcoin"},
    {"id": "ethereum",                  "symbol": "eth",    "name": "Ethereum"},
    {"id": "binancecoin",               "symbol": "bnb",    "name": "BNB"},
    {"id": "solana",                    "symbol": "sol",    "name": "Solana"},
    {"id": "ripple",                    "symbol": "xrp",    "name": "XRP"},
    {"id": "dogecoin",                  "symbol": "doge",   "name": "Dogecoin"},
    {"id": "avalanche-2",               "symbol": "avax",   "name": "Avalanche"},
    {"id": "polkadot",                  "symbol": "dot",    "name": "Polkadot"},
    {"id": "chainlink",                 "symbol": "link",   "name": "Chainlink"},
    {"id": "litecoin",                  "symbol": "ltc",    "name": "Litecoin"},
    {"id": "tron",                      "symbol": "trx",    "name": "TRON"},
    {"id": "usd-coin",                  "symbol": "usdc",   "name": "USD Coin"},
    {"id": "tether",                    "symbol": "usdt",   "name": "Tether"},
    {"id": "uniswap",                   "symbol": "uni",    "name": "Uniswap"},
    {"id": "pepe",                      "symbol": "pepe",   "name": "Pepe"},
    {"id": "shiba-inu",                 "symbol": "shib",   "name": "Shiba Inu"},
    {"id": "aave",                      "symbol": "aave",   "name": "Aave"},
    {"id": "1inch",                     "symbol": "1inch",  "name": "1inch"},
    {"id": "apecoin",                   "symbol": "ape",    "name": "ApeCoin"},
    {"id": "arbitrum",                  "symbol": "arb",    "name": "Arbitrum"},
    {"id": "axie-infinity",             "symbol": "axs",    "name": "Axie Infinity"},
    {"id": "basic-attention-token",     "symbol": "bat",    "name": "Basic Attention Token"},
    {"id": "bitcoin-cash",              "symbol": "bch",    "name": "Bitcoin Cash"},
    {"id": "bonk",                      "symbol": "bonk",   "name": "Bonk"},
    {"id": "pancakeswap-token",         "symbol": "cake",   "name": "PancakeSwap"},
    {"id": "chiliz",                    "symbol": "chz",    "name": "Chiliz"},
    {"id": "compound-governance-token", "symbol": "comp",   "name": "Compound"},
    {"id": "curve-dao-token",           "symbol": "crv",    "name": "Curve DAO Token"},
    {"id": "decred",                    "symbol": "dcr",    "name": "Decred"},
    {"id": "eigenlayer",                "symbol": "eigen",  "name": "EigenLayer"},
    {"id": "ethereum-name-service",     "symbol": "ens",    "name": "Ethereum Name Service"},
    {"id": "ethereum-classic",          "symbol": "etc",    "name": "Ethereum Classic"},
    {"id": "fetch-ai",                  "symbol": "fet",    "name": "Fetch.ai"},
    {"id": "floki",                     "symbol": "floki",  "name": "FLOKI"},
    {"id": "ftx-token",                 "symbol": "ftt",    "name": "FTX Token"},
    {"id": "gala",                      "symbol": "gala",   "name": "GALA"},
    {"id": "gmx",                       "symbol": "gmx",    "name": "GMX"},
    {"id": "the-graph",                 "symbol": "grt",    "name": "The Graph"},
    {"id": "near",                      "symbol": "near",   "name": "NEAR Protocol"},
    {"id": "optimism",                  "symbol": "op",     "name": "Optimism"},
    {"id": "ordinals",                  "symbol": "ordi",   "name": "ORDI"},
    {"id": "constitutiondao",           "symbol": "people", "name": "ConstitutionDAO"},
    {"id": "polygon-ecosystem-token",   "symbol": "pol",    "name": "POL (ex-MATIC)"},
    {"id": "pyth-network",              "symbol": "pyth",   "name": "Pyth Network"},
    {"id": "render-token",              "symbol": "render", "name": "Render"},
    {"id": "the-sandbox",               "symbol": "sand",   "name": "The Sandbox"},
    {"id": "sushi",                     "symbol": "sushi",  "name": "Sushi"},
    {"id": "the-open-network",          "symbol": "ton",    "name": "Toncoin"},
    {"id": "worldcoin-wld",             "symbol": "wld",    "name": "Worldcoin"},
    {"id": "ecash",                     "symbol": "xec",    "name": "eCash"},
    {"id": "stellar",                   "symbol": "xlm",    "name": "Stellar"},
    {"id": "zcash",                     "symbol": "zec",    "name": "Zcash"},
]

# ── Helper functions (must be defined before _SYMBOLS_INFO) ───────────────────

def _min_qty(sym: str) -> str:
    table = {
        "BTCUSDT": "0.0001", "ETHUSDT": "0.01",  "BNBUSDT": "0.1",
        "SOLUSDT": "0.1",    "XRPUSDT": "20",    "DOGEUSDT": "200",
        "AVAXUSDT": "0.5",   "DOTUSDT": "10",    "LINKUSDT": "10",
        "LTCUSDT": "0.1",    "TRXUSDT": "300",   "USDCUSDT": "20",
    }
    return table.get(sym, "1")


def _max_qty(sym: str) -> str:
    table = {
        "BTCUSDT": "10", "ETHUSDT": "100", "BNBUSDT": "500",
        "SOLUSDT": "500", "XRPUSDT": "50000", "TRXUSDT": "1000000",
        "USDCUSDT": "500000",
    }
    return table.get(sym, "10000")


def _jitter(price: float, pct: float = 0.005) -> float:
    if _NO_JITTER:
        return price
    return price * (1.0 + random.uniform(-pct, pct))


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())


def _send_json(handler, data, status: int = 200) -> None:
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# ── Static data built after helpers ──────────────────────────────────────────

_SYMBOLS_INFO: list[dict] = [
    {
        "pair": sym,
        "base_currency": sym.replace("USDT", ""),
        "quote_currency": "USDT",
        "base_min_amount": _min_qty(sym),
        "base_max_amount": _max_qty(sym),
    }
    for sym in _PRICES
    if sym.endswith("USDT") and sym != "USDTUSDT"
]

_WALLET_BALANCES: list[dict] = [
    {"currency": "USDT", "available_balance": "800000001.000000"},
    {"currency": "USDC", "available_balance": "500000.000000"},
    {"currency": "TRX",  "available_balance": "411294412.473223"},
]

_BALANCE_PLUS: list[dict] = [
    {"currency": "USDT", "available_balance": "50000.000000"},
    {"currency": "USDC", "available_balance": "0.000000"},
    {"currency": "TRX",  "available_balance": "0.000000"},
]

_CG_ID_BY_ID = {c["id"]: c for c in _CG_COIN_LIST}

# ── Request handler ───────────────────────────────────────────────────────────

class MockAPIHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # noqa: N802
        print(f"  [{time.strftime('%H:%M:%S')}] {self.path}  →  {args[1]}")

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query, keep_blank_values=True)

        if path.startswith("/api/v3/"):
            self._handle_coingecko(path, qs)
        else:
            self._handle_matrixport(path, qs)

    # ── Matrixport ────────────────────────────────────────────────────────────

    def _handle_matrixport(self, path: str, qs: dict) -> None:
        if path == "/trader/v2/api/symbols-info":
            _send_json(self, {"code": 0, "message": "OK", "data": _SYMBOLS_INFO})

        elif path == "/trader/v2/api/rfq-price":
            symbol = (qs.get("symbol") or [""])[0].upper()
            qty    = (qs.get("qty")    or ["1"])[0]
            side   = (qs.get("side")   or ["1"])[0]
            base   = _PRICES.get(symbol)
            if base is None:
                _send_json(self, {"code": 400, "message": f"Symbol not supported: {symbol}"}, 400)
                return
            price = _jitter(base)
            _send_json(self, {
                "code": 0, "message": "OK",
                "data": {
                    "symbol": symbol, "side": side, "qty": qty,
                    "price": f"{price:.10g}",
                    "cash":  f"{float(qty) * price:.6f}",
                    "price_id": f"mock-{uuid.uuid4().hex[:12]}",
                },
            })

        elif path == "/mapi/v1/wallet/balance":
            _send_json(self, {"code": 0, "message": "OK", "data": _WALLET_BALANCES})

        elif path == "/flexible/api/v2/user/asset/summary":
            _send_json(self, {
                "code": 0, "message": "OK",
                "data": {"currencies": _BALANCE_PLUS},
            })

        else:
            _send_json(self, {"code": 404, "message": f"Unknown path: {path}"}, 404)

    # ── CoinGecko ─────────────────────────────────────────────────────────────

    def _handle_coingecko(self, path: str, qs: dict) -> None:
        sub = path[len("/api/v3"):]

        if sub == "/coins/markets":
            ids_raw   = (qs.get("ids") or [""])[0]
            requested = {cid.strip() for cid in ids_raw.split(",") if cid.strip()}
            results   = []
            for cg_id, sym in _CG_ID_TO_SYM.items():
                if requested and cg_id not in requested:
                    continue
                base     = _PRICES.get(sym, 0.0)
                price    = _jitter(base)
                chg_pct  = _CHANGE_24H.get(sym, 0.0)
                chg_usd  = price * chg_pct / 100
                meta     = _CG_ID_BY_ID.get(cg_id, {"symbol": cg_id, "name": cg_id})
                results.append({
                    "id":                          cg_id,
                    "symbol":                      meta["symbol"],
                    "name":                        meta["name"],
                    "current_price":               price,
                    "price_change_24h":            chg_usd,
                    "price_change_percentage_24h": chg_pct,
                    "high_24h":                    price * 1.015,
                    "low_24h":                     price * 0.985,
                    "total_volume":                price * random.uniform(5e6, 5e8),
                    "market_cap":                  price * random.uniform(1e8, 1e12),
                    "last_updated":                _now_iso(),
                })
            _send_json(self, results)

        elif sub == "/coins/list":
            _send_json(self, _CG_COIN_LIST)

        else:
            _send_json(self, {"error": f"Unknown CoinGecko path: {path}"}, 404)


# ── Entry point ───────────────────────────────────────────────────────────────

_NO_JITTER = False


def main() -> None:
    global _NO_JITTER

    parser = argparse.ArgumentParser(description="Mock API server — Matrixport + CoinGecko")
    parser.add_argument("--port",      type=int, default=8765,       help="Port (default: 8765)")
    parser.add_argument("--host",      default="127.0.0.1",          help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--no-jitter", action="store_true",           help="Fixed prices — no random variation")
    parser.add_argument("--seed",      type=int, default=None,        help="Random seed for reproducible jitter")
    args = parser.parse_args()

    _NO_JITTER = args.no_jitter
    if args.seed is not None:
        random.seed(args.seed)

    server = HTTPServer((args.host, args.port), MockAPIHandler)

    print("=" * 60)
    print("  Mock API Server  —  Matrixport + CoinGecko")
    print("=" * 60)
    print(f"  Listening  : http://{args.host}:{args.port}")
    print(f"  Jitter     : {'off (--no-jitter)' if _NO_JITTER else 'on  (±0.5% per request)'}")
    print(f"  Seed       : {args.seed if args.seed is not None else 'random'}")
    print()
    print("  Env vars to redirect your scripts:")
    print(f"    export MATRIXPORT_BASE_URL=http://{args.host}:{args.port}")
    print(f"    export COINGECKO_BASE_URL=http://{args.host}:{args.port}/api/v3")
    print()
    print("  Endpoints:")
    print("    GET /trader/v2/api/symbols-info")
    print("    GET /trader/v2/api/rfq-price?symbol=BTCUSDT&qty=0.0001&side=1")
    print("    GET /mapi/v1/wallet/balance")
    print("    GET /flexible/api/v2/user/asset/summary")
    print("    GET /api/v3/coins/markets?ids=bitcoin,tron&vs_currency=usd")
    print("    GET /api/v3/coins/list")
    print()
    print("  Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
