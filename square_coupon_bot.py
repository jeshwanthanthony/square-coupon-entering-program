"""Create Square Marketing coupons from a CSV file."""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


COUPONS_URL = "https://app.squareup.com/dashboard/customers/marketing/coupons"
NEW_COUPON_URL = "https://app.squareup.com/dashboard/customers/marketing/coupons/new"
DEFAULT_ITEM = 'Free Small 10" Pizza'
DEFAULT_TIMEOUT_MS = 20_000

LOGGER = logging.getLogger("square_coupons")


@dataclass(frozen=True)
class Settings:
    """The small set of values that can change between runs."""

    codes_file: Path
    item_name: str
    headless: bool
    slow_mo_ms: int


def read_codes(path: Path) -> list[str]:
    """Read, clean, and validate coupon codes from a CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Coupon file not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or "code" not in reader.fieldnames:
            raise ValueError(f"{path} must contain a column named 'code'")

        codes = [row["code"].strip() for row in reader if row.get("code", "").strip()]

    unique_codes = list(dict.fromkeys(codes))
    if not unique_codes:
        raise ValueError(f"No coupon codes were found in {path}")

    if len(unique_codes) != len(codes):
        LOGGER.info("Ignored %d duplicate code(s).", len(codes) - len(unique_codes))

    return unique_codes


def create_coupon(page: Page, code: str, item_name: str) -> None:
    """Fill out and activate one coupon in Square."""
    page.goto(NEW_COUPON_URL, wait_until="domcontentloaded")

    page.get_by_placeholder("ANNUALSALE1").fill(code)
    page.get_by_text("Free", exact=True).click()
    page.get_by_text("Specific item", exact=True).click()

    item_search = page.locator('input[autocomplete="off"]')
    item_search.click()
    item_search.fill(item_name)
    page.wait_for_timeout(700)
    page.keyboard.press("Enter")

    # Square keeps these options unchecked by default, so set both limits explicitly.
    page.get_by_text(
        "Limit number of times customers can use coupon", exact=True
    ).click()
    page.locator('input[type="number"]').nth(0).fill("1")

    page.get_by_text(
        "Limit number of times coupon can be redeemed", exact=True
    ).click()
    page.locator('input[type="number"]').nth(1).fill("1")

    page.get_by_role("button", name="Activate").click()
    page.wait_for_timeout(1_500)


def run(settings: Settings) -> int:
    """Create all coupons and return a shell-friendly exit code."""
    codes = read_codes(settings.codes_file)
    LOGGER.info("Loaded %d coupon code(s).", len(codes))

    completed: list[str] = []
    failed: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo_ms,
        )
        page = browser.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)

        try:
            page.goto(COUPONS_URL, wait_until="domcontentloaded")
            input("Log in to Square, open the Coupons page, then press Enter here... ")

            for number, code in enumerate(codes, start=1):
                LOGGER.info("Creating coupon %d/%d: %s", number, len(codes), code)
                try:
                    create_coupon(page, code, settings.item_name)
                except PlaywrightTimeoutError:
                    LOGGER.exception("Square timed out while creating %s", code)
                    failed.append(code)
                except Exception:
                    LOGGER.exception("Could not create %s", code)
                    failed.append(code)
                else:
                    completed.append(code)
        finally:
            browser.close()

    LOGGER.info("Finished: %d created, %d failed.", len(completed), len(failed))
    if failed:
        LOGGER.error("Failed codes: %s", ", ".join(failed))
        return 1
    return 0


def parse_args() -> Settings:
    parser = argparse.ArgumentParser(description="Create Square coupons from a CSV file.")
    parser.add_argument(
        "--codes-file", type=Path, default=Path("codes.csv"), help="CSV file with a code column."
    )
    parser.add_argument("--item-name", default=DEFAULT_ITEM, help="Square item the coupon applies to.")
    parser.add_argument("--headless", action="store_true", help="Run without opening a browser window.")
    parser.add_argument("--slow-mo", type=int, default=250, help="Delay browser actions by this many milliseconds.")
    args = parser.parse_args()

    if args.slow_mo < 0:
        parser.error("--slow-mo cannot be negative")

    return Settings(args.codes_file, args.item_name, args.headless, args.slow_mo)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        return run(parse_args())
    except (FileNotFoundError, ValueError) as error:
        LOGGER.error("%s", error)
        return 2
    except KeyboardInterrupt:
        LOGGER.warning("Stopped by user.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
