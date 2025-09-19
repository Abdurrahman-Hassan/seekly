import requests
from bs4 import BeautifulSoup

def scrape_pakwheels(query: str, limit: int = 5):
    url = f"https://www.pakwheels.com/used-cars/search/-/q_{query.replace(' ', '-')}/"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    for card in soup.select(".search-page__result")[:limit]:
        title = card.select_one(".car-name").get_text(strip=True) if card.select_one(".car-name") else "N/A"
        price = card.select_one(".price").get_text(strip=True) if card.select_one(".price") else "N/A"
        link = "https://www.pakwheels.com" + card.find("a")["href"]
        image = card.select_one("img")["src"] if card.select_one("img") else None

        results.append({
            "retailer": "PakWheels",
            "title": title,
            "price": price,
            "currency": "PKR",
            "url": link,
            "image": image
        })

    return results
