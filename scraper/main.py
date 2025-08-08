import argparse
import csv
import sys
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

import yaml
from bs4 import BeautifulSoup

from .utils import create_session, fetch_html, normalize_whitespace, rate_limit_sleep


@dataclass
class TargetConfig:
    url: str
    item_selector: str
    name_selector: Optional[str]
    link_selector: Optional[str]
    extra_fields: Optional[List[str]]
    delay_seconds: float
    mode: str = "simple"


def parse_config(path: str) -> TargetConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return TargetConfig(
        url=data["url"],
        item_selector=data["selectors"]["item"],
        name_selector=data["selectors"].get("name"),
        link_selector=data["selectors"].get("link"),
        extra_fields=data.get("extra_fields", []),
        delay_seconds=float(data.get("delay_seconds", 0.0)),
        mode=str(data.get("mode", "simple")),
    )


def extract_text(element, selector: Optional[str]) -> str:
    if not selector:
        return ""
    node = element.select_one(selector)
    return normalize_whitespace(node.get_text(" ") if node else "")


def extract_link(element, selector: Optional[str]) -> str:
    if not selector:
        return ""
    node = element.select_one(selector)
    if not node:
        return ""
    href = node.get("href")
    return normalize_whitespace(href or "")


def scrape(config_path: str, output_csv: str) -> None:
    config = parse_config(config_path)
    session = create_session()
    html = fetch_html(session, config.url)
    soup = BeautifulSoup(html, "lxml")

    rows: List[dict] = []
    if config.mode == "simple":
        for item in soup.select(config.item_selector):
            name = extract_text(item, config.name_selector)
            link = extract_link(item, config.link_selector)
            if link and not link.startswith("http"):
                link = urljoin(config.url, link)
            row = {"name": name, "link": link}
            rows.append(row)
    elif config.mode == "ses_affiliates":
        # Heuristic: affiliate sections contain a heading and a CTA button with text including 'Visit website' or 'View website'
        main = soup.select_one("main") or soup
        for cta in main.select("a.btn"):
            btn_text = normalize_whitespace(cta.get_text(" "))
            if "visit website" in btn_text.lower() or "view website" in btn_text.lower():
                # climb up to the container with heading
                container = cta
                for _ in range(6):
                    container = container.parent
                    if container is None:
                        break
                    heading = container.select_one("h2, h3, .teaser__title, .card__title")
                    if heading:
                        name = normalize_whitespace(heading.get_text(" "))
                        link = normalize_whitespace(cta.get("href") or "")
                        rows.append({"name": name, "link": link})
                        break
    else:
        raise ValueError(f"Unknown mode: {config.mode}")

    # CSV headers
    fieldnames = ["name", "link"]
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    rate_limit_sleep(config.delay_seconds)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Config-driven HTML scraper to CSV")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--out", required=True, help="Path to output CSV file")
    args = parser.parse_args(argv)

    try:
        scrape(args.config, args.out)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())