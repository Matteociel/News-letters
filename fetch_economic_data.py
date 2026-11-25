
import csv
import json
import time
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
        f"?id={series_id}&cosd=2015-01-01"
    )

    for attempt in range(3):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            with urllib.request.urlopen(request, timeout=60) as response:
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

        except Exception as error:
            print(f"Tentative {attempt + 1}/3 pour {series_id}: {error}")
            if attempt < 2:
                time.sleep(5)

    return []

def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "FRED - Federal Reserve Bank of St. Louis",
        "indicators": {}
    }

    successful = 0

    for name, series_id in SERIES.items():
        values = fetch_series(series_id)

        if values:
            successful += 1
            data["indicators"][name] = {
                "latest": values[-1],
                "previous": values[-2] if len(values) > 1 else None,
                "history": values[-15:]
            }
            print(f"{name}: OK")
        else:
            data["indicators"][name] = None
            print(f"{name}: indisponible")

    inflation = data["indicators"].get("inflation")

    if inflation and len(inflation["history"]) >= 13:
        values = fetch_series("CPIAUCSL")

        if len(values) >= 13:
            current = float(values[-1]["value"])
            year_ago = float(values[-13]["value"])

            data["indicators"]["inflation_yoy"] = {
                "value": round((current / year_ago - 1) * 100, 2),
                "date": values[-1]["date"]
            }

    with open("us_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"{successful}/5 indicateurs récupérés.")

    if successful == 0:
        raise SystemExit("Aucune donnée récupérée depuis FRED.")

if __name__ == "__main__":
    main()
