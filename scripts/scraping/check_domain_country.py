import whois

def get_domain_country(domain):
    try:
        # Perform WHOIS Lookup
        domain_info = whois.whois(domain)
        whois_country = domain_info.get('country', 'N/A')
    except Exception as e:
        whois_country = f"N/A"
    
    return whois_country
