# SES Companies Scraper

Config-driven Python scraper that outputs a CSV of companies from a target SES page.

## Setup

1. Create a virtual environment (optional) and install requirements:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

1. Copy `scraper/config.sample.yml` to `scraper/config.yml` and update `url` and CSS selectors to match the page listing SES affiliates/companies.
2. Run the scraper:

```bash
python -m scraper.main --config scraper/config.yml --out ses_companies.csv
```

The output CSV contains columns: `name,link`.

## Notes

- Adjust selectors using your browser devtools. If SES publishes an "Affiliates" page, set `url` to that page and target the list items.
- The scraper uses retries and a desktop User-Agent. Respect robots.txt and site terms.