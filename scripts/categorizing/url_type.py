def check_url(url):
    url_lower = url.lower()
    result = None

    if 'cdn' in url_lower:
        result = "Content delivery"
    elif '.gov' in url_lower:
        result = "Government"
    elif '.ac' in url_lower or '.edu' in url_lower:
        result = "Education"
    elif 'blog' in url_lower or 'forum' in url_lower:
        result = "Blogs & forums"
    elif 'vpn' in url_lower:
        result = "Anonymizers"
    elif 'mail' in url_lower:
        result = "Web e-mail"
    elif 'news' in url_lower:
        result = "News"
    elif '.mil' in url_lower:
        result = "Military"
    elif '.int' in url_lower:
        result = "International organization"
    elif 'adult' in url_lower or 'porn' in url_lower:
        result = "Sexually explicit"
    elif 'torrent' in url_lower or 'p2p' in url_lower:
        result = "Peer-to-peer & torrents"
    elif 'fitness' in url_lower:
        result = "Hobbies"

    if result:
        print(f'Final Response: URL: {url} Category: {result}\n')
        return result
    
    return None
