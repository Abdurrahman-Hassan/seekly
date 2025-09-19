from playwright.async_api import async_playwright
from lib.structured_parser import parse_structured_data

async def scrape_daraz(url: str):
    async with async_playwright() as p:
        browser =await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        html = await page.content()
        await browser.close()

    data = parse_structured_data(html)
    if data:
        data["url"] = url
        data["retailer"] = "Daraz"
    return data
