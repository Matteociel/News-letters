from html.parser import HTMLParser
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from html import unescape

FEEDS = [
    {
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "source": "Federal Reserve",
        "region": "États-Unis"
    },
    {
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "source": "Banque centrale européenne",
        "region": "Europe"
    },
    {
        "url": "https://ec.europa.eu/eurostat/cache/RSS/rss_estat_news.xml",
        "source": "Eurostat",
        "region": "Europe"
    }
]

NAMESPACES = {
    
class MetaImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return

        data = dict(attrs)
        prop = data.get("property", "").lower()
        name = data.get("name", "").lower()

        if prop == "og:image" or name == "twitter:image":
            content = data.get("content")
            if content and content.startswith("http"):
                self.image = content


def get_article_image(url):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=8) as response:
            html = response.read(500000).decode(
                "utf-8", errors="ignore"
            )

        parser = MetaImageParser()
        parser.feed(html)
        return parser.image

    except Exception:
        return None

    "media": "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/"
}

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            attributes = dict(attrs)
            src = attributes.get("src")
            if src:
                self.images.append(src)

def get_text(element, names):
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def get_image(item):
    # Images fournies par Media RSS
    for tag in ("media:content", "media:thumbnail"):
        element = item.find(tag, NAMESPACES)
        if element is not None:
            url = element.attrib.get("url")
            if url:
                return url

    # Image jointe au flux RSS
    for enclosure in item.findall("enclosure"):
        url = enclosure.attrib.get("url", "")
        mime = enclosure.attrib.get("type", "")
        if url and (mime.startswith("image/") or
                    any(url.lower().split("?")[0].endswith(ext)
                        for ext in (".jpg", ".jpeg", ".png", ".webp"))):
            return url

    # Image intégrée dans le contenu
    content = (
        get_text(item, ["content:encoded", "description"]) or
        ""
    )

    parser = ImageParser()
    try:
        parser.feed(unescape(content))
    except Exception:
        pass

    if parser.images:
        return parser.images[0]

    return None

def normalize_date(value):
    if not value:
        return ""

    try:
        date = parsedate_to_datetime(value)
        return date.isoformat()
    except Exception:
        return value

def fetch_feed(feed):
    articles = []

    request = urllib.request.Request(
        feed["url"],
        headers={"User-Agent": "GEI-NewsBot/1.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        items = root.findall(".//item")

        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            title = get_text(item, ["title"])
            link = get_text(item, ["link"])

            # Format Atom
            if not link:
                link_element = item.find("{http://www.w3.org/2005/Atom}link")
                if link_element is not None:
                    link = link_element.attrib.get("href", "")

            date = (
                get_text(item, ["pubDate", "published", "updated"]) or ""
            )

            if title and link:
                articles.append({
                    "title": title,
                    "url": link,
                    "source": feed["source"],
                    "region": feed["region"],
                    "date": normalize_date(date),
                    "image": get_image(item) or get_article_image(link)
                })

        print(f"{feed['source']}: {len(articles)} articles")

    except Exception as error:
        print(f"Erreur {feed['source']}: {error}")

    return articles

def main():
    articles = []
    seen = set()

    for feed in FEEDS:
        for article in fetch_feed(feed):
            if article["url"] not in seen:
                seen.add(article["url"])
                articles.append(article)

    articles.sort(key=lambda x: x["date"], reverse=True)

    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "articles": articles
    }

    with open("news.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"Total : {len(articles)} actualités enregistrées.")

if __name__ == "__main__":
    main()
