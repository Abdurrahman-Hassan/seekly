from providers.olx import scrape_olx_search_httpx
from providers.pakwheels import scrape_pakwheels_search_httpx

def scrape_dynamic(url: str):
    if "olx.com.pk" in url or "olx.com" in url:
        return scrape_olx_search_httpx(url)
    elif "pakwheels.com" in url:
        return scrape_pakwheels_search_httpx(url)
    else:
        raise ValueError(f"Unsupported website: {url}")
