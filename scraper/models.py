import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    site_name: str
    name: str
    item_url: str
    price: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: bool = True
    variants_available: Optional[str] = None  # JSON: ["S","M"] など在庫ありバリアント
    variants_all: Optional[str] = None        # JSON: ["S","M","L"] など全バリアント
    item_id: str = field(default="", init=True)

    def __post_init__(self) -> None:
        if not self.item_id:
            self.item_id = hashlib.md5(
                f"{self.site_name}:{self.item_url}".encode()
            ).hexdigest()
