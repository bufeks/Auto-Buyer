"""
One-shot scraper: runs all configured sites once, updates the database,
then regenerates dashboard.html.

Used by GitHub Actions (runs on every scheduled trigger).
"""
import logging
import sys
from pathlib import Path

import yaml

from scraper import scrape_site
from storage.database import init_db, log_scrape, upsert_items
from generate_static import generate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config" / "sites.yaml"


def load_config() -> list:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return [s for s in cfg.get("sites", []) if s.get("enabled", True)]


def run_scraper(site_config: dict) -> None:
    site_name = site_config["name"]
    logger.info("Scraping: %s", site_name)
    try:
        items = scrape_site(site_config)
        stats = upsert_items(site_name, items)
        log_scrape(site_name, stats["total"], stats["new"], stats["restock"])
        logger.info(
            "%s → %d 件 (新着 %d, リストック %d)",
            site_name, stats["total"], stats["new"], stats["restock"],
        )
    except Exception as exc:
        logger.error("%s → エラー: %s", site_name, exc, exc_info=True)
        log_scrape(site_name, 0, 0, 0, str(exc))


def main() -> None:
    init_db()

    sites = load_config()
    if not sites:
        logger.warning("有効なサイトが設定されていません。config/sites.yaml を確認してください。")
        sys.exit(1)

    for site in sites:
        run_scraper(site)

    logger.info("静的ダッシュボードを生成中...")
    generate()
    logger.info("完了！")


if __name__ == "__main__":
    main()
