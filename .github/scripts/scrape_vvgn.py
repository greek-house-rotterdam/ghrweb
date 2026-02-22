#!/usr/bin/env python3
"""Scrape public content from vvgn.eu and export structured data.

Usage:
    python .github/scripts/scrape_vvgn.py
    python .github/scripts/scrape_vvgn.py --start-url https://vvgn.eu/nl/ --max-pages 1200
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

DEFAULT_START_URL = "https://vvgn.eu/nl/"
DEFAULT_OUTPUT_DIR = Path("data/scrapes/vvgn")
USER_AGENT = "ghrweb-scraper/1.0 (+https://github.com/greek-house-rotterdam/ghrweb)"
SKIP_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".rar",
    ".tar",
    ".gz",
    ".mp3",
    ".wav",
    ".ogg",
    ".mp4",
    ".webm",
    ".avi",
    ".mov",
    ".css",
    ".js",
    ".xml",
    ".json",
}


@dataclass(slots=True)
class CrawlResult:
    url: str
    status: int
    ok: bool
    error: str | None = None


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower() if parsed.scheme else "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
        last_segment = path.rsplit("/", maxsplit=1)[-1]
        if "." not in last_segment:
            path = f"{path}/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def should_skip(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host not in allowed_hosts:
        return True
    lowered_path = parsed.path.lower()
    if any(
        marker in lowered_path
        for marker in ("/feed", "/wp-json", "/xmlrpc.php", "/wp-content/uploads/")
    ):
        return True
    return any(lowered_path.endswith(ext) for ext in SKIP_EXTENSIONS)


def extract_links(current_url: str, soup: BeautifulSoup) -> Iterable[str]:
    link_nodes = soup.select(
        "article a[href], main a[href], .post a[href], .entry-content a[href], "
        "nav.pagination a[href], .nav-links a[href], .page-numbers[href]"
    )
    if not link_nodes:
        link_nodes = soup.select("a[href]")
    for a_tag in link_nodes:
        href = a_tag.get("href", "").strip()
        if not href:
            continue
        yield normalize_url(urljoin(current_url, href))


def safe_text(node: BeautifulSoup | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def select_content_node(soup: BeautifulSoup) -> BeautifulSoup:
    for selector in ("article", "main", "#content", ".site-content", "body"):
        node = soup.select_one(selector)
        if node:
            return node
    return soup


def extract_record(url: str, soup: BeautifulSoup, fetched_at: str) -> dict:
    content_node = select_content_node(soup)
    title = (
        safe_text(soup.select_one("meta[property='og:title']"))
        or safe_text(soup.select_one("h1"))
        or safe_text(soup.select_one("title"))
    )
    time_node = soup.select_one("time[datetime]")
    published_at = time_node.get("datetime", "").strip() if time_node else ""
    categories = sorted(
        {
            a.get_text(strip=True)
            for a in soup.select("a[rel~='category']")
            if a.get_text(strip=True)
        }
    )
    media_urls = sorted(
        {
            normalize_url(urljoin(url, img.get("src", "").strip()))
            for img in content_node.select("img[src]")
            if img.get("src", "").strip()
        }
    )
    language = (soup.html.get("lang", "") if soup.html else "").strip()

    return {
        "url": url,
        "title": title,
        "language": language,
        "published_at": published_at,
        "categories": categories,
        "fetched_at": fetched_at,
        "body_text": safe_text(content_node),
        "body_html": str(content_node),
        "media_urls": media_urls,
    }


def filename_for_url(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"{digest}.json"


def write_report(
    output_dir: Path,
    started_at: str,
    finished_at: str,
    max_pages: int,
    delay_seconds: float,
    results: list[CrawlResult],
    records_count: int,
) -> None:
    successes = [r for r in results if r.ok]
    failures = [r for r in results if not r.ok]
    report_path = output_dir / "crawl-report.md"
    report_lines = [
        "# VVGN Crawl Report",
        "",
        f"- Started at: `{started_at}`",
        f"- Finished at: `{finished_at}`",
        f"- Max pages: `{max_pages}`",
        f"- Delay between requests (s): `{delay_seconds}`",
        f"- URLs fetched: `{len(results)}`",
        f"- Successful fetches: `{len(successes)}`",
        f"- Failed fetches: `{len(failures)}`",
        f"- Records exported: `{records_count}`",
        "",
        "## Failures",
        "",
    ]
    if not failures:
        report_lines.append("- None")
    else:
        for failure in failures:
            report_lines.append(
                f"- `{failure.status}` {failure.url} ({failure.error or 'request failed'})"
            )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")


def crawl_site(
    start_url: str,
    output_dir: Path,
    max_pages: int,
    delay_seconds: float,
    timeout_seconds: float,
    retries: int,
) -> None:
    started_at = datetime.now(UTC).isoformat()
    start_url = normalize_url(start_url)
    parsed_start = urlparse(start_url)
    start_host = parsed_start.netloc.lower()
    if start_host.startswith("www."):
        start_host = start_host[4:]
    allowed_hosts = {start_host}

    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    queue: deque[str] = deque([start_url])
    enqueued: set[str] = {start_url}
    seen: set[str] = set()
    results: list[CrawlResult] = []
    records_count = 0

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    while queue and len(seen) < max_pages:
        current_url = queue.popleft()
        if current_url in seen or should_skip(current_url, allowed_hosts):
            continue

        seen.add(current_url)
        try:
            response = None
            for attempt in range(1, retries + 1):
                try:
                    response = session.get(current_url, timeout=timeout_seconds)
                    break
                except requests.RequestException:
                    if attempt == retries:
                        raise
                    time.sleep(0.8 * attempt)

            if response is None:
                raise RuntimeError("request retries exhausted")
            status = response.status_code
            if status != 200:
                results.append(
                    CrawlResult(url=current_url, status=status, ok=False, error="non-200")
                )
                time.sleep(delay_seconds)
                continue

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                results.append(
                    CrawlResult(
                        url=current_url,
                        status=status,
                        ok=False,
                        error=f"unsupported content-type: {content_type}",
                    )
                )
                time.sleep(delay_seconds)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            fetched_at = datetime.now(UTC).isoformat()
            record = extract_record(current_url, soup, fetched_at)
            (records_dir / filename_for_url(current_url)).write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            records_count += 1
            results.append(CrawlResult(url=current_url, status=status, ok=True))

            for link in extract_links(current_url, soup):
                if (
                    link not in seen
                    and link not in enqueued
                    and not should_skip(link, allowed_hosts)
                ):
                    queue.append(link)
                    enqueued.add(link)
        except Exception as exc:
            results.append(
                CrawlResult(url=current_url, status=0, ok=False, error=str(exc))
            )
        finally:
            if len(seen) % 25 == 0:
                print(
                    f"Progress: seen={len(seen)} exported={records_count} queue={len(queue)}"
                )
            time.sleep(delay_seconds)

    manifest = {
        "start_url": start_url,
        "generated_at": datetime.now(UTC).isoformat(),
        "max_pages": max_pages,
        "delay_seconds": delay_seconds,
        "total_seen": len(seen),
        "records_count": records_count,
        "results": [asdict(result) for result in results],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(
        output_dir=output_dir,
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
        max_pages=max_pages,
        delay_seconds=delay_seconds,
        results=results,
        records_count=records_count,
    )

    print(f"Scrape complete. Exported {records_count} records.")
    print(f"Output directory: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape vvgn.eu content")
    parser.add_argument("--start-url", default=DEFAULT_START_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-pages", type=int, default=1500)
    parser.add_argument("--delay-seconds", type=float, default=0.4)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    crawl_site(
        start_url=args.start_url,
        output_dir=args.output_dir,
        max_pages=args.max_pages,
        delay_seconds=args.delay_seconds,
        timeout_seconds=args.timeout_seconds,
        retries=args.retries,
    )


if __name__ == "__main__":
    main()
