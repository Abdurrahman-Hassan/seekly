import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse, urlencode
import re
import time

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

def scrape_olx_search_httpx(url: str, max_pages: int = 3):
    """Scrape OLX with proper pagination support"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    all_items = []
    current_page = get_current_page_number(url)
    
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for page_num in range(current_page, current_page + max_pages):
            try:
                print(f"Scraping page {page_num}...")
                
                # Create URL for this page
                page_url = create_page_url(url, page_num)
                
                resp = client.get(page_url, headers=headers)
                resp.raise_for_status()

                tree = HTMLParser(resp.text)
                
                # Check if we got a valid response with products
                product_list = tree.css('ul._1aad128c li[aria-label="Listing"]')
                
                if not product_list:
                    print("No products found on this page, stopping pagination.")
                    break
                
                print(f"Found {len(product_list)} products on page {page_num}")
                
                for li in product_list:
                    item = extract_olx_item_v2(li)
                    if item:
                        # Check for duplicates by URL
                        if not any(existing_item['url'] == item['url'] for existing_item in all_items):
                            all_items.append(item)
                
                # Check if there are more pages by looking for next button
                next_button = tree.css_first('a[data-testid="pagination-forward"]')
                if not next_button and page_num < (current_page + max_pages - 1):
                    # Also check for disabled next button (indicating last page)
                    disabled_next = tree.css_first('button[data-testid="pagination-forward"][disabled]')
                    if disabled_next:
                        print("Reached the last page, stopping pagination.")
                        break
                
                time.sleep(1)  # Be polite with delays between requests
                
            except Exception as e:
                print(f"Error scraping page {page_num}: {e}")
                break

    return all_items

def get_current_page_number(url: str) -> int:
    """Extract current page number from URL"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    page_param = query_params.get('page', ['1'])
    try:
        return int(page_param[0])
    except (ValueError, IndexError):
        return 1

def create_page_url(base_url: str, page: int) -> str:
    """Create URL for specific page number"""
    parsed_url = urlparse(base_url)
    query_params = parse_qs(parsed_url.query)
    
    # Update page parameter
    query_params['page'] = [str(page)]
    
    # Rebuild query string
    new_query = urlencode(query_params, doseq=True)
    
    # Reconstruct URL
    return urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))

def scrape_olx_search_api(url: str, max_items: int = 50):
    """API-based approach for OLX with pagination"""
    try:
        # Extract search parameters from URL
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        search_query = query_params.get('q', [''])[0]
        category = extract_category_from_url(parsed_url.path)
        
        # Determine page number
        page_num = get_current_page_number(url)
        
        api_url = "https://www.olx.com.pk/api/relevance/v4/search"
        params = {
            'category': category,
            'facet_limit': '100',
            'lang': 'en',
            'location': '1000001',  # Pakistan
            'location_facet_limit': '20',
            'page': str(page_num - 1),  # API uses 0-based indexing
            'query': search_query,
            'spellcheck': 'true',
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': url,
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            items = []
            
            for item in data.get('data', [])[:max_items]:
                title = item.get('title', 'No title available')
                price_info = item.get('price', {})
                price = price_info.get('value', {}).get('display', 'Price not available')
                
                items.append({
                    "retailer": "OLX",
                    "title": title,
                    "price": price,
                    "currency": "PKR",
                    "url": f"https://www.olx.com.pk{item.get('url', '')}",
                    "image": item.get('images', [{}])[0].get('url') if item.get('images') else None
                })
            
            return items
            
    except Exception as e:
        print(f"API method failed: {e}")
        # Fallback to HTML scraping for single page
        return scrape_olx_search_httpx(url, max_pages=1)

def extract_category_from_url(path: str) -> str:
    """Extract category from URL path"""
    # Example: /spare-parts_c82/ -> '82'
    category_match = re.search(r'_c(\d+)', path)
    if category_match:
        return category_match.group(1)
    return 'all'

def scrape_olx_search(url: str, max_pages: int = 3):
    """Main OLX scraping function"""
    print(f"Scraping OLX URL: {url}")
    
    # For single page requests, try API first
    if get_current_page_number(url) == 1:
        try:
            print("Trying API method...")
            api_results = scrape_olx_search_api(url)
            if api_results:
                print(f"API returned {len(api_results)} items")
                return api_results
        except Exception as api_error:
            print(f"API method failed: {api_error}")
    
    # Fallback to HTML scraping with pagination
    print("Using HTML method with pagination...")
    return scrape_olx_search_httpx(url, max_pages=max_pages)