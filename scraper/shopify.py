import requests
from typing import Any, Dict, List
from .models import Item

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_shopify(site_config: Dict[str, Any]) -> List[Item]:
    """Scrape a Shopify store via its products.json endpoint."""
    site_name = site_config["name"]
    base_url = site_config["url"].rstrip("/")
    collection = site_config.get("collection")
    limit = site_config.get("limit", 50)

    if collection:
        url = f"{base_url}/collections/{collection}/products.json?limit={limit}"
    else:
        url = f"{base_url}/products.json?limit={limit}"
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()

    items: List[Item] = []
    for product in resp.json().get("products", []):
        variants = product.get("variants", [])
        available_variants = [v for v in variants if v.get("available")]
        in_stock = bool(available_variants)

        title = product.get("title", "")
        vendor = product.get("vendor", "")
        handle = product.get("handle", "")

        name = f"{vendor} {title}".strip() if vendor else title

        price_variants = available_variants if in_stock else variants
        prices = [float(v["price"]) for v in price_variants if v.get("price")]
        price = f"¥{int(min(prices)):,}" if prices else None

        images = product.get("images", [])
        image_url = images[0]["src"] if images else None

        item_url = f"{base_url}/products/{handle}"

        items.append(
            Item(
                site_name=site_name,
                name=name,
                price=price,
                image_url=image_url,
                in_stock=in_stock,
                item_url=item_url,
            )
        )

    return items
