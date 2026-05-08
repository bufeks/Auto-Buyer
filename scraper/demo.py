import random
from typing import Any, Dict, List
from .models import Item

_BRANDS = ["Nike", "Adidas", "Supreme", "BAPE", "Stussy", "Carhartt", "Palace", "Stone Island"]
_TYPES = ["Hoodie", "T-Shirt", "Sweatpants", "Jacket", "Cap", "Sneakers", "Shorts", "Cargo Pants"]
_COLORS = ["Black", "White", "Grey", "Navy", "Red", "Olive", "Blue", "Beige"]


def scrape_demo(site_config: Dict[str, Any]) -> List[Item]:
    """Generate mock items for local testing."""
    site_name = site_config["name"]
    seed = site_config.get("seed", 42)
    rng = random.Random(seed)

    count = rng.randint(4, 10)
    items: List[Item] = []
    for i in range(count):
        brand = rng.choice(_BRANDS)
        item_type = rng.choice(_TYPES)
        color = rng.choice(_COLORS)
        price = rng.randint(3000, 50000)

        name = f"{brand} {color} {item_type}"
        item_url = f"https://example.com/products/{brand.lower()}-{item_type.lower()}-{i}"
        image_url = f"https://picsum.photos/seed/{brand}{item_type}{i}/300/400"

        items.append(
            Item(
                site_name=site_name,
                name=name,
                price=f"¥{price:,}",
                image_url=image_url,
                item_url=item_url,
            )
        )

    return items
