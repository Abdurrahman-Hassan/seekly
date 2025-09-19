import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import re

def extract_olx_item_v2(card):
    try:
        # Title
        title_tag = card.css_first('div[aria-label="Title"] h2')
        title = title_tag.text().strip() if title_tag else "No title available"

        # Price
        price_tag = card.css_first('div[aria-label="Price"] span')
        price = price_tag.text().strip() if price_tag else "Price not available"

        # URL
        a_tag = card.css_first('a[href*="/item/"]')
        href = a_tag.attributes.get("href") if a_tag else None
        url = urljoin("https://www.olx.com.pk", href) if href else "#"

        # Image
        img_tag = card.css_first('img')
        image_url = img_tag.attributes.get("src") if img_tag else None

        return {
            "retailer": "OLX",
            "title": title,
            "price": price,
            "currency": "PKR",
            "url": url,
            "image": image_url
        }
    except Exception as e:
        print(f"Error extracting item: {e}")
        return None

def scrape_olx_search_httpx(url: str):
    from httpx import Client
    from selectolax.parser import HTMLParser

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    with Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()

        tree = HTMLParser(resp.text)

        # Each item is inside ul._1aad128c > li
        items = []
        product_list = tree.css('ul._1aad128c li[aria-label="Listing"]')
        for li in product_list:
            item = extract_olx_item_v2(li)
            if item:
                items.append(item)

        return items


def extract_olx_item(card, base_url):
    """Extract item information from OLX card"""
    try:
        # Try multiple title selectors
        title_selectors = [
            "[data-aut-id='itemTitle']",
            "h6",
            "h5",
            "h4",
            ".title",
            "[aria-label*='title']",
            "span[class*='title']",
            "div[class*='title']"
        ]
        
        title = None
        for selector in title_selectors:
            title_tag = card.css_first(selector)
            if title_tag and title_tag.text().strip():
                title = title_tag.text().strip()
                break
        
        # Try multiple price selectors
        price_selectors = [
            "[data-aut-id='itemPrice']",
            "[class*='price']",
            "[aria-label*='price']",
            "span[class*='price']",
            "div[class*='price']",
            "b",
            "strong"
        ]
        
        price = None
        for selector in price_selectors:
            price_tag = card.css_first(selector)
            if price_tag and price_tag.text().strip():
                price_text = price_tag.text().strip()
                # Clean price text
                price = re.sub(r'\s+', ' ', price_text)
                break
        
        # Get URL
        href = card.attributes.get('href', '')
        if href and not href.startswith(('http://', 'https://')):
            url = urljoin("https://www.olx.com.pk", href)
        else:
            url = href
        
        # Get image
        image_selectors = ["img", "source", "[data-src]", "[src]"]
        image_url = None
        for selector in image_selectors:
            img_tag = card.css_first(selector)
            if img_tag:
                image_url = img_tag.attributes.get('src') or img_tag.attributes.get('data-src')
                if image_url:
                    break
        
        return {
            "retailer": "OLX",
            "title": title or "No title available",
            "price": price or "Price not available",
            "currency": "PKR",
            "url": url or "#",
            "image": image_url
        }
        
    except Exception as e:
        print(f"Error extracting item: {e}")
        return None

def extract_from_generic_link(link):
    """Extract from generic link when specific selectors fail"""
    try:
        title = link.text().strip()
        if not title or len(title) < 5:  # Skip very short titles
            return None
            
        # Get parent or nearby elements for price
        parent = link.parent
        price = None
        if parent:
            # Look for price elements near the link
            price_elements = parent.css('[class*="price"], [aria-label*="price"], b, strong, span')
            for elem in price_elements:
                text = elem.text().strip()
                if text and any(char.isdigit() for char in text):
                    price = text
                    break
        
        href = link.attributes.get('href', '')
        url = urljoin("https://www.olx.com.pk", href) if href else "#"
        
        return {
            "retailer": "OLX",
            "title": title,
            "price": price or "Price not available",
            "currency": "PKR",
            "url": url,
            "image": None
        }
        
    except Exception as e:
        print(f"Error in generic extraction: {e}")
        return None