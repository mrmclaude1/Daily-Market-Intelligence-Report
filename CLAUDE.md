# Daily Market Intelligence Report — Session Instructions

## Purpose
This repository stores the persistent cache for the Daily Market Intelligence Report.
Every scheduled run reads `report_cache.json` at start (for diffs) and writes it back
at the end (via GitHub API). The cache is what makes Section 2 (Daily Change Log)
show real before/after comparisons instead of "New Signal / Baseline" every time.

---

## Network Architecture — Know This First

### What runs server-side at Anthropic (proxy-exempt):
- **WebSearch** — use for news, congressional trades, weather, prediction markets
- **WebFetch** — use for structured pages; may 403 if the target site blocks bots
- **MCP tools** (CoinDesk, Crypto.com) — live crypto prices and news

### What runs in-container (goes through local egress proxy):
- **Bash / curl** — `api.github.com` is reachable; proxy injects GitHub auth automatically
- **No `REPORT_GITHUB_TOKEN` needed** — the proxy handles authentication transparently
- **git clone / git push are blocked** — use GitHub Contents API instead
- **Playwright/Chromium** — blocked from all external sites

### 403 errors from WebFetch:
These are the target website blocking server-side fetches. Fix: use WebSearch instead.

---

## MANDATORY: Start-of-Run Protocol

Run this at the **very start of every session**, before any market data searches.
This fetches the previous report's values so Section 2 can show real diffs.

```bash
# Download previous cache and update helper from GitHub (proxy handles auth)
REPO="mrmclaude1/Daily-Market-Intelligence-Report"
API="https://api.github.com/repos/${REPO}/contents"

echo "=== Fetching previous report cache ==="
curl -s "${API}/report_cache.json" \
  -H "Accept: application/vnd.github.v3+json" | python3 -c "
import json, sys, base64
d = json.load(sys.stdin)
sha = d.get('sha','')
content = base64.b64decode(d['content']).decode('utf-8')
with open('/tmp/report_cache.json', 'w') as f: f.write(content)
with open('/tmp/cache_sha.txt', 'w') as f: f.write(sha)
print(f'Cache loaded: {len(content)} bytes, SHA {sha[:8]}')
"

echo "=== Fetching update_cache.py ==="
curl -s "${API}/update_cache.py" \
  -H "Accept: application/vnd.github.v3+json" | python3 -c "
import json, sys, base64
d = json.load(sys.stdin)
content = base64.b64decode(d['content']).decode('utf-8')
with open('/tmp/update_cache.py', 'w') as f: f.write(content)
print(f'update_cache.py loaded: {len(content)} bytes')
"

echo "=== Prior report values for diff ==="
python3 - <<'PYEOF'
import json
try:
    c = json.load(open('/tmp/report_cache.json'))
    p = c.get('prices', {})
    m = c.get('markets', {})
    mac = c.get('macro', {})
    re = c.get('real_estate', {})
    etf = c.get('crypto_etf', {})
    reg = c.get('regulation', {})
    w = c.get('watchlist', {})
    s = c.get('sector_scores', {})
    print("=" * 50)
    print(f"PRIOR REPORT DATE : {c.get('meta',{}).get('last_report_date','NONE')}")
    print(f"REPORT COUNT      : {c.get('meta',{}).get('report_count',0)}")
    print("-" * 50)
    print(f"BTC               : ${p.get('btc_usd','N/A'):,}  ({p.get('btc_change_24h_pct','N/A')}% 24h)  High:{p.get('btc_24h_high','N/A')}  Low:{p.get('btc_24h_low','N/A')}")
    print(f"ETH               : ${p.get('eth_usd','N/A'):,}  ({p.get('eth_change_24h_pct','N/A')}% 24h)")
    print(f"XRP               : ${p.get('xrp_usd','N/A')}  ({p.get('xrp_change_24h_pct','N/A')}% 24h)")
    print(f"S&P 500           : {m.get('sp500_level','N/A')}  ({m.get('sp500_change_24h_pct','N/A')}%)")
    print(f"Nasdaq            : {m.get('nasdaq_level','N/A')}  ({m.get('nasdaq_change_24h_pct','N/A')}%)  Down days: {m.get('nasdaq_consecutive_down_days','N/A')}")
    print(f"VIX               : {m.get('vix','N/A')}")
    print(f"Market posture    : {m.get('market_posture','N/A')}")
    print(f"Fed rate          : {mac.get('fed_funds_rate_lower','N/A')}–{mac.get('fed_funds_rate_upper','N/A')}%")
    print(f"Cuts projected    : {mac.get('cuts_projected_2026','N/A')}  Hike on table: {mac.get('rate_hike_on_table','N/A')}")
    print(f"Iran war active   : {mac.get('iran_war_active','N/A')}  Ceasefire: {mac.get('iran_ceasefire_confirmed','N/A')}")
    print(f"Oil trend         : {mac.get('oil_trend','N/A')}")
    print(f"Mortgage 30yr     : {re.get('mortgage_30yr_fixed_pct','N/A')}%")
    print(f"BTC ETF weekly    : ${etf.get('btc_spot_etf_weekly_flow_bn','N/A')}B  4-wk total: ${etf.get('btc_spot_etf_total_outflow_4wk_bn','N/A')}B")
    print(f"CLARITY Act odds  : {reg.get('clarity_act_polymarket_odds_pct','N/A')}%  (prior peak: {reg.get('clarity_act_prior_peak_odds_pct','N/A')}%)")
    print(f"XRP ETF approved  : {reg.get('xrp_etf_approved','N/A')}")
    print(f"XRP key support   : ${w.get('xrp_key_support','N/A')}  downside: ${w.get('xrp_downside_target','N/A')}")
    print(f"BTC 200wk MA      : ${w.get('btc_200wk_ma_level','N/A')}  status: {w.get('btc_200wk_ma_status','N/A')}")
    print("-" * 50)
    print(f"SECTOR SCORES     : Crypto={s.get('crypto','N/A')} Macro={s.get('macro','N/A')} Markets={s.get('public_markets','N/A')} AI={s.get('ai_sector','N/A')} Defense={s.get('defense','N/A')} RE={s.get('real_estate','N/A')} BizAcq={s.get('business_acquisitions','N/A')}")
    print("-" * 50)
    print(f"TOP SIGNALS       :")
    for sig in c.get('top_signals', []): print(f"  • {sig}")
    print(f"ELEVATED RISKS    :")
    for risk in c.get('elevated_risks', []): print(f"  • {risk}")
    print("=" * 50)
    print("Use the above values to populate Section 2 Daily Change Log with REAL diffs.")
except Exception as e:
    print(f"BASELINE: {e} — no prior data. Mark all signals as New Signal.")
PYEOF
```

**After running the above:**
- If output shows a prior report date → compare today's data to those values in Section 2
- If output says BASELINE → mark all signals as "New Signal" in Section 2

---

## MANDATORY: End-of-Run Protocol

After the complete report is generated, run this to persist today's values.
Replace all placeholder values with the actual numbers from today's report.

```bash
# Step 1: Update cache with today's values
python3 /tmp/update_cache.py \
  --date "YYYY-MM-DD" \
  --btc-price BTC_PRICE \
  --btc-chg BTC_24H_PCT \
  --eth-price ETH_PRICE \
  --eth-chg ETH_24H_PCT \
  --xrp-price XRP_PRICE \
  --xrp-chg XRP_24H_PCT \
  --btc-high BTC_24H_HIGH \
  --btc-low BTC_24H_LOW \
  --eth-high ETH_24H_HIGH \
  --xrp-high XRP_24H_HIGH \
  --fed-upper FED_UPPER \
  --fed-lower FED_LOWER \
  --pce-2026 CORE_INFLATION_PCT \
  --prime-rate PRIME_RATE \
  --hike-on-table true_or_false \
  --cuts-2026 NUM_CUTS \
  --iran-war true_or_false \
  --iran-ceasefire true_or_false \
  --oil-trend "rising|falling|stable" \
  --sp500 SP500_LEVEL \
  --sp500-chg SP500_PCT \
  --nasdaq NASDAQ_LEVEL \
  --nasdaq-chg NASDAQ_PCT \
  --nasdaq-down-days NUM \
  --vix VIX_LEVEL \
  --market-posture "risk-on|risk-off|mixed-risk-off|mixed" \
  --mortgage-30yr RATE_PCT \
  --btc-etf-weekly WEEKLY_FLOW_BILLIONS \
  --btc-etf-4wk FOUR_WEEK_FLOW_BILLIONS \
  --clarity-odds POLYMARKET_PCT \
  --xrp-etf-approved true_or_false \
  --top-signals "SIGNAL1,SIGNAL2,SIGNAL3,SIGNAL4,SIGNAL5" \
  --elevated-risks "RISK1,RISK2,RISK3,RISK4,RISK5" \
  --btc-200wk-ma BTC_200WK_MA_PRICE \
  --btc-200wk-status "above|below|testing" \
  --xrp-support XRP_KEY_SUPPORT \
  --xrp-downside XRP_DOWNSIDE_TARGET \
  --congress-month "Month YYYY" \
  --congress-sectors "Sector1,Sector2,Sector3" \
  --congress-tickers "TICK1,TICK2,TICK3" \
  --score-crypto SCORE \
  --score-macro SCORE \
  --score-markets SCORE \
  --score-ai SCORE \
  --score-defense SCORE \
  --score-realestate SCORE \
  --score-bizacq SCORE

# Step 2: Push updated cache to GitHub (proxy handles auth — no token needed)
SHA=$(cat /tmp/cache_sha.txt)
CONTENT=$(base64 -w 0 < /tmp/report_cache_updated.json)
DATE_TODAY=$(date -u +"%Y-%m-%d")
curl -s -X PUT "https://api.github.com/repos/mrmclaude1/Daily-Market-Intelligence-Report/contents/report_cache.json" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"cache: ${DATE_TODAY}\", \"content\": \"${CONTENT}\", \"sha\": \"${SHA}\"}" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
if 'content' in d:
    print('✅ Cache pushed:', d['content']['sha'][:8])
else:
    print('❌ Push failed:', d.get('message','unknown'))
"
```

---

## GitHub Cache Details

- **Repo:** `mrmclaude1/Daily-Market-Intelligence-Report`
- **Cache file:** `report_cache.json` at repo root
- **Auth:** Proxy-injected automatically — NO token env var required
- **Mechanism:** GitHub Contents API via curl — no git clone needed
- **api.github.com is reachable** directly from the container

---

## Data Sources by Category

### Congressional Trades (capitoltrades.com and unusualwhales.com block server-side fetches)
Use WebSearch:
- `"congress stock trades disclosed June 2026"`
- `"STOCK Act disclosures [CURRENT MONTH] [YEAR]"`
- `site:trendlyne.com us politicians recent trades`

### Weather 30080 (forecast.weather.gov and wunderground.com block server-side fetches)
Use WebSearch:
- `"NWS Atlanta Smyrna GA 30080 forecast [TODAY'S DATE]"`
- `"accuweather smyrna GA 30080 forecast"`
- `"weather.gov Atlanta heat advisory [TODAY'S DATE]"`

### Live Crypto Prices
Use MCP tools (load via ToolSearch):
- `mcp__CoinDesk__fetch_index_tick` → BTC-USD, ETH-USD, XRP-USD
- `mcp__CoinDesk__fetch_news` → latest crypto news (limit 30)

### Everything Else
Use WebSearch and WebFetch — financial news sites are accessible server-side.

---

## Zip Code for Weather
30080 (Smyrna / Atlanta, GA)
