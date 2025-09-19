from providers.olx_selenium_optimized import scrape_olx_fast_selenium, scrape_olx_async
from providers.pakwheels import scrape_pakwheels_search_httpx
import asyncio

def scrape_dynamic(url: str):
    if "olx.com.pk" in url or "olx.com" in url:
        try:
            # Use the optimized synchronous version
            # return scrape_olx_fast_selenium(url, max_pages=3)
            
            # Or use async version for even better performance:
            return asyncio.run(scrape_olx_async(url, max_pages=5))
            
        except Exception as e:
            print(f"Optimized OLX scraping failed: {e}")
            # Fallback to basic method
            return scrape_olx_fast_selenium(url, max_pages=1)
    elif "pakwheels.com" in url:
        return scrape_pakwheels_search_httpx(url)
    else:
        raise ValueError(f"Unsupported website: {url}")