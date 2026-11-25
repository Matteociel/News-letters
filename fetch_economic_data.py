
import json
import urllib.request
from datetime import datetime, timezone

INDICATORS = {
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "gdp": "NY.GDP.MKTP.KD.ZG"
}

def fetch_indicator(code):
    url = (
        "https://api.worldbank.org/v2/country/USA/indicator/"
        + code + "?format=json&per_page=10"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GEI-EconomicDashboard/1.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if len(result) < 2 or not result[1]:
        return None

    for item in result[1]:
        if item["value"] is not None:
            return {
                "value": round(item["value"], 2),
                "date": item["date"]
            }

    return None

def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "Banque mondiale",
        "indicators": {}
    }

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
