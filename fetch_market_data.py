
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Sources de données Yahoo Finance

MARKETS = {
    "bitcoin": "BTC-USD",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "cac40": "^FCHI",
    "gold": "GC=F",
    "silver": "SI=F",
    "oil": "CL=F",
    "eurusd": "EURUSD=X"
}

def get_price(symbol):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol, safe="")
        + "?range=1d&interval=5m"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    result = data["chart"]["result"][0]
    price = result["meta"].get("regularMarketPrice")

    if price is None:
        prices = result["indicators"]["quote"][0]["close"]
        valid_prices = [p for p in prices if p is not None]

        if not valid_prices:
            raise ValueError("Aucun cours disponible")

        price = valid_prices[-1]

    return round(float(price), 4)


def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance",
        "markets": {}
    }

    for name, symbol in MARKETS.items():
        try:
            price = get_price(symbol)

            data["markets"][name] = {
                "value": price,
                "status": "ok",
                "symbol": symbol
            }

            print(name, ":", price)

        except Exception as error:
            data["markets"][name] = {
                "value": None,
                "status": "error",
                "message": str(error)
            }

            print("Erreur", name, ":", error)

    with open("market_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print("Fichier market_data.json créé.")


if __name__ == "__main__":
    main()
