import re
import requests
from urllib.parse import urlparse, parse_qs

def find_between(text, first, last):
    try:
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]
    except ValueError:
        return None

def get_formatted_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def get_data(url: str):
    netloc = urlparse(url).netloc
    url = url.replace(netloc, "1024terabox.com")

    try:
        page = requests.get(url)
        thumb = find_between(page.text, 'og:image" content="', '"')
    except:
        thumb = None

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://ytshorts.savetube.me"
    }

    payload = {"url": url}
    res = requests.post("https://ytshorts.savetube.me/api/v1/terabox-downloader", json=payload, headers=headers)

    if res.status_code != 200:
        return None

    result = res.json().get("response", [])[0]
    resolutions = result.get("resolutions", {})
    video = resolutions.get("HD Video", "") or resolutions.get("Fast Download", "")

    head = requests.head(video)
    size = int(head.headers.get("Content-Length", 0))
    name = re.findall('filename="(.+?)"', head.headers.get("content-disposition", ""))

    return {
        "file_name": name[0] if name else "Terabox Video",
        "link": video,
        "direct_link": video,
        "thumb": thumb,
        "size": get_formatted_size(size) if size else None,
        "sizebytes": size
    }