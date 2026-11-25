
import json
import urllib.request
from datetime import datetime, timezone

INDICATORS = {
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "gdp": "NY.GDP.MKTP.KD.ZG"
}

def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GEI-EconomicDashboard/1.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

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

def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "Banque mondiale et Federal Reserve Bank of New York",
        "fed": None,
        "indicators": {}
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

    with open("us_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("Fichier us_data.json créé.")

if __name__ == "__main__":
    main()
