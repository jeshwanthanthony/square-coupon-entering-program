# Square Coupon Entering Program 🍕

I got tired of entering coupons into Square one by one. Square is great, but it doesn't offer the little API I needed for this job—so I made one with a browser instead.

This script opens Square Marketing, lets you log in normally, and then enters a batch of coupon codes for a specific item. It is intentionally small, transparent, and easy to tweak when Square changes a label or page layout.

## What it does

- Reads coupon codes from a local CSV file.
- Removes blank and duplicate codes before starting.
- Opens a visible Chromium browser so you can log in yourself.
- Creates free, single-use coupons for one selected Square item.
- Reports successes and failures at the end instead of silently losing track.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Create `codes.csv` next to the script:

```csv
code
PIZZA10
FREECHEESE
THANKYOU25
```

## Run it

```bash
python square_coupon_bot.py
```

The browser opens on Square's Coupons page. Log in, open the Coupons page if needed, and press Enter in the terminal. The default item is `Free Small 10" Pizza`.

Useful options:

```bash
python square_coupon_bot.py --codes-file my-codes.csv
python square_coupon_bot.py --item-name "Large Cheese Pizza"
python square_coupon_bot.py --slow-mo 500
```

## A few important notes

This is browser automation, not an official Square integration. Keep an eye on the first run and check the created coupons in Square before sending them to customers. If Square changes its interface, the text selectors in `square_coupon_bot.py` may need an update.

Never commit `codes.csv`, browser profiles, Square credentials, or customer data. Those files are ignored by Git in this project.

## License

Use it, improve it, and save yourself from a little repetitive clicking.
