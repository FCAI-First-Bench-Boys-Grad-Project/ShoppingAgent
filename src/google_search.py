# Improved Google URL Scraper with better compatibility
import asyncio
import nest_asyncio
from playwright.async_api import async_playwright
import random
from typing import List, Optional
import time

# Enable nested event loops for Jupyter
nest_asyncio.apply()

class GoogleURLScraper:
    def __init__(self, headless=True, locale='en-US', region='US'):
        self.headless = headless
        self.locale = locale
        self.region = region
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # More robust browser launch options
        launch_options = {
            'headless': self.headless,
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--disable-extensions',
                '--disable-default-apps'
            ]
        }
        
        try:
            self.browser = await self.playwright.chromium.launch(**launch_options)
        except Exception as e:
            print(f"Failed to launch Chromium: {e}")
            print("Trying with Firefox...")
            self.browser = await self.playwright.firefox.launch(headless=self.headless)
        
        # Set up context with locale and region
        context_options = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': self.locale,
            'timezone_id': 'America/New_York' if self.region == 'US' else 'UTC',
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060} if self.region == 'US' else None,
            'permissions': ['geolocation'] if self.region == 'US' else []
        }
        
        self.context = await self.browser.new_context(**context_options)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def handle_cookie_consent(self, page):
        """Handle various cookie consent dialogs"""
        cookie_selectors = [
            '#L2AGLb',  # "I agree" button
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("OK")',
            '[aria-label*="Accept"]',
            '[data-ved] button:has-text("Accept")',
            'button[jsname]:has-text("Accept")'
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_btn = await page.wait_for_selector(selector, timeout=2000)
                if cookie_btn:
                    await cookie_btn.click()
                    await asyncio.sleep(1)
                    print("Accepted cookies")
                    return True
            except:
                continue
        return False
    
    async def perform_search(self, page, query: str) -> bool:
        """Perform the search with multiple fallback strategies"""
        search_strategies = [
            # Strategy 1: Standard search input
            {
                'url': 'https://www.google.com',
                'selectors': ['input[name="q"]', 'textarea[name="q"]', 'input[title="Search"]']
            },
            # Strategy 2: Direct search URL
            {
                'url': f'https://www.google.com/search?q={query.replace(" ", "+")}',
                'selectors': []
            },
            # Strategy 3: Different Google domain
            {
                'url': 'https://google.com',
                'selectors': ['input[name="q"]', 'textarea[name="q"]']
            }
        ]
        
        for strategy in search_strategies:
            try:
                print(f"Trying strategy: {strategy['url']}")
                await page.goto(strategy['url'], wait_until='networkidle', timeout=15000)
                await asyncio.sleep(random.uniform(1, 3))
                
                # Handle cookie consent
                await self.handle_cookie_consent(page)
                
                # If no selectors, we used direct search URL
                if not strategy['selectors']:
                    return True
                
                # Try to find and use search input
                search_input = None
                for selector in strategy['selectors']:
                    try:
                        search_input = await page.wait_for_selector(selector, timeout=5000)
                        if search_input:
                            break
                    except:
                        continue
                
                if search_input:
                    await search_input.click()
                    await search_input.fill(query)
                    await page.keyboard.press('Enter')
                    return True
                    
            except Exception as e:
                print(f"Strategy failed: {e}")
                continue
        
        return False
    
    async def wait_for_results(self, page) -> bool:
        """Wait for search results with multiple selectors"""
        result_selectors = [
            'div#search',
            'div#rso', 
            '#search',
            'div[id="search"]',
            '[data-ved]:has(h3)',
            '.g:has(h3)'
        ]
        
        for selector in result_selectors:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                print(f"Results loaded with selector: {selector}")
                return True
            except:
                continue
        
        print("Warning: Could not confirm results loaded, proceeding anyway...")
        return False
    
    async def extract_urls(self, page, max_results: int) -> List[str]:
        """Extract URLs with comprehensive selectors"""
        urls = []
        
        # Wait a bit for page to fully load
        await asyncio.sleep(2)
        
        # Multiple container strategies
        container_strategies = [
            'div.g:has(h3)',
            'div[data-ved]:has(h3)',
            '.g:has(a h3)',
            'div.tF2Cxc',
            '[jscontroller]:has(h3)',
            'div:has(h3 a)',
            '[data-ved] div:has(h3)',
            'div.yuRUbf',  # Another Google format
            'div.kvH3mc'   # Yet another format
        ]
        
        result_containers = []
        for selector in container_strategies:
            try:
                containers = await page.query_selector_all(selector)
                if containers and len(containers) >= 3:  # Ensure we have meaningful results
                    result_containers = containers
                    print(f"Found {len(containers)} containers with: {selector}")
                    break
            except Exception as e:
                print(f"Container selector '{selector}' failed: {e}")
                continue
        
        if not result_containers:
            print("No containers found, trying alternative extraction...")
            # Fallback: look for any links with h3 elements
            try:
                all_links = await page.query_selector_all('a[href^="http"]:has(h3)')
                result_containers = all_links[:max_results * 2]  # Get more to filter
                print(f"Fallback found {len(result_containers)} potential links")
            except:
                return []
        
        # Extract URLs from containers
        for i, container in enumerate(result_containers[:max_results * 3]):  # Process more to get enough valid ones
            if len(urls) >= max_results:
                break
                
            try:
                link_selectors = [
                    'h3 a',
                    'a:has(h3)', 
                    'a[href^="http"]:has(h3)',
                    'a[jsname]',
                    'a[data-ved]',
                    'a:first-child'
                ]
                
                link_element = None
                for selector in link_selectors:
                    try:
                        link_element = await container.query_selector(selector)
                        if link_element:
                            break
                    except:
                        continue
                
                if link_element:
                    url = await link_element.get_attribute('href')
                    if self.is_valid_url(url):
                        urls.append(url)
                        print(f"Extracted URL {len(urls)}: {url[:80]}...")
                        
            except Exception as e:
                continue
        
        return urls[:max_results]
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not a Google service"""
        if not url or not url.startswith('http'):
            return False
        
        # Filter out Google and other unwanted domains
        excluded_domains = [
            'google.com', 'youtube.com', 'googleusercontent.com',
            'googlevideo.com', 'gstatic.com', 'googleapis.com',
            'google-analytics.com', 'googletagmanager.com',
            'accounts.google.com', 'support.google.com'
        ]
        
        for domain in excluded_domains:
            if domain in url.lower():
                return False
        
        return True
    
    async def get_search_urls(self, query: str, max_results: int = 10) -> List[str]:
        """Main method to get search URLs"""
        page = await self.context.new_page()
        
        try:
            print(f"Searching for: '{query}'")
            
            # Perform search
            if not await self.perform_search(page, query):
                print("All search strategies failed")
                return []
            
            # Wait for results
            await self.wait_for_results(page)
            
            # Extract URLs
            urls = await self.extract_urls(page, max_results)
            
            print(f"Successfully extracted {len(urls)} URLs")
            return urls
            
        except Exception as e:
            print(f"Error during search: {e}")
            # Take screenshot for debugging
            try:
                await page.screenshot(path=f"debug_screenshot_{int(time.time())}.png")
                print("Debug screenshot saved")
            except:
                pass
            return []
            
        finally:
            await page.close()

# Utility functions remain the same
async def search_urls(query: str, max_results: int = 10, locale: str = 'en-US', region: str = 'US') -> List[str]:
    """Simple function to get URLs from Google search"""
    async with GoogleURLScraper(headless=True, locale=locale, region=region) as scraper:
        urls = await scraper.get_search_urls(query, max_results)
        return urls

def print_urls(urls: List[str], query: str = ""):
    """Print URLs in a clean format"""
    print(f"\n{'='*60}")
    if query:
        print(f"URLs for query: '{query}'")
    print(f"Found {len(urls)} URLs")
    print(f"{'='*60}")
    
    for i, url in enumerate(urls, 1):
        print(f"{i:2d}. {url}")
    print()

def save_urls(urls: List[str], filename: str = "urls.txt"):
    """Save URLs to a text file"""
    with open(filename, 'w') as f:
        for url in urls:
            f.write(url + '\n')
    print(f"Saved {len(urls)} URLs to {filename}")

# Test function to diagnose issues
async def diagnose_setup():
    """Test the setup and diagnose common issues"""
    print("Diagnosing setup...")
    
    try:
        # Test browser launch
        async with GoogleURLScraper(headless=False) as scraper:  # Non-headless for debugging
            print("✓ Browser launched successfully")
            
            # Test simple search
            urls = await scraper.get_search_urls("test", max_results=3)
            if urls:
                print(f"✓ Search working - found {len(urls)} URLs")
                return True
            else:
                print("✗ Search failed - no URLs found")
                return False
                
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        return False

# Usage examples
async def main():
    # Test setup first
    print("Testing setup...")
    if not await diagnose_setup():
        print("Setup failed. Please check your installation.")
        return
    
    # Single search
    query = "python web scraping"
    urls = await search_urls(query, max_results=5)
    print_urls(urls, query)
    
    if urls:
        save_urls(urls, "search_urls.txt")
    
    return urls

if __name__ == "__main__":
    # Run the main function
    urls = asyncio.run(main())