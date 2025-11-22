"""
Web scraper to collect work pass information from MOM website
"""
import requests
from bs4 import BeautifulSoup
import time
import json
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MOMScraper:
    """Scraper for Ministry of Manpower Singapore website"""
    
    def __init__(self, base_url: str = "https://www.mom.gov.sg"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.scraped_data = []
        
    def scrape_page(self, url: str) -> Dict:
        """Scrape a single page and extract relevant content"""
        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            # MOM website typically has content in main, article, or specific divs
            content_selectors = [
                'main',
                'article',
                '.content',
                '.main-content',
                '#main-content',
                '.page-content'
            ]
            
            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                content = soup.find('body')
            
            # Remove script and style elements
            for script in content.find_all(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Extract text
            text = content.get_text(separator='\n', strip=True)
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else url
            
            # Extract headings for structure
            headings = []
            for heading in content.find_all(['h1', 'h2', 'h3', 'h4']):
                headings.append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            
            # Extract links for further scraping
            links = []
            for link in content.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                    links.append(full_url)
            
            return {
                'url': url,
                'title': title_text,
                'content': text,
                'headings': headings,
                'links': list(set(links))  # Remove duplicates
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def find_work_pass_pages(self) -> List[str]:
        """Find all relevant work pass pages from MOM website"""
        # Main passes page
        passes_url = f"{self.base_url}/passes-and-permits"
        
        work_pass_urls = [passes_url]
        
        try:
            response = self.session.get(passes_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find links related to work passes
            # Common patterns in MOM URLs
            pass_keywords = [
                'employment-pass',
                'personalised-employment-pass',
                'entrepass',
                's-pass',
                'work-permit',
                'training-employment-pass',
                'work-holiday-pass',
                'dependant',
                'ltvp',
                'foreign-domestic-worker',
                'performing-artiste',
                'confinement-nanny'
            ]
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(self.base_url, href)
                
                # Check if URL contains work pass keywords
                if any(keyword in href.lower() for keyword in pass_keywords):
                    if full_url not in work_pass_urls:
                        work_pass_urls.append(full_url)
            
            logger.info(f"Found {len(work_pass_urls)} work pass related URLs")
            
        except Exception as e:
            logger.error(f"Error finding work pass pages: {str(e)}")
        
        return work_pass_urls
    
    def scrape_all(self, max_pages: int = 50) -> List[Dict]:
        """Scrape all work pass related pages"""
        urls = self.find_work_pass_pages()
        scraped = []
        visited = set()
        
        # Limit to max_pages to avoid excessive scraping
        urls_to_scrape = urls[:max_pages]
        
        for url in urls_to_scrape:
            if url in visited:
                continue
                
            visited.add(url)
            data = self.scrape_page(url)
            
            if data:
                scraped.append(data)
            
            # Be respectful - add delay between requests
            time.sleep(1)
        
        self.scraped_data = scraped
        return scraped
    
    def save_to_json(self, filename: str = "mom_data.json"):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.scraped_data)} pages to {filename}")


