import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Any, Dict, List
from .models import Item

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_generic(site_config: Dict[str, Any]) -> List[Item]:
    """Scrape any site using configurable CSS selectors."""
    site_name = site_config["name"]
    url = site_config["url"]
    selectors = site_config.get("selectors", {})
    headers = {**_HEADERS, **site_config.get("headers", {})}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    container_sel = selectors.get("container", "")
    if not container_sel:
        return []

    parsed_base = urlparse(url)
    base = f"{parsed_base.scheme}://{parsed_base.netloc}"

    items: List[Item] = []
    for container in soup.select(container_sel):
        name_el = container.select_one(selectors.get("name", "")) if selectors.get("name") else None
        price_el = container.select_one(selectors.get("price", "")) if selectors.get("price") else None
        image_el = container.select_one(selectors.get("image", "img"))
        link_el = container.select_one(selectors.get("link", "a")) if selectors.get("link") else None
        # コンテナ自体がリンク（<a> タグ）の場合はそれを使う
        if link_el is None and container.name == "a":
            link_el = container
        elif link_el is None:
            link_el = container.select_one("a")

        name = name_el.get_text(strip=True) if name_el else ""
        if not name:
            continue

        price = price_el.get_text(strip=True) if price_el else None

        image_url = None
        if image_el:
            src = image_el.get("src") or image_el.get("data-src") or ""
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = base + src
            image_url = src or None

        item_url = url
        if link_el:
            href = link_el.get("href", "")
            if href.startswith("http"):
                item_url = href
            elif href.startswith("//"):
                item_url = "https:" + href
            elif href.startswith("/"):
                item_url = base + href

        soldout_el = container.select_one(selectors.get("sold_out", "")) if selectors.get("sold_out") else None
        # コンテナ自身のクラスで SOLD OUT を判定する場合
        sold_out_class = selectors.get("sold_out_class")
        if sold_out_class:
            in_stock = sold_out_class not in container.get("class", [])
        else:
            in_stock = soldout_el is None

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
