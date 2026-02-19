#!/usr/bin/env python3
"""agentainer-fetch: Fetch a URL via headless Chromium and extract rendered text.

Usage:
    agentainer-fetch https://example.com
    agentainer-fetch https://example.com --out ./page.md
    agentainer-fetch https://example.com --screenshot ./shot.png
    agentainer-fetch https://example.com --html ./raw.html
"""

import argparse
import sys
import textwrap
from pathlib import Path

from playwright.sync_api import sync_playwright


def fetch_page(
    url: str,
    out_path: str | None = None,
    screenshot_path: str | None = None,
    html_path: str | None = None,
    timeout_ms: int = 30000,
) -> str:
    """Fetch a URL with headless Chromium, return rendered text content."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)

        title = page.title()
        text_content = page.inner_text("body")

        # Optional: save screenshot
        if screenshot_path:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved: {screenshot_path}", file=sys.stderr)

        # Optional: save raw HTML
        if html_path:
            raw_html = page.content()
            Path(html_path).write_text(raw_html, encoding="utf-8")
            print(f"HTML saved: {html_path}", file=sys.stderr)

        browser.close()

    # Format as markdown
    md = f"# {title}\n\nSource: {url}\n\n---\n\n{text_content}\n"

    if out_path:
        Path(out_path).write_text(md, encoding="utf-8")
        print(f"Rendered text saved: {out_path}", file=sys.stderr)
    else:
        print(md)

    return md


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a URL via headless Chromium and extract rendered text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              agentainer-fetch https://example.com
              agentainer-fetch https://example.com --out ./page.md
              agentainer-fetch https://example.com --screenshot ./shot.png
        """),
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--out", "-o", help="Output file for rendered text (markdown)")
    parser.add_argument("--screenshot", "-s", help="Save full-page screenshot")
    parser.add_argument("--html", help="Save raw HTML")
    parser.add_argument(
        "--timeout", type=int, default=30000, help="Page load timeout in ms (default: 30000)"
    )

    args = parser.parse_args()
    fetch_page(
        url=args.url,
        out_path=args.out,
        screenshot_path=args.screenshot,
        html_path=args.html,
        timeout_ms=args.timeout,
    )


if __name__ == "__main__":
    main()
