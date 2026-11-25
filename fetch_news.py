
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = [
    {
        "name": "Federal Reserve",
        "region": "États-Unis",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml"
    },
    {
        "name": "BCE",
        "region": "Europe",
        "url": "https://www.ecb.europa.eu/rss/press.html"
    },
    {
        "name": "Eurostat",
        "region": "Europe",
        "url": "https://ec.europa.eu/eurostat/cache/RSS/rss_estat_news.xml"
    }
]

def get_text(element, names):
    for child in element.iter():
        tag = child.tag.split("}")[-1].lower()
        if tag in names and child.text:
            return child.text.strip()
    return ""

def read_feed(feed):
    articles = []

    request = urllib.request.Request(
        feed["url"],
        headers={"User-Agent": "GEI-NewsBot/1.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            root = ET.fromstring(response.read())

        for item in root.iter():
            tag = item.tag.split("}")[-1].lower()

            if tag not in ("item", "entry"):
                continue

            title = get_text(item, ["title"])
            link = ""

            for child in item:
                child_tag = child.tag.split("}")[-1].lower()

                if child_tag == "link":
                    link = child.attrib.get("href", "")
                    if not link:
                        link = child.text or ""

            if not link:
                link = get_text(item, ["guid", "id"])

            date = get_text(
                item,
                ["pubdate", "published", "updated", "date"]
            )

            if title and link:
                articles.append({
                    "title": title,
                    "url": link,
                    "date": date,
                    "source": feed["name"],
                    "region": feed["region"]
                })

    except Exception as error:
        print("Erreur pour", feed["name"], ":", error)

    return articles

all_articles = []

for feed in FEEDS:
    print("Lecture :", feed["name"])
    all_articles.extend(read_feed(feed))

# Suppression des doublons
unique = {}
for article in all_articles:
    unique[article["url"]] = article

articles = list(unique.values())[:60]

data = {
    "updated": datetime.now(timezone.utc).isoformat(),
    "count": len(articles),
    "articles": articles
}

with open("news.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("Articles récupérés :", len(articles))
