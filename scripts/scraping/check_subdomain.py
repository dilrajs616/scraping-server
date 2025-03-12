from urllib.parse import urlparse
import tldextract

def is_subdomain(url):
    # Parse the original URL to extract the scheme
    parsed_url = urlparse(url)
    
    # Extract the subdomain, domain, and suffix
    extracted = tldextract.extract(url)
    
    # Determine if it's a subdomain, ignoring "www"
    if extracted.subdomain and extracted.subdomain != "www":
        base_domain = f"{extracted.domain}.{extracted.suffix}"
        domain_without_subdomain = f"{parsed_url.scheme}://{base_domain}"
        return True, domain_without_subdomain
    else:
        return False, "N/A"