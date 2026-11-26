
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Sources de données Yahoo Finance


MARKETS = {
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "cac40": "^FCHI",
    "gold": "GC=F",
    "silver": "SI=F",
    "oil": "CL=F",
    "eurusd": "EURUSD=X"
}



def get_market_data(symbol):
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
    meta = result["meta"]

    # Dernier cours disponible
    price = meta.get("regularMarketPrice")

    if price is None:
        prices = result["indicators"]["quote"][0]["close"]
        valid_prices = [p for p in prices if p is not None]

        if not valid_prices:
            raise ValueError("Aucun cours disponible")

        price = valid_prices[-1]

    price = float(price)

    # Clôture de la séance précédente
    previous_close = (
        meta.get("chartPreviousClose")
        or meta.get("previousClose")
    )

    change = None
    change_percent = None

    if previous_close is not None and float(previous_close) != 0:
        previous_close = float(previous_close)
        change = price - previous_close
        change_percent = (change / previous_close) * 100

    return {
        "value": round(price, 4),
        "previous_close": (
            round(previous_close, 4)
            if previous_close is not None else None
        ),
        "change": (
            round(change, 4) if change is not None else None
        ),
        "change_percent": (
            round(change_percent, 2)
            if change_percent is not None else None
        )
    }


def main():
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance",
        "markets": {}
    }

    for name, symbol in MARKETS.items():
        try:
            market = get_market_data(symbol)

            data["markets"][name] = {
                **market,
                "status": "ok",
                "symbol": symbol
            }

            print(
                name,
                ":",
                market["value"],
                "Variation :",
                market["change_percent"]
            )

        except Exception as error:
            data["markets"][name] = {
                "value": None,
                "previous_close": None,
                "change": None,
                "change_percent": None,
                "status": "error",
                "message": str(error)
            }

            print("Erreur", name, ":", error)

    with open("market_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print("Fichier market_data.json créé.")


if __name__ == "__main__":
    main()
