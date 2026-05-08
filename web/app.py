from flask import Flask, jsonify, render_template, request

from storage.database import get_items, get_scrape_log, get_sites, init_db

app = Flask(__name__)


@app.route("/")
def index():
    site_filter = request.args.get("site", "")
    status_filter = request.args.get("status", "all")

    items = get_items(
        site_name=site_filter or None,
        status=status_filter if status_filter != "all" else None,
    )
    sites = get_sites()
    log = get_scrape_log(10)

    return render_template(
        "index.html",
        items=items,
        sites=sites,
        log=log,
        current_site=site_filter,
        current_status=status_filter,
    )


@app.route("/api/items")
def api_items():
    site_filter = request.args.get("site", "")
    status_filter = request.args.get("status", "")
    items = get_items(
        site_name=site_filter or None,
        status=status_filter or None,
    )
    return jsonify(items)


@app.route("/api/sites")
def api_sites():
    return jsonify(get_sites())


@app.route("/api/log")
def api_log():
    return jsonify(get_scrape_log())


def create_app() -> Flask:
    init_db()
    return app
