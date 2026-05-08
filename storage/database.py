import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from scraper.models import Item

DB_PATH = Path(__file__).parent.parent / "data" / "items.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                item_id     TEXT PRIMARY KEY,
                site_name   TEXT NOT NULL,
                name        TEXT NOT NULL,
                price       TEXT,
                image_url   TEXT,
                item_url    TEXT NOT NULL,
                first_seen  TEXT NOT NULL,
                last_seen   TEXT NOT NULL,
                is_restock  INTEGER NOT NULL DEFAULT 0,
                is_active   INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS scrape_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                site_name       TEXT NOT NULL,
                scraped_at      TEXT NOT NULL,
                items_found     INTEGER DEFAULT 0,
                new_items       INTEGER DEFAULT 0,
                restock_items   INTEGER DEFAULT 0,
                error           TEXT
            );
        """)


def upsert_items(site_name: str, scraped: List[Item]) -> dict:
    """Persist scraped items, detecting new arrivals and restocks."""
    now = datetime.now().isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as conn:
        existing = {
            row[0]: bool(row[1])
            for row in conn.execute(
                "SELECT item_id, is_active FROM items WHERE site_name = ?",
                (site_name,),
            )
        }

        scraped_ids = {item.item_id for item in scraped}
        new_count = restock_count = 0

        for item in scraped:
            if item.item_id not in existing:
                conn.execute(
                    """
                    INSERT INTO items
                        (item_id, site_name, name, price, image_url, item_url,
                         first_seen, last_seen, is_restock, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
                    """,
                    (
                        item.item_id, site_name, item.name, item.price,
                        item.image_url, item.item_url, now, now,
                    ),
                )
                new_count += 1
            elif not existing[item.item_id]:
                # Item was inactive but has reappeared → restock
                conn.execute(
                    """
                    UPDATE items
                    SET is_restock = 1, is_active = 1, last_seen = ?,
                        name = ?, price = ?, image_url = ?
                    WHERE item_id = ?
                    """,
                    (now, item.name, item.price, item.image_url, item.item_id),
                )
                restock_count += 1
            else:
                conn.execute(
                    "UPDATE items SET last_seen = ?, name = ?, price = ?, image_url = ? WHERE item_id = ?",
                    (now, item.name, item.price, item.image_url, item.item_id),
                )

        # Items no longer in the scrape → mark inactive
        for item_id in existing:
            if item_id not in scraped_ids:
                conn.execute(
                    "UPDATE items SET is_active = 0 WHERE item_id = ?",
                    (item_id,),
                )

    return {"total": len(scraped), "new": new_count, "restock": restock_count}


def log_scrape(
    site_name: str,
    items_found: int,
    new_items: int,
    restock_items: int,
    error: Optional[str] = None,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO scrape_log
                (site_name, scraped_at, items_found, new_items, restock_items, error)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                site_name,
                datetime.now().isoformat(timespec="seconds"),
                items_found,
                new_items,
                restock_items,
                error,
            ),
        )


def get_items(
    site_name: Optional[str] = None,
    status: Optional[str] = None,
) -> List[dict]:
    query = "SELECT * FROM items WHERE 1=1"
    params: list = []

    if site_name:
        query += " AND site_name = ?"
        params.append(site_name)

    if status == "new":
        query += " AND is_restock = 0 AND is_active = 1"
    elif status == "restock":
        query += " AND is_restock = 1 AND is_active = 1"
    else:
        query += " AND is_active = 1"

    query += " ORDER BY last_seen DESC"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, params)]


def get_sites() -> List[str]:
    with sqlite3.connect(DB_PATH) as conn:
        return [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT site_name FROM items ORDER BY site_name"
            )
        ]


def get_scrape_log(limit: int = 20) -> List[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM scrape_log ORDER BY scraped_at DESC LIMIT ?",
                (limit,),
            )
        ]
