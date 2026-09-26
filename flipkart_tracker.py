import asyncio
import os
import requests
from playwright.async_api import async_playwright


PRODUCTS = [
    {
        "name": "iPhone 17e Soft Pink 256GB",
        "url": (
            "https://www.flipkart.com/"
            "apple-iphone-17e-soft-pink-256-gb/"
            "p/itm124dbc903758f"
            "?pid=MOBHH2SHDXGYG2EZ"
            "&marketplace=FLIPKART"
        ),
    },
    {
        "name": "iPhone 17e Soft Pink 512GB",
        "url": (
            "https://www.flipkart.com/"
            "apple-iphone-17e-soft-pink-512-gb/"
            "p/itm9ca2e491bc0c9"
            "?pid=MOBHH2SHZCPZZHAP"
            "&marketplace=FLIPKART"
        ),
    },
]

PINCODE = "110041"

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )

    response.raise_for_status()

    print("Telegram notification sent.")


async def check_product(page, product):

    print(f"Checking {product['name']}...")

    await page.goto(
        product["url"],
        wait_until="domcontentloaded",
        timeout=60000,
    )

    await page.wait_for_timeout(5000)

    # Find pincode input
    inputs = page.locator(
        'input[placeholder*="Pincode" i], '
        'input[placeholder*="pincode" i]'
    )

    for i in range(await inputs.count()):

        try:
            box = inputs.nth(i)

            if await box.is_visible():

                await box.fill(PINCODE)
                await box.press("Enter")

                await page.wait_for_timeout(3000)

                break

        except Exception:
            continue

    text = (
        await page.locator("body").inner_text()
    ).lower()

    unavailable_phrases = [
        "currently unavailable",
        "out of stock",
        "sold out",
        "not deliverable",
        "not available at this pincode",
        "delivery not available",
    ]

    available_phrases = [
        "delivery by",
        "get it by",
        "available for delivery",
    ]

    unavailable = any(
        phrase in text
        for phrase in unavailable_phrases
    )

    available = any(
        phrase in text
        for phrase in available_phrases
    )

    if unavailable:
        print(f"NOT AVAILABLE: {product['name']}")
        return False

    if available:
        print(f"AVAILABLE: {product['name']}")
        return True

    print(f"UNKNOWN: {product['name']}")
    return None


async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000,
            }
        )

        for product in PRODUCTS:

            try:

                available = await check_product(
                    page,
                    product,
                )

                if available:

                    send_telegram(
                        "🚨🍎 iPHONE 17e AVAILABLE!\n\n"
                        f"📱 {product['name']}\n"
                        f"📍 Delivery pincode: {PINCODE}\n\n"
                        "🛒 BUY NOW:\n"
                        f"{product['url']}"
                    )

            except Exception as e:

                print(
                    f"Error checking "
                    f"{product['name']}: {e}"
                )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
