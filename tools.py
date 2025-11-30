# Example tools, add your own tools here and add them to the schema.json file

import httpx


def crypto_prices(product_id: str):
    """Fetch crypto price info for a Coinbase product id."""
    url = f"https://api.coinbase.com/api/v3/brokerage/market/products/{product_id}"
    response = httpx.get(url, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    return response.json()
