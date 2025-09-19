import httpx
from selectolax.parser import HTMLParser
import json
from urllib.parse import urljoin

def scrape_pakwheels_search_httpx(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            tree = HTMLParser(response.text)

            items = []

            # Each listing card
            listings = tree.css("li.search-listing-card")
            for listing in listings:
                script_tag = listing.css_first("script[type='application/ld+json']")
                if not script_tag:
                    continue

                try:
                    data = json.loads(script_tag.text())
                    # Sometimes JSON-LD is a list, sometimes dict
                    if isinstance(data, list):
                        data = data[0]

                    offer = data.get("offers", {})
                    price = offer.get("price")
                    currency = offer.get("priceCurrency", "PKR")
                    item_url = offer.get("url") or data.get("url")
                    image = data.get("image")
                    title = data.get("name") or data.get("description", "No title available")

                    # Normalize price display
                    if price and currency:
                        if len(str(price)) > 0:
                            if int(price) > 1000000:
                                display_price = f"Rs {int(price)/100000:.2f} Lacs"
                            else:
                                display_price = f"Rs {price}"
                        else:
                            display_price = "Price not available"
                    else:
                        display_price = "Price not available"

                    items.append({
                        "retailer": "PakWheels",
                        "title": title,
                        "price": display_price,
                        "currency": currency,
                        "url": item_url,
                        "image": image
                    })

                except Exception as e:
                    print(f"Error parsing JSON-LD: {e}")
                    continue

            return items

    except Exception as e:
        raise Exception(f"Scraping failed: {str(e)}")
