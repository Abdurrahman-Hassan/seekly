import json
from bs4 import BeautifulSoup

def parse_structured_data(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # JSON-LD
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("@type") in ["Product", "Offer"]:
                return {
                    "title": data.get("name"),
                    "price": data.get("offers", {}).get("price"),
                    "currency": data.get("offers", {}).get("priceCurrency"),
                    "image": data.get("image"),
                    "retailer": data.get("brand"),
                }
        except Exception:
            continue

    # OG fallback
    og_data = {}
    for meta in soup.find_all("meta"):
        if meta.get("property") and meta.get("content"):
            og_data[meta["property"]] = meta["content"]

    return {
        "title": og_data.get("og:title"),
        "image": og_data.get("og:image"),
        "price": og_data.get("og:price:amount"),
        "currency": og_data.get("og:price:currency"),
        "retailer": og_data.get("og:site_name"),
    }
