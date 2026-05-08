from typing import List, Dict, Any
from .models import Item
from .shopify import scrape_shopify
from .generic import scrape_generic
from .demo import scrape_demo

_SCRAPERS = {
    "shopify": scrape_shopify,
    "generic": scrape_generic,
    "demo": scrape_demo,
}


def scrape_site(site_config: Dict[str, Any]) -> List[Item]:
    scraper_type = site_config.get("type", "generic")
    fn = _SCRAPERS.get(scraper_type, scrape_generic)
    return fn(site_config)
