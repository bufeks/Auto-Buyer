from playwright.sync_api import sync_playwright
from typing import Any, Dict, List
from .models import Item


def scrape_playwright(site_config: Dict[str, Any]) -> List[Item]:
    """Scrape JavaScript-rendered pages using a headless Chromium browser."""
    site_name = site_config["name"]
    url = site_config["url"]
    selectors = site_config.get("selectors", {})
    wait_for = site_config.get("wait_for", "")  # optional CSS selector to wait for

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)

        if wait_for:
            page.wait_for_selector(wait_for, timeout=15000)

        if not wait_for:
            page.wait_for_timeout(2000)

        container_sel = selectors.get("container", "")
        if not container_sel:
            browser.close()
            return []

        containers = page.query_selector_all(container_sel)
        items: List[Item] = []

        for container in containers:
            name_sel = selectors.get("name", "")
            price_sel = selectors.get("price", "")
            image_sel = selectors.get("image", "img")
            link_sel = selectors.get("link", "a")

            name_el = container.query_selector(name_sel) if name_sel else None
            price_el = container.query_selector(price_sel) if price_sel else None
            image_el = container.query_selector(image_sel)
            link_el = container.query_selector(link_sel)

            name = name_el.inner_text().strip() if name_el else ""
            if not name:
                continue

            price = price_el.inner_text().strip() if price_el else None

            image_url = None
            if image_el:
                image_url = (
                    image_el.get_attribute("src")
                    or image_el.get_attribute("data-src")
                )

            item_url = url
            if link_el:
                href = link_el.get_attribute("href") or ""
                if href.startswith("http"):
                    item_url = href
                elif href.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    item_url = f"{parsed.scheme}://{parsed.netloc}{href}"

            items.append(
                Item(
                    site_name=site_name,
                    name=name,
                    price=price,
                    image_url=image_url,
                    item_url=item_url,
                )
            )

        context.close()
        browser.close()
    return items
