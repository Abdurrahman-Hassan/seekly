from playwright.sync_api import sync_playwright

def scrape_olx(query: str, limit: int = 5):
    url = f"https://www.olx.com.pk/items/q-{query.replace(' ', '-')}"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)  # wait for JS to load

        items = page.query_selector_all("li._7e3920c1")
        for item in items[:limit]:
            title = item.query_selector("._2tW1I") or None
            price = item.query_selector("._89yzn") or None
            link = item.query_selector("a") or None
            image = item.query_selector("img") or None

            results.append({
                "retailer": "OLX",
                "title": title.inner_text() if title else "N/A",
                "price": price.inner_text() if price else "N/A",
                "currency": "PKR",
                "url": link.get_attribute("href") if link else None,
                "image": image.get_attribute("src") if image else None
            })

        browser.close()

    return results
