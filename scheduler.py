"""
Entry point: starts the scraper scheduler and the Flask web server.

Usage:
    pip install -r requirements.txt
    python scheduler.py

Web dashboard: http://localhost:5000
"""

import logging
import sys
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from scraper import scrape_site
from storage.database import init_db, log_scrape, upsert_items
from web.app import create_app

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
        logger.error("%s → エラー: %s", site_name, exc)
        log_scrape(site_name, 0, 0, 0, str(exc))


def main() -> None:
    init_db()

    sites = load_config()
    if not sites:
        logger.warning(
            "有効なサイトが設定されていません。config/sites.yaml を確認してください。"
        )

    scheduler = BackgroundScheduler()

    for site in sites:
        interval = site.get("interval_minutes", 60)
        # 起動時に即座に実行
        run_scraper(site)
        # 定期実行をスケジュール
        scheduler.add_job(
            run_scraper,
            trigger="interval",
            minutes=interval,
            args=[site],
            id=site["name"],
        )
        logger.info("スケジュール登録: %s (%d分ごと)", site["name"], interval)

    scheduler.start()
    logger.info("スケジューラー起動完了")

    app = create_app()
    port = 5000
    logger.info("Webサーバー起動: http://localhost:%d", port)
    try:
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
