
import csv
import json
import urllib.request
from datetime import datetime, timezone
from io import StringIO

SERIES = {
    "fed_rate": "FEDFUNDS",
    "inflation": "CPIAUCSL",
    "unemployment": "UNRATE",
    "payrolls": "PAYEMS",
    "gdp": "A191RL1Q225SBEA"
}

def fetch_series(series_id):
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GEI-EconomicData/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        content = response.read().decode("utf-8")

    rows = list(csv.DictReader(StringIO(content)))
    return [
        {
            "date": row["observation_date"],
            "value": row[series_id]
        }
        for row in rows
        if row.get(series_id) not in ("", ".")
    ]

def latest(series):
    return series[-1] if series else None

def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "Federal Reserve Bank of St. Louis - FRED",
        "indicators": {}
    }

    for name, series_id in SERIES.items():
        try:
            values = fetch_series(series_id)
            data["indicators"][name] = {
                "latest": latest(values),
                "previous": values[-2] if len(values) > 1 else None,
                "history": values[-15:]
            }
            print(f"{name}: OK")
        except Exception as error:
            print(f"{name}: erreur - {error}")
            data["indicators"][name] = None

    inflation = fetch_series("CPIAUCSL")
    if len(inflation) > 12:
        current = float(inflation[-1]["value"])
        year_ago = float(inflation[-13]["value"])
        data["indicators"]["inflation_yoy"] = {
            "value": round((current / year_ago - 1) * 100, 2),
            "date": inflation[-1]["date"]
        }

    with open("us_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("Fichier us_data.json créé.")

if __name__ == "__main__":
    main()
