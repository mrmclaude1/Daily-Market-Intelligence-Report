# Daily Market Intelligence Report — Session Instructions

## Purpose
This repository stores the persistent cache for the Daily Market Intelligence Report.
Every scheduled run reads `report_cache.json` at start (for diffs) and writes it back
at the end (via GitHub API). The cache is the mechanism that makes Section 2 (Daily Change
Log) show real before/after comparisons instead of "New Signal" every time.

---

## Network Architecture — Know This Before Anything Else

### What runs server-side at Anthropic (proxy-exempt):
- **WebSearch** — use for all news, congressional trades, weather, prediction markets
- **WebFetch** — use for structured web pages; may return 403 if the TARGET SITE blocks bots
- **MCP tools** (CoinDesk, Crypto.com) — use for live crypto prices and news

### What runs in-container (goes through local egress proxy):
- **Bash / curl** — only `api.github.com` is reachable externally (used for cache r/w)
- **Playwright/Chromium** — blocked from all external sites; do NOT use
- **git clone** — blocked; use GitHub Contents API instead

### 403 errors from WebFetch:
These are the TARGET WEBSITE blocking server-side fetches (anti-bot).
**Fix:** Use WebSearch instead, or find an alternative URL for the same data.

---

## MANDATORY: Start-of-Run Protocol

At the very start of every run, before any market data searches:

```bash
# Step 1: Load the GitHub cache helper
source /home/user/market-report-cache/cache_io.sh

# Step 2: Download previous report cache
PREVIOUS_CACHE=$(fetch_cache)
echo "$PREVIOUS_CACHE" > /tmp/previous_cache.json

# Step 3: Extract key values for diff
python3 - <<'EOF'
import json, sys
try:
    cache = json.load(open('/tmp/previous_cache.json'))
    print("=== PREVIOUS REPORT DATA FOR DIFF ===")
    print(f"Report date:       {cache.get('meta',{}).get('last_report_date', 'NONE')}")
    p = cache.get('prices', {})
    print(f"BTC price:         ${p.get('btc_usd', 'N/A'):,}")
    print(f"ETH price:         ${p.get('eth_usd', 'N/A'):,}")
    print(f"XRP price:         ${p.get('xrp_usd', 'N/A')}")
    m = cache.get('markets', {})
    print(f"S&P 500:           {m.get('sp500_level', 'N/A')}")
    print(f"Nasdaq:            {m.get('nasdaq_level', 'N/A')}")
    r = cache.get('regulation', {})
    print(f"CLARITY Act odds:  {r.get('clarity_act_polymarket_odds_pct', 'N/A')}%")
    mac = cache.get('macro', {})
    print(f"Fed rate upper:    {mac.get('fed_funds_rate_upper', 'N/A')}%")
    re = cache.get('real_estate', {})
    print(f"Mortgage 30yr:     {re.get('mortgage_30yr_fixed_pct', 'N/A')}%")
    w = cache.get('watchlist', {})
    print(f"BTC 200wk MA:      {w.get('btc_200wk_ma_status', 'N/A')}")
    print(f"XRP key support:   ${w.get('xrp_key_support', 'N/A')}")
    print(f"AscendEX warning:  {w.get('ascendex_warning_active', 'N/A')}")
    print(f"Top signals:       {cache.get('top_signals', [])}")
    print(f"Elevated risks:    {cache.get('elevated_risks', [])}")
except Exception as e:
    print(f"BASELINE: No prior cache found ({e}). All signals are New Signal.")
EOF
```

Use the output to populate Section 2 (Daily Change Log) with real diffs.
If the output says BASELINE, mark all signals as "New Signal."

---

## MANDATORY: End-of-Run Protocol

After the complete report is generated, run this to persist today's values:

```bash
python3 /home/user/market-report-cache/update_cache.py \
  --date "$(date -u +%Y-%m-%d)" \
  --btc-price BTC_PRICE_HERE \
  --btc-chg BTC_24H_PCT_HERE \
  --eth-price ETH_PRICE_HERE \
  --eth-chg ETH_24H_PCT_HERE \
  --xrp-price XRP_PRICE_HERE \
  --xrp-chg XRP_24H_PCT_HERE \
  --btc-high BTC_HIGH_HERE \
  --btc-low BTC_LOW_HERE \
  --fed-upper 3.75 \
  --fed-lower 3.5 \
  --pce-2026 3.6 \
  --prime-rate 6.75 \
  --hike-on-table true \
  --cuts-2026 0 \
  --iran-ceasefire true \
  --oil-trend "falling" \
  --sp500 SP500_LEVEL_HERE \
  --sp500-chg SP500_PCT_HERE \
  --nasdaq NASDAQ_LEVEL_HERE \
  --nasdaq-chg NASDAQ_PCT_HERE \
  --market-posture "risk-off" \
  --mortgage-30yr 6.56 \
  --inventory-yoy 1.8 \
  --listing-px-yoy -2.4 \
  --clarity-odds POLYMARKET_ODDS_HERE \
  --xrp-etf-approved true \
  --top-signals "SIGNAL1,SIGNAL2,SIGNAL3" \
  --elevated-risks "RISK1,RISK2,RISK3" \
  --btc-200wk-ma 57500 \
  --btc-200wk-status "testing" \
  --xrp-support 1.09 \
  --xrp-downside 0.88 \
  --ascendex-warn true \
  --congress-month "June 2026" \
  --congress-sectors "Technology,Defense,Healthcare" \
  --congress-tickers "NVDA,GOOGL,MCK"

# Then push to GitHub
source /home/user/market-report-cache/cache_io.sh
push_cache /tmp/report_cache_updated.json
```

Replace all `_HERE` placeholders with the actual values from today's report.
If `REPORT_GITHUB_TOKEN` is not set, the push step logs a warning and continues.

---

## GitHub Cache Setup

- **Repo:** `mrmclaude1/Daily-Market-Intelligence-Report`
- **File stored:** `report_cache.json` at root of repo
- **Auth token env var:** `REPORT_GITHUB_TOKEN` (GitHub PAT with `repo` scope)
- **Mechanism:** GitHub Contents API via `curl` — no git clone needed
- **api.github.com is reachable** from the container even though most other sites are not

### Setup checklist (one-time):
- [ ] Repo initialized at github.com/mrmclaude1/Daily-Market-Intelligence-Report (needs ≥1 commit)
- [ ] GitHub PAT created at github.com/settings/tokens with `repo` scope checked
- [ ] `REPORT_GITHUB_TOKEN` added to the Claude Code scheduled job (see below)

### How to set REPORT_GITHUB_TOKEN in Claude Code web (Step 3):
1. Go to your Claude Code web dashboard at code.claude.com
2. Find the scheduled job that runs this report (the 6:35 AM job)
3. Open its **Settings** or **Configuration**
4. Find the **Environment Variables** or **Secrets** section
5. Add a new variable:
   - Name:  `REPORT_GITHUB_TOKEN`
   - Value: `ghp_xxxxxxxxxxxxxxxxx`  ← your PAT from github.com/settings/tokens
6. Save / Apply
7. The variable will be available as `$REPORT_GITHUB_TOKEN` in every future run

Full Claude Code web environment docs: https://code.claude.com/docs/en/claude-code-on-the-web

---

## Data Sources by Category

### Congressional Trades (capitoltrades.com, unusualwhales.com are proxy-blocked)
Use WebSearch:
- `"congress stock trades disclosed June 2026"`
- `"STOCK Act disclosures [CURRENT MONTH] [YEAR]"`
- `"[MEMBER NAME] stock trade disclosure 2026"`
- `site:trendlyne.com us politicians recent trades`
- Check congressstock.com via WebSearch if direct WebFetch fails

### Weather 30080 (forecast.weather.gov, wunderground.com are proxy-blocked)
Use WebSearch:
- `"NWS Atlanta Smyrna GA 30080 forecast [TODAY'S DATE]"`
- `"accuweather smyrna GA 30080"` (try WebFetch on accuweather if search gives good results)
- `"weather.gov Atlanta forecast [TODAY'S DATE]"`

### Crypto (live prices)
Use MCP tools (load via ToolSearch if not available):
- `mcp__Crypto-com__get_ticker` → BTC_USDT, ETH_USDT, XRP_USDT
- `mcp__CoinDesk__fetch_news` → latest crypto news
- `mcp__CoinDesk__fetch_spot_tick` → spot prices by exchange

### Macro, Markets, AI, Defense, Real Estate
Use WebSearch and WebFetch — most financial news sites are accessible server-side.

---

## Report Requirements

Run the complete 18-section Daily Market Intelligence Report.
Section 2 (Daily Change Log) MUST use the prior cache values for real diffs.
Section 12 (Congressional Trades) — use WebSearch; note limitations when specific
  disclosures cannot be verified.
Section 0 (Weather) — use WebSearch; note NWS direct access is unavailable.

## Zip Code for Weather
30080 (Smyrna / Atlanta, GA)
