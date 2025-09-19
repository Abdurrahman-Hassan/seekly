from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selectolax.parser import HTMLParser
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

def setup_driver():
    """Setup Chrome driver with optimized settings"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1200,800")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-javascript")  # Try without JS first
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Performance optimizations
    chrome_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.cookies": 2,
        "profile.managed_default_content_settings.javascript": 2,  # Disable JS initially
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    })
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_olx_fast_selenium(url: str, max_pages: int = 3):
    """Optimized OLX scraper with faster loading"""
    driver = setup_driver()
    all_items = []
    current_page = get_current_page_number(url)
    
    try:
        # First try without JavaScript (much faster)
        try:
            print("Trying without JavaScript...")
            items_no_js = scrape_without_javascript(url, driver)
            if items_no_js:
                print(f"Found {len(items_no_js)} items without JavaScript")
                return items_no_js
        except Exception as e:
            print(f"No-JS approach failed: {e}")
        
        # If no-JS failed, enable JavaScript and try properly
        print("Enabling JavaScript for dynamic content...")
        driver.quit()
        driver = setup_driver()
        # Re-enable JavaScript by updating preferences
        driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': False})
        
        for page_num in range(current_page, current_page + max_pages):
            try:
                print(f"Scraping page {page_num}...")
                
                page_url = create_page_url(url, page_num)
                driver.get(page_url)
                
                # Smart wait - check if products are loaded quickly
                products = smart_wait_for_products(driver, timeout=8)
                
                if not products:
                    print("No products found, stopping.")
                    break
                
                # Extract items quickly
                html = driver.page_source
                items = extract_items_from_html(html)
                print(f"Found {len(items)} items on page {page_num}")
                
                # Add unique items
                for item in items:
                    if item and not any(existing_item['url'] == item['url'] for existing_item in all_items):
                        all_items.append(item)
                
                # Quick check for next page
                if not has_next_page(driver) and page_num < (current_page + max_pages - 1):
                    print("No more pages available.")
                    break
                
                # Minimal delay between pages
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                break
                
    finally:
        driver.quit()
    
    return all_items

def scrape_without_javascript(url: str, driver):
    """Try to scrape without JavaScript (much faster)"""
    driver.get(url)
    time.sleep(2)  # Minimal wait
    
    html = driver.page_source
    tree = HTMLParser(html)
    
    items = []
    product_list = tree.css('ul._1aad128c li[aria-label="Listing"]')
    
    for li in product_list:
        item = extract_olx_item_optimized(li)
        if item:
            items.append(item)
    
    return items

def smart_wait_for_products(driver, timeout=10):
    """Smart waiting for products to load"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Quick check for products
            products = driver.find_elements(By.CSS_SELECTOR, 'ul._1aad128c li[aria-label="Listing"]')
            if products:
                return products
            
            # Check if page is still loading
            loading_indicators = driver.find_elements(By.CSS_SELECTOR, '[data-testid="loading"], .loading, .spinner')
            if not loading_indicators:
                # No loading indicators, probably content is loaded
                return driver.find_elements(By.CSS_SELECTOR, 'ul._1aad128c li[aria-label="Listing"]')
            
            time.sleep(0.3)
        except:
            time.sleep(0.3)
    
    return driver.find_elements(By.CSS_SELECTOR, 'ul._1aad128c li[aria-label="Listing"]')

def extract_items_from_html(html):
    """Quick extraction from HTML"""
    tree = HTMLParser(html)
    items = []
    
    product_list = tree.css('ul._1aad128c li[aria-label="Listing"]')
    for li in product_list:
        item = extract_olx_item_optimized(li)
        if item:
            items.append(item)
    
    return items

def extract_olx_item_optimized(card):
    """Optimized item extraction"""
    try:
        # Fast selectors
        title_tag = card.css_first('div[aria-label="Title"] h2, [data-aut-id="itemTitle"]')
        price_tag = card.css_first('div[aria-label="Price"] span, [data-aut-id="itemPrice"]')
        a_tag = card.css_first('a[href*="/item/"]')
        img_tag = card.css_first('img')
        
        title = title_tag.text().strip() if title_tag else "No title"
        price = price_tag.text().strip() if price_tag else "Price not available"
        href = a_tag.attributes.get("href") if a_tag else None
        url = f"https://www.olx.com.pk{href}" if href else "#"
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
        return None

def has_next_page(driver):
    """Quick check for next page"""
    try:
        next_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-testid="pagination-forward"]:not([disabled])')
        return len(next_buttons) > 0
    except:
        return False

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
    
    query_params['page'] = [str(page)]
    new_query = urlencode(query_params, doseq=True)
    
    return urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))

# Async version for even better performance
async def scrape_olx_async(url: str, max_pages: int = 3):
    """Async version for better performance"""
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor() as executor:
        results = []
        current_page = get_current_page_number(url)
        
        # Scrape pages concurrently
        for page_num in range(current_page, current_page + max_pages):
            page_url = create_page_url(url, page_num)
            results.append(
                loop.run_in_executor(
                    executor, 
                    scrape_single_page_fast, 
                    page_url
                )
            )
        
        # Wait for all pages to complete
        all_items = []
        for future in results:
            try:
                items = await future
                for item in items:
                    if item and not any(existing_item['url'] == item['url'] for existing_item in all_items):
                        all_items.append(item)
            except Exception as e:
                print(f"Error scraping page: {e}")
        
        return all_items

def scrape_single_page_fast(url: str):
    """Scrape a single page quickly"""
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(2)  # Reduced wait time
        
        html = driver.page_source
        return extract_items_from_html(html)
    finally:
        driver.quit()