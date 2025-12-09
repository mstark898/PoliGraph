#!/usr/bin/env python3
"""
Chrome Web Store Disclosure Scraper

Uses Playwright to scrape developer disclosure text from Chrome Web Store
extension pages. This is useful for getting the latest disclosure text
for extensions.

Usage:
    python disclosure_scraper.py --extension-id kbfnbcaeplbcioakkpcpgfkobkghlhen
    python disclosure_scraper.py --all
"""

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def scrape_disclosure(extension_id: str, headless: bool = True) -> Optional[dict]:
    """
    Scrape the developer disclosure from a Chrome Web Store extension page.

    Args:
        extension_id: Chrome extension ID
        headless: Run browser in headless mode

    Returns:
        Dictionary with extension info and disclosure text, or None on failure
    """
    url = f"https://chromewebstore.google.com/detail/{extension_id}"

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        )
        page = await context.new_page()

        try:
            print(f"Loading: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for the page to load
            await page.wait_for_timeout(2000)

            # Get extension name
            name_element = await page.query_selector("h1")
            extension_name = await name_element.inner_text() if name_element else "Unknown"

            # Click on "Privacy practices" tab/section if it exists
            privacy_link = await page.query_selector('text="Privacy practices"')
            if privacy_link:
                await privacy_link.click()
                await page.wait_for_timeout(1000)

            # Try to find privacy disclosure content
            # The Chrome Web Store uses various selectors
            disclosure_text = ""

            # Try different selectors that might contain privacy info
            selectors = [
                '[class*="privacy"]',
                '[class*="disclosure"]',
                'section:has-text("Privacy practices")',
                'div:has-text("handles the following")',
            ]

            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        text = await el.inner_text()
                        if "handles the following" in text or "developer declares" in text:
                            if len(text) > len(disclosure_text):
                                disclosure_text = text
                except Exception:
                    continue

            # If still no luck, get the full page text and extract relevant sections
            if not disclosure_text:
                full_text = await page.inner_text("body")

                # Look for the privacy section
                if "Privacy practices" in full_text:
                    # Extract from "Privacy practices" to end of declarations
                    start = full_text.find("Privacy practices")
                    end = full_text.find("lending purposes", start)
                    if end > start:
                        disclosure_text = full_text[start:end + len("lending purposes")]

            # Navigate to privacy policy page for URL
            privacy_policy_url = ""
            try:
                privacy_url = f"{url}/privacy"
                await page.goto(privacy_url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1000)

                # Look for external privacy policy link
                links = await page.query_selector_all('a[href*="privacy"]')
                for link in links:
                    href = await link.get_attribute("href")
                    if href and not "chromewebstore" in href:
                        privacy_policy_url = href
                        break
            except Exception:
                pass

            await browser.close()

            return {
                "extension_id": extension_id,
                "extension_name": extension_name.strip(),
                "disclosure_text": disclosure_text.strip(),
                "privacy_policy_url": privacy_policy_url,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

        except PlaywrightTimeout:
            print(f"Timeout loading {url}")
            await browser.close()
            return None
        except Exception as e:
            print(f"Error scraping {extension_id}: {e}")
            await browser.close()
            return None


async def scrape_multiple(extension_ids: list, output_file: Optional[str] = None,
                          headless: bool = True) -> list:
    """
    Scrape disclosures for multiple extensions.

    Args:
        extension_ids: List of extension IDs to scrape
        output_file: Optional path to save results as JSON
        headless: Run browser in headless mode

    Returns:
        List of scrape results
    """
    results = []

    for ext_id in extension_ids:
        print(f"\nScraping: {ext_id}")
        result = await scrape_disclosure(ext_id, headless=headless)
        if result:
            results.append(result)
            print(f"  Name: {result['extension_name']}")
            print(f"  Disclosure length: {len(result['disclosure_text'])} chars")
        else:
            print(f"  Failed to scrape")

        # Be polite - wait between requests
        await asyncio.sleep(2)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Chrome Web Store developer disclosures"
    )
    parser.add_argument(
        "--extension-id", "-e",
        type=str,
        help="Single extension ID to scrape"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Scrape all configured extensions"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="scraped_disclosures.json",
        help="Output JSON file"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible window (for debugging)"
    )

    args = parser.parse_args()

    if args.extension_id:
        result = asyncio.run(scrape_disclosure(
            args.extension_id,
            headless=not args.no_headless
        ))
        if result:
            print(json.dumps(result, indent=2))

    elif args.all:
        from extension_privacy_analysis.extensions_data import EXTENSIONS
        ext_ids = [e.extension_id for e in EXTENSIONS]

        asyncio.run(scrape_multiple(
            ext_ids,
            output_file=args.output,
            headless=not args.no_headless
        ))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
