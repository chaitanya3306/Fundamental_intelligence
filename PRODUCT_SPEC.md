# FinSight AI Product Specification

**Status:** Approved product direction. Implementation status lives in PROJECT_PROGRESS.md.

## Product purpose
FinSight AI is a fundamental-analysis and financial-intelligence application for supported US-listed companies. It helps users move from company discovery to understanding a company's business, financial statements, quality, growth and valuation. It is a research tool, not an automated trading system or a guarantee of investment returns.

## Product principles
- Evidence before presentation: every number traces to a provider observation or documented calculation.
- Honest availability: missing/unsupported data is unavailable, never fabricated or silently converted to zero.
- Period correctness: annual, quarterly and TTM values remain distinct.
- Transparent calculations: disclose definitions, inputs, assumptions and limitations.
- Shared company context: selected company persists across pages.
- Build data-backed vertical slices, not disconnected mock screens.
- Support only markets/securities/providers whose coverage is verified.

## Navigation and references
Exactly six primary pages:
1. Home: Artifacts/Home.png
2. Company Overview: Artifacts/Company Overview.png
3. Financial Statements: Artifacts/Financial Statement.png
4. Financial Quality: Artifacts/Financial Quality.png
5. Growth Analysis: Artifacts/Growth Analysis.png
6. Valuation: Artifacts/Valuation.png

Journey: Home → search/select company → Company Overview → Statements / Quality / Growth / Valuation. The selected company persists across company pages. These images define visual hierarchy and expected interactions. Their sample numbers, dates, logos, news and company facts are illustrative and must not be hardcoded as live facts.

## Page requirements

### Home
- Global header, company/ticker search, popular ticker shortcuts.
- Market overview/index cards, gainers/losers and latest news as shown.
- Search supports only known securities.
- Market indices/movers require market-wide data sources and timestamps; news requires real source, publication time and link. Defer unsupported features or show unavailable states.

### Company Overview
- Company identity, ticker, exchange, sector/industry, description and profile facts.
- Price/change/quote timestamp; market cap, P/E, revenue, net income, EPS, 52-week range.
- Historical price and volume chart with selectable windows.
- TTM fundamentals, historical revenue/net-income, valuation ratios and annual snapshot.
- Quote time and financial reporting period must be distinguished. Market cap uses compatible price and share count. Unknown profile fields remain unknown.

### Financial Statements
- Income statement, balance sheet and cash flow statement.
- Annual/quarterly controls and explicit currency/scale.
- Historical tables, key metrics, margin/ratio charts.
- Preserve signs and missing values. Do not mix annual, quarterly or TTM without explicit derivation and labels. Derived rows need formulas.

### Financial Quality
- Earnings quality, cash conversion, profitability/returns, balance-sheet strength, margins and capital allocation.
- Overall/component scores only after methodology, weights, thresholds, history and coverage rules are documented.
- Each strength/risk links to evidence and limitations. Insufficient evidence is not a healthy score. CFO and FCF are different. Heuristics are not proof of misconduct.

### Growth Analysis
- Revenue, net income, EPS, operating income, FCF and FCF/share growth.
- Annual/quarterly controls, historical values, YoY, CAGR, comparisons and segment growth where sourced.
- CAGR uses valid endpoints and elapsed time, not simply row count. Handle zero/negative bases and missing periods. Compare like-for-like periods.

### Valuation
- Market multiples (EV, P/E, P/B, P/S, EV/EBITDA, dividend yield where supported).
- DCF projections and adjustable assumptions, base/bull/bear scenarios, relative valuation, DDM where data supports it, sensitivity and takeaways.
- Define unlevered vs levered cash flow and consistent discount rate. For unlevered FCF: calculate EV, bridge to equity (cash, debt and documented adjustments), then divide by compatible diluted shares. Assumptions are not reported facts. Scenarios must recalculate independently; sensitivity central case must reconcile to base case.

## Shared behavior
- Persistent selected company and consistent navigation.
- Loading, empty, invalid ticker, stale data, provider failure and unavailable-data states.
- Consistent currency, scale, percentage and negative formatting.
- Metric definitions/tooltips.
- Responsive and accessible controls.
- WhaleWatch AI and Combined Analysis are future features, not primary MVP pages.

## Data classification
Every value is classified as provider-reported observation, derived calculation, market-data observation, user assumption or sourced estimate. Preserve source, retrieval time, reporting period, currency/unit and freshness where available. Review provider coverage, terms, rate limits and licensing.

## Acceptance
A page is complete only when its data is sourced/calculated, contracts and UI controls work, context persists, missing/stale/error states are correct, values reconcile, tests pass and material visual differences are reviewed.
