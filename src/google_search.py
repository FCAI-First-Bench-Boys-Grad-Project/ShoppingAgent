# Simple Google URL Scraper
# pip install playwright nest-asyncio
# playwright install

import asyncio
import nest_asyncio
from playwright.async_api import async_playwright
import random
from typing import List

# Enable nested event loops for Jupyter
nest_asyncio.apply()

class GoogleURLScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def get_search_urls(self, query: str, max_results: int = 10) -> List[str]:
        """Search Google and return only the URLs"""
        page = await self.context.new_page()
        
        try:
            print(f"Searching for: {query}")
            await page.goto("https://www.google.com", wait_until='networkidle')
            await asyncio.sleep(random.uniform(1, 2))

            # Handle cookie consent if present
            try:
                cookie_btn = await page.wait_for_selector('#L2AGLb, button:has-text("Accept")', timeout=3000)
                await cookie_btn.click()
                await asyncio.sleep(1)
            except:
                pass

            # Perform search - try multiple selectors
            search_input = None
            search_selectors = ['input[name="q"]', 'textarea[name="q"]', 'input[title="Search"]']
            
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            if not search_input:
                raise Exception("Could not find search input")
                
            await search_input.click()
            await search_input.fill(query)
            await page.keyboard.press('Enter')
            
            # Wait for results - try multiple selectors
            result_selectors = ['div#search', 'div#rso', '#search']
            results_loaded = False
            
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    results_loaded = True
                    break
                except:
                    continue
            
            if not results_loaded:
                raise Exception("Could not find search results")
                
            await asyncio.sleep(2)

            # Extract URLs - try multiple container selectors
            urls = []
            container_selectors = [
                'div.g:has(h3)',           # Standard containers
                'div[data-ved]:has(h3)',   # Alternative containers  
                '.g:has(a h3)',            # Another format
                'div.tF2Cxc',              # Newer Google format
                '[jscontroller]:has(h3)'   # Generic controller containers
            ]
            
            result_containers = []
            for selector in container_selectors:
                try:
                    containers = await page.query_selector_all(selector)
                    if containers:
                        result_containers = containers
                        print(f"Found {len(containers)} containers with selector: {selector}")
                        break
                except:
                    continue
            
            if not result_containers:
                print("No result containers found with any selector")
                return []
            
            for container in result_containers[:max_results]:
                try:
                    # Try multiple link selectors
                    link_selectors = [
                        'h3 a',                    # Title link
                        'a:has(h3)',              # Link containing title
                        'a[href^="http"]:has(h3)', # External link with title
                        'h3 parent::a',           # Title's parent link
                        'a[jsname]'               # Links with jsname attribute
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
                        # Filter out Google URLs and ensure it's a valid external URL
                        if (url and url.startswith('http') and 
                            'google.com' not in url and 
                            'youtube.com' not in url):  # Optional: filter YouTube too
                            urls.append(url)
                            print(f"Found URL {len(urls)}: {url}")
                except Exception as e:
                    continue
            
            return urls
            
        except Exception as e:
            print(f"Error during search: {e}")
            return []
            
        finally:
            await page.close()

# Simple usage functions
async def search_urls(query: str, max_results: int = 10) -> List[str]:
    """Simple function to get URLs from Google search"""
    async with GoogleURLScraper(headless=True) as scraper:
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

# Usage examples
async def main():
    # Single search
    query = "python web scraping"
    urls = await search_urls(query, max_results=5)
    print_urls(urls, query)
    
    # Save to file
    if urls:
        save_urls(urls, "search_urls.txt")
    
    return urls

# Batch search function
async def batch_search_urls(queries: List[str], max_results: int = 5):
    """Search multiple queries and return all URLs"""
    all_urls = {}
    
    async with GoogleURLScraper(headless=True) as scraper:
        for query in queries:
            print(f"\nProcessing: {query}")
            urls = await scraper.get_search_urls(query, max_results)
            all_urls[query] = urls
            print(f"Found {len(urls)} URLs")
            
            # Delay between searches
            await asyncio.sleep(random.uniform(3, 6))
    
    return all_urls

# Example usage
if __name__ == "__main__":
    # Run single search
    urls = asyncio.run(search_urls("OpenAI GPT-4", max_results=5))    
    # Or run batch search
    # queries = ["python tutorial", "web scraping", "data science"]
    # results = asyncio.run(batch_search_urls(queries))
    # for query, urls in results.items():
    #     print_urls(urls, query)