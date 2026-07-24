# ETF Holdings Explorer

Enter any ETF ticker and a date range. The app shows the fund's price chart,
its current top holdings ranked by weight, and individual price charts for
each of the top 8 holdings.

## Holdings cleanup

Some funds report the same underlying company multiple times — for example,
as a direct equity position and separately as a total-return swap contract
on that same company. This app groups those together under one clean
company name and combines their weight, so you see the fund's real exposure
to each company rather than duplicate synthetic entries.

## Data source and limitations

Holdings and prices come from Yahoo Finance via the `yfinance` library.
Yahoo typically exposes a fund's **top ~10 holdings**, not its complete
daily holdings file — for the full list of a specific fund, check that
fund issuer's official site directly.

## Access

This app is private and limited to approved users.

---

Created by Augustine Villalobos
