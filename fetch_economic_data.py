
import json
import re
import html
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone

INDICATORS = {
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "gdp": "NY.GDP.MKTP.KD.ZG"
}

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GEI-EconomicDashboard/1.0"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def get_page_text(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GEI-EconomicDashboard/1.0"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        page = response.read().decode("utf-8", errors="replace")

    parser = TextExtractor()
    parser.feed(page)
    return re.sub(r"\s+", " ", html.unescape(parser.get_text()))


def fetch_indicator(code):
    url = (
        "https://api.worldbank.org/v2/country/USA/indicator/"
        + code + "?format=json&per_page=10"
    )
    result = get_json(url)

    if len(result) < 2 or not result[1]:
        return None

    for item in result[1]:
        if item["value"] is not None:
            return {
                "value": round(item["value"], 2),
                "date": item["date"]
            }

    return None


def fetch_fed_rate():
    url = (
        "https://markets.newyorkfed.org/api/rates/"
        "unsecured/effr/last/1.json"
    )
    result = get_json(url)
    rates = result.get("refRates", [])

    if not rates:
        return None

    rate = rates[0]

    return {
        "value": rate.get("percentRate"),
        "date": rate.get("effectiveDate"),
        "target_min": rate.get("targetRateFrom"),
        "target_max": rate.get("targetRateTo")
    }


def fetch_cleveland_inflation():
    url = "https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting"
    text = get_page_text(url)

    section = text.split(
        "Inflation, year-over-year percent change", 1
    )

    if len(section) < 2:
        return None

    match = re.search(
        r"([A-Za-z]+ \d{4})\s+"
        r"(-?\d+(?:\.\d+)?)\s+"
        r"(-?\d+(?:\.\d+)?)\s+"
        r"(-?\d+(?:\.\d+)?)\s+"
        r"(-?\d+(?:\.\d+)?)",
        section[1]
    )

    if not match:
        return None

    return {
        "month": match.group(1),
        "cpi": float(match.group(2)),
        "core_cpi": float(match.group(3)),
        "pce": float(match.group(4)),
        "core_pce": float(match.group(5)),
        "source": "Federal Reserve Bank of Cleveland",
        "type": "Nowcast annuel"
    }


def fetch_gdpnow():
    url = "https://www.atlantafed.org/research-and-data/data/gdpnow"
    text = get_page_text(url)

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*%+\s+"
        r"(?:Fourth|First|Second|Third)-Quarter "
        r"GDPNow Estimate for (\d{4}:Q\d)\s+"
        r"Updated:\s+([A-Za-z]+ \d{1,2}, \d{4})",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return {
        "value": float(match.group(1)),
        "quarter": match.group(2),
        "date": match.group(3),
        "source": "Federal Reserve Bank of Atlanta",
        "type": "Nowcast de croissance annualisée"
    }


def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "Banque mondiale et banques fédérales américaines",
        "fed": None,
        "indicators": {},
        "forecasts": {
            "inflation": None,
            "gdp": None,
            "employment": {
                "source": "Federal Reserve Bank of Philadelphia",
                "url": "https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/spf",
                "type": "Prévisions trimestrielles des économistes",
                "note": "Consulter la dernière enquête pour les projections de chômage et d'emploi."
            }
        }
    }

    try:
        data["fed"] = fetch_fed_rate()
        print("Fed Funds :", data["fed"])
    except Exception as error:
        print("Erreur Fed :", error)

    for name, code in INDICATORS.items():
        try:
            data["indicators"][name] = fetch_indicator(code)
            print(name, data["indicators"][name])
        except Exception as error:
            print("Erreur", name, error)
            data["indicators"][name] = None

    try:
        data["forecasts"]["inflation"] = fetch_cleveland_inflation()
        print("Prévision inflation :", data["forecasts"]["inflation"])
    except Exception as error:
        print("Erreur prévision inflation :", error)

    try:
        data["forecasts"]["gdp"] = fetch_gdpnow()
        print("Prévision PIB :", data["forecasts"]["gdp"])
    except Exception as error:
        print("Erreur prévision PIB :", error)

    with open("us_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("Fichier us_data.json créé.")


if __name__ == "__main__":
    main()
