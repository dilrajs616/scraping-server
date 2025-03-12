from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from scripts.scraping.language_detector import detect_language
from scripts.scraping.check_domain_country import get_domain_country
from scripts.scraping.check_subdomain import is_subdomain
from bs4 import BeautifulSoup
import asyncio

# Function to extract text content from a webpage
async def extract_text_content(page, site: str, error_log_path: str, max_retries=2) -> str:
    print(f"Extracting content from site: {site}")

    retries = 0
    while retries < max_retries:
        try:
            # Navigate to the site with a timeout for slow pages
            response = await page.goto(site, timeout=15000)  # 15-second timeout

            # Capture the final URL if redirected
            final_url = response.url if response else site
            print(f"Redirected to: {final_url}")

            # Wait for the page to load
            await page.wait_for_selector('body', timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)

            # Extract HTML content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract main content
            main_content = soup.find_all(["article", "section", "main", "div"])
            text_content = " ".join([element.get_text(separator=" ", strip=True) for element in main_content])

            # Clean the content
            cleaned_content = ' '.join(text_content.split())
            if not cleaned_content:
                raise ValueError("Content is empty or failed to load properly.")

            # Detect language
            language = detect_language(cleaned_content)
            language = language if language else 'Unknown'

            return final_url, cleaned_content, language

        except (PlaywrightTimeoutError, ValueError) as e:
            print(f"Attempt {retries+1} failed for {site}: {e}")
            retries += 1
            await asyncio.sleep(2)  # Wait before retrying

    # If all retries fail, return None
    print(f"Failed to scrape {site} after {max_retries} attempts.")
    return site, None, None


async def scrape_website(page, site: str) -> tuple:
    sub_domain, domain = is_subdomain(site)
    print(sub_domain, domain)
    country = get_domain_country(site)
    print(country)
    final_url, content, language = await extract_text_content(page, site, error_log_path=None)
    print(f"language for {site} is : {language}")
    if content:
        return site, final_url, language, country, sub_domain, domain, content
    else:
        return site, None, None, None, sub_domain, domain, None


# Main scraping function
async def scrape_all_websites(domains: list, max_tabs: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
        )

        # Shared browser context
        context = await browser.new_context()

        semaphore = asyncio.Semaphore(max_tabs)

        async def scrape_with_semaphore(site):
            try:
                async with semaphore:
                    page = await context.new_page()  # Create a new page in the shared context
                    site, final_url, language, country, sub_domain, domain, content = await scrape_website(page, site)
                    return {
                        'site': site,
                        'final_url': final_url,
                        'content': content,
                        'language': language,
                        'country': country,
                        'sub_domain': sub_domain,
                        'domain': domain
                    }
            except Exception as e:
                print(f"Error scraping {site}: {str(e)}")
                return None
            finally:
                if not page.is_closed():
                    await page.close()

        try:
            # Collect results in parallel but return them one by one
            tasks = [scrape_with_semaphore(site) for site in domains]
            for result in asyncio.as_completed(tasks):
                yield await result  # Return each result sequentially for categorization
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await context.close()
            await browser.close()
