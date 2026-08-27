# config/universe_builder.py
"""Build tradeable universe: market cap >= floor, EXCLUDING Chinese filers
(mainland China + Hong Kong). Early-stops once below the size threshold."""

import os, time, json, requests
import yfinance as yf

HEADERS = {"User-Agent": "Stock Screener rcjmvzzsbg@example.com"}
MARKET_CAP_FLOOR = 10_000_000_000          # $10B
CACHE_FILE = "config/universe_cache.json"
CHINA_CODES = {"F4", "K3"}                  # EDGAR: F4=China, K3=Hong Kong


def fetch_sec_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
    return [{"ticker": row["ticker"].upper(),
             "cik": str(row["cik_str"]).zfill(10),
             "name": row["title"]} for row in r.json().values()]


def get_market_cap(ticker):
    try:
        fi = yf.Ticker(ticker).fast_info
        for key in ("market_cap", "marketCap"):
            try:
                mc = fi[key]
                if mc: return float(mc)
            except Exception: pass
        for attr in ("market_cap", "marketCap"):
            mc = getattr(fi, attr, None)
            if mc: return float(mc)
    except Exception:
        return None
    return None


# Known Chinese ADRs that use offshore (Cayman/BVI) shells -> country codes miss them
CHINA_BLOCKLIST = {
    "BABA","CYATY","PDD","JD","BIDU","NIO","LI","XPEV","BILI","TCOM",
    "NTES","TME","YUMC","BEKE","ZTO","HTHT","VIPS","IQ","WB","FUTU",
    "TIGR","LU","DIDIY","KC","GDS","ATHM","EDU","TAL","YMM","ZH","LKNCY","LI","ZK","TAL","BZ","DOYU","QFIN","FINV","LKNCY","LI","ZK","TAL","BZ","DOYU","QFIN","FINV",
}

def is_chinese(cik, ticker=""):
    """True if China/HK by ticker blocklist OR any SEC country field = F4/K3."""
    if ticker.upper() in CHINA_BLOCKLIST:
        return True
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        r = requests.get(url, headers=HEADERS, timeout=20); r.raise_for_status()
        j = r.json()
        fields = [j.get("stateOfIncorporation", "")]
        for kind in ("business", "mailing"):
            a = j.get("addresses", {}).get(kind, {}) or {}
            fields.append(a.get("stateOrCountry", ""))
        return any((f or "").upper() in CHINA_CODES for f in fields)
    except Exception:
        return False


def build_universe(floor=MARKET_CAP_FLOOR, limit=None, sleep=0.15,
                   stop_after_misses=300):
    candidates = fetch_sec_tickers()
    if limit: candidates = candidates[:limit]
    print(f"Screening {len(candidates):,} tickers >= ${floor/1e9:.0f}B (excluding Chinese)...\n")
    kept, misses = [], 0
    for i, c in enumerate(candidates, 1):
        mc = get_market_cap(c["ticker"])
        if mc and mc >= floor:
            misses = 0
            if is_chinese(c["cik"], c["ticker"]):
                print(f"  [{i:>5}] ✗ {c['ticker']:<6} ${mc/1e9:>7.1f}B  (Chinese - skipped)")
                time.sleep(sleep); continue
            c["market_cap"] = mc
            kept.append(c)
            print(f"  [{i:>5}] ✓ {c['ticker']:<6} ${mc/1e9:>7.1f}B  {c['name'][:38]}")
        else:
            misses += 1
        if stop_after_misses and misses >= stop_after_misses:
            print(f"\n⏹  {stop_after_misses} consecutive sub-${floor/1e9:.0f}B names — stopping at #{i}.")
            break
        if i % 250 == 0:
            print(f"  ... scanned {i:,}, kept {len(kept)}")
        time.sleep(sleep)
    kept.sort(key=lambda x: x["market_cap"], reverse=True)
    with open(CACHE_FILE, "w") as f: json.dump(kept, f, indent=2)
    print(f"\n✅ Universe: {len(kept)} companies >= ${floor/1e9:.0f}B (Chinese excluded)")
    return kept


def load_universe():
    if not os.path.exists(CACHE_FILE): return []
    with open(CACHE_FILE) as f: return json.load(f)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    build_universe(limit=lim)
