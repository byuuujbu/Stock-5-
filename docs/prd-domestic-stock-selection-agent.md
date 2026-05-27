# PRD: Domestic Stock Selection Agent

## Problem Statement

The user wants a local AI-assisted stock screening agent that runs every Korean trading day after the regular domestic stock market close, excluding after-market data, and identifies KOSPI and KOSDAQ stocks that simultaneously meet three screening criteria:

1. Daily trading value is at least KRW 1 trillion.
2. Annual operating profit was positive for each of the most recent 3 fiscal years, using annual values rather than LTM.
3. Daily price increase is at least 5%.

The user needs the selected stocks to be available in a web dashboard, preserved by date for historical review, enriched with recent relevant news, and sent as a daily messenger notification.

## Solution

Build a local Windows-first web application and scheduled agent.

The agent runs at 15:45 KST on weekdays, after the regular Korean market close. It fetches market data for KOSPI and KOSDAQ stocks, filters candidates by trading value and daily change rate, verifies the most recent 3 annual operating profit values through OpenDART, enriches selected stocks with up to 3 relevant NAVER News Search API articles from the previous 7 days, stores the daily result in SQLite, and sends a Telegram notification.

The web application exposes:

- A Dashboard showing the latest selected stocks, capped at 10 stocks and sorted by trading value descending.
- Relevant recent news per selected stock.
- A History page listing prior run dates and allowing users to view historical selections.

The MVP supports sample data mode so the full product flow can be tested without API keys. Real API mode is enabled by adding credentials to `.env`.

## User Stories

1. As a private investor, I want the agent to run after the regular Korean market close, so that the selected stocks reflect regular-session data rather than after-market movement.
2. As a private investor, I want KOSPI stocks screened, so that I can monitor large domestic exchange-listed opportunities.
3. As a private investor, I want KOSDAQ stocks screened, so that I can monitor high-momentum domestic growth stocks as well.
4. As a private investor, I want stocks filtered by daily trading value of at least KRW 1 trillion, so that selected stocks have meaningful market liquidity.
5. As a private investor, I want stocks filtered by daily price increase of at least 5%, so that selected stocks show significant same-day momentum.
6. As a private investor, I want stocks filtered by positive annual operating profit for the most recent 3 fiscal years, so that selected stocks have a basic profitability track record.
7. As a private investor, I want the operating profit rule to use annual values rather than LTM, so that the rule matches a simple fiscal-year profitability screen.
8. As a private investor, I want connected financial statements checked first, so that consolidated business performance is prioritized.
9. As a private investor, I want separate financial statements used when connected statements are unavailable, so that otherwise valid companies are not excluded unnecessarily.
10. As a private investor, I want all screening criteria applied as simultaneous filters rather than weighted priorities, so that every selected stock satisfies every rule.
11. As a private investor, I want selected stocks sorted by trading value descending when more than 10 pass the filter, so that the dashboard emphasizes the most liquid names.
12. As a private investor, I want the dashboard capped at 10 stocks, so that the daily result remains easy to scan.
13. As a private investor, I want each selected stock to show market, ticker, name, closing price, daily change rate, and trading value, so that I can evaluate the selection quickly.
14. As a private investor, I want each selected stock to show recent relevant articles, so that I can understand possible market context.
15. As a private investor, I want news limited to the last 7 days, so that stale articles do not distort the daily context.
16. As a private investor, I want up to 3 articles per stock, so that each selection has useful context without clutter.
17. As a private investor, I want article selection based on relevance rather than unavailable public view counts, so that the feature can be implemented reliably with official APIs.
18. As a private investor, I want NAVER News Search API support, so that Korean stock news quality is practical for domestic equities.
19. As a private investor, I want duplicate news links removed, so that the same article does not appear multiple times.
20. As a private investor, I want the daily selection stored by date, so that I can revisit past results.
21. As a private investor, I want a History page, so that I can browse prior screening days.
22. As a private investor, I want a daily Telegram notification, so that I do not need to manually open the dashboard every day.
23. As a private investor, I want the Telegram notification to summarize selected stocks and include a dashboard link, so that I can quickly move from alert to details.
24. As a private investor, I want the system to handle days with no selected stocks, so that an empty result is clear rather than ambiguous.
25. As a local Windows user, I want a Windows Task Scheduler registration script, so that the daily run can be automated on my PC.
26. As a local Windows user, I want the scheduled task to run at 15:45 KST on weekdays, so that the agent runs after the regular market close.
27. As a local Windows user, I want a manual run command, so that I can test the selector on demand.
28. As a local Windows user, I want a sample mode, so that I can verify dashboard, history, database, and notification flow before entering API credentials.
29. As a local Windows user, I want a `.env.example`, so that I know which credentials and settings are required.
30. As a local Windows user, I want real secrets excluded from git, so that API keys and tokens are not accidentally committed.
31. As a maintainer, I want KIS, OpenDART, NAVER News, and Telegram integrations isolated behind provider modules, so that each external dependency can be changed independently.
32. As a maintainer, I want the screening rules isolated in a deep module, so that the rule set can be tested without web, database, or notification concerns.
33. As a maintainer, I want SQLite persistence isolated behind a data access module, so that schema behavior is explicit and testable.
34. As a maintainer, I want the web server to read from stored daily results, so that dashboard rendering does not trigger external API calls.
35. As a maintainer, I want the API adapters to fail clearly when configuration is missing, so that operational setup problems are obvious.
36. As a maintainer, I want the stock universe to be maintained through a CSV, so that KOSPI/KOSDAQ coverage can be updated without code changes.
37. As a maintainer, I want DART corp code mapping cached locally, so that repeated runs avoid unnecessary downloads.
38. As a maintainer, I want date-based run replacement, so that rerunning the same day updates that day’s result deterministically.
39. As a maintainer, I want provider interfaces to be simple, so that sample providers and real providers remain interchangeable.
40. As a maintainer, I want the MVP to avoid React/Next.js complexity, so that local operation and debugging stay simple.

## Implementation Decisions

- Use FastAPI and Jinja2 for the local web dashboard.
- Use SQLite for local historical storage.
- Use a Windows-first execution model with PowerShell scripts and Task Scheduler.
- Run the daily scheduled job at 15:45 KST on weekdays.
- Treat the three stock selection criteria as hard filters, not a weighted score.
- Include both KOSPI and KOSDAQ stocks.
- Cap displayed and notified selections at 10 stocks.
- Sort selected stocks by daily trading value descending.
- Use KIS Developers API as the market data source for domestic stock quote data.
- Use OpenDART as the financial data source for annual operating profit.
- Use connected financial statements first and fallback to separate financial statements when connected statements are unavailable.
- Use NAVER News Search API for recent relevant articles.
- Define news relevance as “recent 7-day related articles from NAVER News Search API” rather than actual article view counts, because stable official view count access is not available.
- Use Telegram Bot API as the only notification channel for the MVP.
- Store configuration in `.env`, with `.env.example` committed and `.env` ignored.
- Provide a deterministic sample data mode for local verification without external API credentials.
- Keep market data, financial data, news, notification, screening, persistence, and web rendering as separate modules.
- Keep the web dashboard read-only for MVP.
- Save a daily run record even when zero stocks are selected, so the History page can show that the job ran.
- Replace an existing run for the same date when manually rerun, so same-day retries are deterministic.
- Use a local CSV as the stock universe input for KIS quote iteration.
- Cache OpenDART corp code mappings locally.
- Use provider interfaces that return simple domain objects:
  - Market data provider returns stock quotes.
  - Financial provider returns recent annual operating profits.
  - News provider returns recent articles.
  - Notifier sends a daily result summary.
- Keep KIS response field mapping isolated because KIS endpoint schemas and field names may differ by endpoint or environment.

## Testing Decisions

- Good tests should verify external behavior rather than implementation details.
- The screening module should be tested with sample providers to confirm:
  - Stocks below KRW 1 trillion trading value are excluded.
  - Stocks below 5% daily change are excluded.
  - Stocks without 3 positive annual operating profit values are excluded.
  - Passing stocks are sorted by trading value descending.
  - Results are capped at 10.
- The persistence module should be tested against a temporary SQLite database to confirm:
  - Runs are saved by date.
  - Same-day reruns replace prior selections and articles.
  - Latest run loading returns selected stocks with attached articles.
  - History lists run dates and stock counts.
- The web module should be tested with FastAPI’s test client to confirm:
  - Dashboard renders the latest run.
  - Dashboard renders an empty state when no run exists.
  - History renders prior dates.
  - History detail renders a selected date.
- The Telegram notifier should be tested by mocking the HTTP call to confirm:
  - No call is made when token or chat ID is missing.
  - Message text includes run date, selected stocks, and dashboard URL.
  - Empty results are represented clearly.
- Provider integration tests against real KIS, OpenDART, and NAVER APIs should be opt-in because they require credentials, network access, and may be rate-limited.
- Prior art in the current codebase is limited because this is a new repository. The sample providers and current manual sample run provide the initial behavioral baseline.

## Out of Scope

- Automated trading or order placement.
- Buy/sell recommendations.
- Portfolio management.
- Backtesting.
- Risk scoring.
- Valuation scoring.
- LTM or quarterly operating profit screening.
- Article view-count ranking.
- Slack, KakaoTalk, Discord, email, or multi-recipient notification management.
- Multi-user authentication.
- Cloud deployment.
- Mobile app development.
- Full KRX holiday calendar integration in the MVP.
- Automatic KOSPI/KOSDAQ universe download in the MVP.
- Advanced NLP summarization of articles.
- Paid data vendor integrations.

## Further Notes

- The current implementation already includes the MVP structure, sample mode, SQLite persistence, FastAPI dashboard, History page, KIS/OpenDART/NAVER provider modules, Telegram notifier, and Windows scheduling scripts.
- Real operation still requires valid credentials for KIS Developers, OpenDART, NAVER Developers, and Telegram Bot API.
- The KIS provider may require field mapping adjustment after testing with the user’s actual KIS API credentials and selected endpoint permissions.
- The stock universe CSV must be maintained for real screening coverage.
- The local PC must remain powered on and connected to the network at the scheduled execution time.
- If reliability becomes important, the next operational step should be moving scheduled execution from a local PC to a small server, NAS, or cloud VM.

