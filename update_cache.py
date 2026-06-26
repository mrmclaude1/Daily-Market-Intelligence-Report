#!/usr/bin/env python3
"""
update_cache.py — Merge today's report values into report_cache.json
Usage: python3 update_cache.py --date 2026-06-26 --btc-price 59432 ...
Writes updated cache to /tmp/report_cache_updated.json
"""

import argparse
import json
import sys
from pathlib import Path

CACHE_IN  = Path("/tmp/report_cache.json")
CACHE_OUT = Path("/tmp/report_cache_updated.json")
TEMPLATE  = Path("/home/user/market-report-cache/report_cache.json")

def load_existing():
    if CACHE_IN.exists():
        try:
            return json.loads(CACHE_IN.read_text())
        except Exception:
            pass
    if TEMPLATE.exists():
        try:
            return json.loads(TEMPLATE.read_text())
        except Exception:
            pass
    return {}

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--date",                     default=None)
    # Prices
    p.add_argument("--btc-price",    type=float, default=None)
    p.add_argument("--btc-chg",      type=float, default=None, help="24h % change")
    p.add_argument("--eth-price",    type=float, default=None)
    p.add_argument("--eth-chg",      type=float, default=None)
    p.add_argument("--xrp-price",    type=float, default=None)
    p.add_argument("--xrp-chg",      type=float, default=None)
    p.add_argument("--btc-high",     type=float, default=None)
    p.add_argument("--btc-low",      type=float, default=None)
    p.add_argument("--eth-high",     type=float, default=None)
    p.add_argument("--xrp-high",     type=float, default=None)
    # Macro
    p.add_argument("--fed-upper",    type=float, default=None)
    p.add_argument("--fed-lower",    type=float, default=None)
    p.add_argument("--pce-2026",     type=float, default=None)
    p.add_argument("--cpi-yoy",      type=float, default=None)
    p.add_argument("--prime-rate",   type=float, default=None)
    p.add_argument("--hike-on-table",            default=None, choices=["true","false"])
    p.add_argument("--cuts-2026",    type=int,   default=None)
    p.add_argument("--iran-war",                 default=None, choices=["true","false"])
    p.add_argument("--iran-ceasefire",           default=None, choices=["true","false"])
    p.add_argument("--oil-trend",                default=None)
    # Markets
    p.add_argument("--sp500",        type=float, default=None)
    p.add_argument("--sp500-chg",    type=float, default=None)
    p.add_argument("--nasdaq",       type=float, default=None)
    p.add_argument("--nasdaq-chg",   type=float, default=None)
    p.add_argument("--nasdaq-down-days", type=int, default=None)
    p.add_argument("--vix",          type=float, default=None)
    p.add_argument("--market-posture",           default=None)
    # Real estate
    p.add_argument("--mortgage-30yr",  type=float, default=None)
    p.add_argument("--inventory-yoy",  type=float, default=None)
    p.add_argument("--listing-px-yoy", type=float, default=None)
    # Crypto ETF
    p.add_argument("--btc-etf-weekly", type=float, default=None)
    p.add_argument("--btc-etf-4wk",   type=float, default=None)
    p.add_argument("--eth-etf-weekly", type=float, default=None)
    # Regulation
    p.add_argument("--clarity-odds",   type=float, default=None)
    p.add_argument("--clarity-peak",   type=float, default=None)
    p.add_argument("--xrp-etf-approved",         default=None, choices=["true","false"])
    # Signals (comma-separated strings)
    p.add_argument("--top-signals",              default=None)
    p.add_argument("--elevated-risks",           default=None)
    # Watchlist
    p.add_argument("--btc-200wk-ma",   type=float, default=None)
    p.add_argument("--btc-200wk-status",         default=None)
    p.add_argument("--xrp-support",   type=float, default=None)
    p.add_argument("--xrp-downside",  type=float, default=None)
    p.add_argument("--ascendex-warn",            default=None, choices=["true","false"])
    # Sector scores 1-10
    p.add_argument("--score-crypto",   type=float, default=None)
    p.add_argument("--score-macro",    type=float, default=None)
    p.add_argument("--score-markets",  type=float, default=None)
    p.add_argument("--score-ai",       type=float, default=None)
    p.add_argument("--score-defense",  type=float, default=None)
    p.add_argument("--score-realestate", type=float, default=None)
    p.add_argument("--score-bizacq",   type=float, default=None)
    # Congressional
    p.add_argument("--congress-month",           default=None)
    p.add_argument("--congress-sectors",         default=None)
    p.add_argument("--congress-tickers",         default=None)
    return p.parse_args()

def tf(val):
    """Convert 'true'/'false' string to bool."""
    if val is None: return None
    return val.lower() == "true"

def csv(val):
    """Convert comma-separated string to list."""
    if val is None: return None
    return [x.strip() for x in val.split(",") if x.strip()]

def merge(cache, key_path, value):
    """Set cache[k1][k2] = value if value is not None."""
    if value is None:
        return
    keys = key_path.split(".")
    node = cache
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = value

def main():
    args = parse_args()
    cache = load_existing()

    # Meta
    if args.date:
        cache.setdefault("meta", {})["last_report_date"] = args.date
        cache["meta"]["report_count"] = cache.get("meta", {}).get("report_count", 0) + 1

    # Prices
    merge(cache, "prices.btc_usd",          args.btc_price)
    merge(cache, "prices.btc_change_24h_pct", args.btc_chg)
    merge(cache, "prices.eth_usd",          args.eth_price)
    merge(cache, "prices.eth_change_24h_pct", args.eth_chg)
    merge(cache, "prices.xrp_usd",          args.xrp_price)
    merge(cache, "prices.xrp_change_24h_pct", args.xrp_chg)
    merge(cache, "prices.btc_24h_high",     args.btc_high)
    merge(cache, "prices.btc_24h_low",      args.btc_low)
    merge(cache, "prices.eth_24h_high",     args.eth_high)
    merge(cache, "prices.xrp_24h_high",     args.xrp_high)

    # Macro
    merge(cache, "macro.fed_funds_rate_upper",   args.fed_upper)
    merge(cache, "macro.fed_funds_rate_lower",   args.fed_lower)
    merge(cache, "macro.pce_inflation_2026_pct", args.pce_2026)
    merge(cache, "macro.may_cpi_yoy_pct",        args.cpi_yoy)
    merge(cache, "macro.prime_rate",             args.prime_rate)
    merge(cache, "macro.rate_hike_on_table",     tf(args.hike_on_table))
    merge(cache, "macro.cuts_projected_2026",    args.cuts_2026)
    merge(cache, "macro.iran_war_active",        tf(args.iran_war))
    merge(cache, "macro.iran_ceasefire_confirmed", tf(args.iran_ceasefire))
    merge(cache, "macro.oil_trend",              args.oil_trend)

    # Markets
    merge(cache, "markets.sp500_level",              args.sp500)
    merge(cache, "markets.sp500_change_24h_pct",     args.sp500_chg)
    merge(cache, "markets.nasdaq_level",             args.nasdaq)
    merge(cache, "markets.nasdaq_change_24h_pct",    args.nasdaq_chg)
    merge(cache, "markets.nasdaq_consecutive_down_days", args.nasdaq_down_days)
    merge(cache, "markets.vix",                      args.vix)
    merge(cache, "markets.market_posture",           args.market_posture)

    # Real estate
    merge(cache, "real_estate.mortgage_30yr_fixed_pct", args.mortgage_30yr)
    merge(cache, "real_estate.housing_inventory_yoy_pct", args.inventory_yoy)
    merge(cache, "real_estate.listing_price_yoy_pct",    args.listing_px_yoy)

    # ETF flows
    merge(cache, "crypto_etf.btc_spot_etf_weekly_flow_bn",   args.btc_etf_weekly)
    merge(cache, "crypto_etf.btc_spot_etf_total_outflow_4wk_bn", args.btc_etf_4wk)
    merge(cache, "crypto_etf.eth_etf_weekly_flow_bn",         args.eth_etf_weekly)

    # Regulation
    merge(cache, "regulation.clarity_act_polymarket_odds_pct", args.clarity_odds)
    merge(cache, "regulation.clarity_act_prior_peak_odds_pct", args.clarity_peak)
    merge(cache, "regulation.xrp_etf_approved",               tf(args.xrp_etf_approved))

    # Signals
    if args.top_signals:
        cache["top_signals"] = csv(args.top_signals)
    if args.elevated_risks:
        cache["elevated_risks"] = csv(args.elevated_risks)

    # Watchlist
    merge(cache, "watchlist.btc_200wk_ma_level",  args.btc_200wk_ma)
    merge(cache, "watchlist.btc_200wk_ma_status", args.btc_200wk_status)
    merge(cache, "watchlist.xrp_key_support",     args.xrp_support)
    merge(cache, "watchlist.xrp_downside_target", args.xrp_downside)
    merge(cache, "watchlist.ascendex_warning_active", tf(args.ascendex_warn))

    # Sector scores
    merge(cache, "sector_scores.crypto",            args.score_crypto)
    merge(cache, "sector_scores.macro",             args.score_macro)
    merge(cache, "sector_scores.public_markets",    args.score_markets)
    merge(cache, "sector_scores.ai_sector",         args.score_ai)
    merge(cache, "sector_scores.defense",           args.score_defense)
    merge(cache, "sector_scores.real_estate",       args.score_realestate)
    merge(cache, "sector_scores.business_acquisitions", args.score_bizacq)

    # Congressional
    if args.congress_month:
        cache.setdefault("congressional_trades", {})["month"] = args.congress_month
    if args.congress_sectors:
        cache.setdefault("congressional_trades", {})["most_traded_sectors"] = csv(args.congress_sectors)
    if args.congress_tickers:
        cache.setdefault("congressional_trades", {})["notable_tickers"] = csv(args.congress_tickers)

    CACHE_OUT.write_text(json.dumps(cache, indent=2))
    print(f"Cache updated → {CACHE_OUT}", file=sys.stderr)
    print(json.dumps(cache, indent=2))

if __name__ == "__main__":
    main()
