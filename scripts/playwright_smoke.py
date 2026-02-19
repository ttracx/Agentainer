"""Playwright headless Chromium smoke test."""

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com", wait_until="domcontentloaded")
        print("TITLE:", page.title())
        browser.close()


if __name__ == "__main__":
    main()
