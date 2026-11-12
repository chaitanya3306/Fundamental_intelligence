# FinSight AI Metric Catalog

**Status:** Initial specification. Verify provider mappings and accounting conventions before production display. Every metric needs definition, source fields, period, currency/unit, freshness, missing/zero/negative behavior, lineage and independent expected-value tests.

## 1. Company and market metrics

| Metric | Definition / inputs | Important rules |
|---|---|---|
| Share price | Provider quote/last close | Quote timestamp, currency, exchange and delayed/live status. |
| Price change | Current price − comparable prior close | Compatible quote observations. |
| Price change % | Change / prior close × 100 | Prior close nonzero. |
| Market cap | Price × compatible shares outstanding | Price/share-count timestamp compatibility; disclose source. |
| Enterprise value | Market cap + debt + preferred/minority claims − cash (document convention) | Do not assume provider conventions are identical. |
| 52-week range | Min/max eligible prices over trailing 52 weeks | Define adjusted/unadjusted prices. |
| P/E | Price / compatible EPS or market cap / net income | Label TTM/period basis; handle zero/negative earnings. |
| P/B | Market cap / book equity or price / book value/share | Negative equity needs explicit treatment. |
| P/S | Market cap / revenue | Label revenue period, usually TTM. |
| EV/EBITDA | EV / EBITDA | Same period; zero/negative EBITDA explicit. |
| Dividend yield | Annualized dividend/share / price | Label trailing vs forward basis. |
| Revenue, net income, EPS | Provider-reported observations | Period, currency, scale and basic/diluted EPS basis. |

## 2. Financial statement metrics

| Metric | Formula | Requirements/cautions |
|---|---|---|
| Gross profit | Revenue − cost of revenue, if not reported | Normalize sign conventions. |
| Gross margin | Gross profit / revenue × 100 | Same period; nonzero revenue. |
| Operating margin | Operating income / revenue × 100 | Do not substitute EBITDA for operating income. |
| Net margin | Net income / revenue × 100 | Preserve negative result. |
| Current ratio | Current assets / current liabilities | Denominator nonzero; same balance-sheet date. |
| Quick ratio | (Cash + short-term investments + receivables) / current liabilities | Component definitions and coverage explicit. |
| Debt/equity | Defined debt / total equity | Specify total debt vs liabilities; negative/zero equity explicit. |
| Interest coverage | EBIT / interest expense | Normalize expense sign; zero/negative interest policy. |
| ROE | Net income / average equity × 100 | Average beginning/ending equity where available. |
| ROA | Net income / average assets × 100 | Average assets where available. |
| ROIC | NOPAT / average invested capital × 100 | Define NOPAT, invested capital and cash/goodwill treatment. |
| ROCE | EBIT / average capital employed × 100 | Define consistently; not a renamed ROIC. |
| EBITDA | EBIT + D&A if deriving | Label provider-reported vs derived. |
| Free cash flow | Operating cash flow − capital expenditures | Normalize CapEx sign convention. |
| FCF margin | FCF / revenue × 100 | Matching period; nonzero revenue. |
| CFO / net income | Operating cash flow / net income | CFO is not FCF; denominator/negative earnings caveat. |
| FCF / net income | FCF / net income | Denominator caveat. |
| FCF / EBITDA | FCF / EBITDA | Same period; EBITDA nonzero. |
| Accrual ratio | Select and document a recognized formula | Name numerator, denominator and balance-sheet/CF inputs. |
| FCF/share | FCF / selected diluted share basis | Align flow period and share-count basis. |

## 3. Growth metrics

| Metric | Formula | Requirements/cautions |
|---|---|---|
| YoY | (Current comparable period / prior-year comparable period − 1) × 100 | Same fiscal frequency; zero/negative base explicit. |
| CAGR | (Ending / beginning)^(1 / elapsed years) − 1 | Actual elapsed time and valid positive endpoints; not row count. |
| Revenue/net income/EPS/FCF CAGR | CAGR of consistently defined series | Negative/zero endpoints make standard CAGR invalid. |
| Segment growth | (Current segment revenue / prior comparable segment revenue − 1) × 100 | Stable segment identity and mapping. |
| FCF/share growth | YoY or CAGR of consistently defined FCF/share | Compatible diluted share basis. |

## 4. Financial quality and risk

Composite scores are interpretations, not accounting facts. Do not display until weights, thresholds, history requirements, coverage and version are documented.

| Indicator | Evidence | Limitations |
|---|---|---|
| Earnings quality | Net income vs operating cash flow; accrual measures | CFO not FCF; one period is not proof of manipulation. |
| Cash conversion | CFO/net income, FCF/net income, FCF/EBITDA | Denominator and working-capital volatility caveats. |
| Profitability | Gross/operating/net margin trends | Industry/business model context. |
| Balance-sheet strength | Debt/equity, current/quick ratio, interest coverage | Consistent definitions and sector context. |
| Returns | ROE, ROA, ROIC, ROCE | Leverage and average balance inputs matter. |
| Capital allocation | CapEx, R&D, dividends, buybacks, payout ratio | Provider coverage; spending is not automatically good/bad. |
| Receivables warning | Receivables growth vs revenue growth | Both series need at least two comparable valid observations. |
| Cash-profit divergence | Net income vs operating cash flow | Use CFO, not FCF; investigate working capital and timing. |
| Altman Z-score | Document appropriate formula variant | Applicability varies by company type/industry. |

Every risk signal must identify evidence, formula/rule, threshold, rationale and limitations. Insufficient evidence is Unavailable, not Low Risk.

## 5. Valuation

| Output | Definition | Requirements |
|---|---|---|
| Projected FCF | Forecast from normalized starting cash flow and assumptions | Specify unlevered vs levered. |
| PV of forecast FCF | Sum of projected FCF discounted at consistent WACC/cost of equity | Period timing explicit. |
| Gordon terminal value | Final forecast FCF × (1 + g) / (discount rate − g) | Discount rate > terminal growth. |
| Enterprise value | PV forecast cash flows + PV terminal value | For unlevered FCF discounted at WACC. |
| Equity value | EV + cash − debt − other specified senior claims | State treatment of leases, preferred/minority interest. |
| Intrinsic value/share | Equity value / compatible diluted shares | Never divide EV directly by shares. |
| Upside/downside | (Intrinsic/share / current price − 1) × 100 | Compatible price timestamp/currency. |
| Relative valuation | Selected multiple × compatible denominator, with equity bridge if EV-based | Comparable periods and definitions. |
| DDM | PV of forecast dividends plus terminal dividend value | Requires dividend history and defensible cost-of-equity/growth. |
| Sensitivity | Recalculate valuation across explicit input grid | Center cell reconciles to base case. |
| Scenarios | Independently recalculate bear/base/bull assumptions | Not just relabelled outputs. |

## 6. Required test cases
For each implemented metric, test a hand-checked positive example, zero denominator, missing input, negative input where meaningful, incompatible periods, unit/currency mismatch detection where supported, irregular historical periods and duplicate observations.

## 7. Definitions still to decide
- Exact provider and aliases per metric.
- Debt definition for leverage and EV.
- ROIC/ROCE invested-capital conventions.
- Accrual ratio formula.
- Financial Quality weights and minimum coverage.
- DCF cash-flow convention and discount rate.
- Diluted share count source/time.
- Trailing vs forward dividend basis.
- Peer universe and relative-valuation source.
