import asyncio
import os
import requests
from playwright.async_api import async_playwright


PRODUCTS = [
    {
        "name": "iPhone 17 Sage 256GB",
        "url": "https://www.flipkart.com/apple-iphone-17-sage-256-gb/p/itm410e85a5f1745?pid=MOBHQV9YZPQXFFGM&marketplace=FLIPKART",
    },
    {
        "name": "iPhone 17 Black 256GB",
        "url": "https://www.flipkart.com/apple-iphone-17-black-256-gb/p/itmc61b40459dd98",
    },
    {
        "name": "iPhone 17 White 256GB",
        "url": "https://www.flipkart.com/apple-iphone-17-white-256-gb/p/itm68ad8410784c7",
    },
    {
        "name": "iPhone 17 Mist Blue 256GB",
        "url": "https://www.flipkart.com/apple-iphone-17-mist-blue-256-gb/p/itmfd8c16e287599",
    },
    {
        "name": "iPhone 17 Lavender 256GB",
        "url": "https://www.flipkart.com/apple-iphone-17-lavender-256-gb/p/itm5c650337c09ee",
    },
]
# PRODUCTS = [
#     {
#         "name": "TEST - Klexio Women Heels",
#         "url": (
#             "https://www.flipkart.com/klexio-women-heels/"
#             "p/itm1c8f0bbe8e404"
#             "?pid=SNDHCDB7VMGNBG6Z"
#             "&lid=LSTSNDHCDB7VMGNBG6ZIXKGAM"
#             "&marketplace=FLIPKART"
#         ),
#     },
# ]

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

    print(f"\nChecking {product['name']}...")

    response = await page.goto(
        product["url"],
        wait_until="domcontentloaded",
        timeout=60000,
    )

    await page.wait_for_timeout(7000)

    print("HTTP:", response.status if response else "Unknown")
    print("Title:", await page.title())

    text = (
        await page.locator("body").inner_text()
    ).lower()

    # Detect blocked pages
    if any(x in text for x in [
        "captcha",
        "verify you are human",
        "access denied",
        "unusual traffic",
    ]):
        print("UNKNOWN: Blocked")
        return None

    # Enter pincode if input is available
    inputs = page.locator(
        'input[placeholder*="pincode" i], '
        'input[placeholder*="pin code" i]'
    )

    pincode_entered = False

    for i in range(await inputs.count()):
        try:
            box = inputs.nth(i)

            if await box.is_visible():
                await box.fill(PINCODE)
                await box.press("Enter")

                await page.wait_for_timeout(5000)

                pincode_entered = True
                break

        except Exception:
            continue

    print("Pincode entered:", pincode_entered)

    # Refresh page text after pincode interaction
    text = (
        await page.locator("body").inner_text()
    ).lower()

    # Explicit unavailability
    unavailable_phrases = [
        "currently unavailable",
        "out of stock",
        "sold out",
        "delivery not available",
        "not deliverable",
    ]

    if any(x in text for x in unavailable_phrases):
        print("UNAVAILABLE:", product["name"])
        return False

    # Look for actual purchase buttons
    buy_now = page.get_by_text(
        "Buy Now",
        exact=True
    )

    add_to_cart = page.get_by_text(
        "Add to cart",
        exact=True
    )

    buy_visible = False
    cart_visible = False

    try:
        for i in range(await buy_now.count()):
            if await buy_now.nth(i).is_visible():
                buy_visible = True

        for i in range(await add_to_cart.count()):
            if await add_to_cart.nth(i).is_visible():
                cart_visible = True

    except Exception:
        pass

    delivery_found = any(
        phrase in text
        for phrase in [
            "delivery by",
            "get it by",
            "delivery details",
        ]
    )

    print("Buy Now:", buy_visible)
    print("Add to Cart:", cart_visible)
    print("Delivery information:", delivery_found)

    if buy_visible or cart_visible:
        print("AVAILABLE:", product["name"])
        return True

    print("NOT AVAILABLE:", product["name"])
    return False


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
                        "🚨🍎 iPHONE 17 AVAILABLE!\n\n"
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
