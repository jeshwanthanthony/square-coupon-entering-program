from playwright.sync_api import sync_playwright
import pandas as pd

CODES_FILE = "codes.csv"

COUPONS_URL = "https://app.squareup.com/dashboard/customers/marketing/coupons"
NEW_COUPON_URL = "https://app.squareup.com/dashboard/customers/marketing/coupons/new"

ITEM_NAME = 'Free Small 10" Pizza'

codes = pd.read_csv(CODES_FILE)["code"].dropna().astype(str).tolist()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        slow_mo=250          # was 500
    )

    page = browser.new_page()
    page.set_default_timeout(20000)   # was 30000

    page.goto(COUPONS_URL)

    input("Log in to Square, stay on the Coupons page, then press ENTER here...")

    for code in codes:
        print(f"Creating coupon: {code}")

        page.goto(NEW_COUPON_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1800)    # was 3000

        # Coupon code
        page.get_by_placeholder("ANNUALSALE1").fill(code)

        # Coupon Type = Free
        page.get_by_text("Free", exact=True).click()
        page.wait_for_timeout(500)     # was 1000

        # Applies To = Specific item
        page.get_by_text("Specific item", exact=True).click()
        page.wait_for_timeout(500)     # was 1000

        # Item dropdown
        page.locator('input[autocomplete="off"]').click()
        page.wait_for_timeout(500)     # was 1000

        page.keyboard.type(ITEM_NAME)
        page.wait_for_timeout(800)     # was 1500

        page.keyboard.press("Enter")
        page.wait_for_timeout(800)     # was 1500

        # Condition 1
        page.get_by_text(
            "Limit number of times customers can use coupon",
            exact=True
        ).click()
        page.wait_for_timeout(500)     # was 1000

        number_inputs = page.locator('input[type="number"]')
        number_inputs.nth(0).fill("1")

        # Condition 2
        page.get_by_text(
            "Limit number of times coupon can be redeemed",
            exact=True
        ).click()
        page.wait_for_timeout(500)     # was 1000

        number_inputs = page.locator('input[type="number"]')
        number_inputs.nth(1).fill("1")

        page.wait_for_timeout(500)     # was 1000

        # Activate
        page.get_by_role("button", name="Activate").click()

        page.wait_for_timeout(3500)    # was 6000

    print("All coupons created.")
    browser.close()