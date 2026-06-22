"""
Generates a self-contained static dashboard.html from the SQLite database.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from storage.database import get_items, get_scrape_log, get_sites

_JST = timezone(timedelta(hours=9))
OUTPUT = Path(__file__).parent / "dashboard.html"


def generate() -> None:
    items = get_items()
    sites = get_sites()
    log = get_scrape_log(20)
    updated = datetime.now(_JST).strftime("%Y-%m-%d %H:%M JST")

    items_json = json.dumps(items, ensure_ascii=False)
    sites_json = json.dumps(sites, ensure_ascii=False)
    log_json = json.dumps(log, ensure_ascii=False)

    OUTPUT.write_text(
        _build_html(items_json, sites_json, log_json, updated),
        encoding="utf-8",
    )
    print(f"Generated {OUTPUT} ({len(items)} items)")


def _build_html(items_json: str, sites_json: str, log_json: str, updated: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SUPPLY TRACKER - 新着 / リストック</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ background:#f5f5f5; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    .navbar-brand {{ font-weight:700; letter-spacing:-.5px; }}
    .card {{ border:none; border-radius:12px; overflow:hidden; transition:transform .15s,box-shadow .15s; text-decoration:none; color:inherit; display:block; }}
    .card:hover {{ transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,.12); color:inherit; text-decoration:none; }}
    .card-img-top {{ height:220px; object-fit:cover; background:#eee; }}
    .card-soldout {{ opacity:.6; }}
    .badge-new {{ background:#22c55e; }}
    .badge-restock {{ background:#f97316; }}
    .badge-soldout {{ background:#6b7280; }}
    .badge-instock {{ background:#3b82f6; }}
    .badge-hot {{ background:#ef4444; }}
    .badge-fast {{ background:#a855f7; }}
    .badge-quick {{ background:#06b6d4; }}
    .price {{ color:#dc2626; font-weight:700; font-size:.95rem; }}
    .price-soldout {{ color:#9ca3af; font-weight:700; font-size:.95rem; text-decoration:line-through; }}
    .site-tag {{ font-size:.7rem; background:#374151; }}
    .item-name {{ font-size:.85rem; font-weight:600; line-height:1.3; }}
    .filter-bar {{ background:#fff; border-radius:12px; padding:1rem; box-shadow:0 1px 4px rgba(0,0,0,.06); }}
    .stat-card {{ background:#fff; border-radius:12px; padding:1rem 1.25rem; box-shadow:0 1px 4px rgba(0,0,0,.06); }}
    .stat-num {{ font-size:1.8rem; font-weight:700; line-height:1; }}
    .log-table td, .log-table th {{ font-size:.78rem; }}
    .site-panel {{ background:#fff; border-radius:12px; padding:.75rem 1rem; box-shadow:0 1px 4px rgba(0,0,0,.06); }}
    .site-check label {{ font-size:.8rem; cursor:pointer; user-select:none; }}
    .site-check input {{ cursor:pointer; }}
  </style>
</head>
<body>
<nav class="navbar navbar-dark bg-dark">
  <div class="container-fluid px-4">
    <span class="navbar-brand">SUPPLY TRACKER</span>
    <span class="text-secondary small" id="count-label"></span>
  </div>
</nav>
<div class="container-fluid px-4 py-4">

  <div class="row g-3 mb-4">
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-num text-success" id="stat-new">—</div>
        <div class="text-muted small">新着</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-num text-warning" id="stat-restock">—</div>
        <div class="text-muted small">リストック</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-num text-secondary" id="stat-soldout">—</div>
        <div class="text-muted small">SOLD OUT</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-num" id="stat-sites">—</div>
        <div class="text-muted small">対象サイト数</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="stat-card">
        <div class="stat-num" style="font-size:1rem; padding-top:.4rem;">{updated}</div>
        <div class="text-muted small">最終取得</div>
      </div>
    </div>
  </div>

  <div class="filter-bar mb-3 d-flex flex-wrap gap-2 align-items-center">
    <div class="btn-group btn-group-sm" id="status-filters">
      <button class="btn btn-dark"              data-status="all">すべて</button>
      <button class="btn btn-outline-secondary" data-status="new">新着</button>
      <button class="btn btn-outline-secondary" data-status="restock">リストック</button>
      <button class="btn btn-outline-secondary" data-status="soldout">SOLD OUT</button>
    </div>
    <span class="ms-auto text-muted small d-none d-md-inline">15分ごとに自動更新</span>
  </div>
  <div class="site-panel mb-4">
    <div class="d-flex align-items-center gap-2 mb-2">
      <span class="small fw-semibold text-muted">サイト絞り込み</span>
      <button class="btn btn-outline-secondary btn-sm py-0 px-2" id="site-all-btn" style="font-size:.75rem;">全選択</button>
      <button class="btn btn-outline-secondary btn-sm py-0 px-2" id="site-none-btn" style="font-size:.75rem;">全解除</button>
    </div>
    <div class="d-flex flex-wrap gap-3" id="site-checkboxes"></div>
  </div>

  <div class="row row-cols-2 row-cols-md-3 row-cols-lg-4 row-cols-xl-5 g-3 mb-5" id="grid"></div>

  <details class="mb-4" id="log-section" style="display:none">
    <summary class="text-muted small mb-2" style="cursor:pointer;">取得ログ</summary>
    <div class="table-responsive">
      <table class="table table-sm log-table bg-white rounded">
        <thead class="table-light">
          <tr><th>サイト</th><th>取得日時</th><th>件数</th><th>新着</th><th>リストック</th><th>エラー</th></tr>
        </thead>
        <tbody id="log-body"></tbody>
      </table>
    </div>
  </details>

</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
const ALL_ITEMS = {items_json};
const ALL_SITES = {sites_json};
const SCRAPE_LOG = {log_json};

const NEW_WINDOW_MS = 72 * 3600 * 1000;  // 新着・リストックの表示期間（72時間）

function isRecentNew(item) {{
  return (Date.now() - new Date(item.first_seen).getTime()) < NEW_WINDOW_MS;
}}

function isRecentRestock(item) {{
  return item.restock_at
    ? (Date.now() - new Date(item.restock_at).getTime()) < NEW_WINDOW_MS
    : false;
}}

// 発売〜完売までの時間（時間単位）。計算できない場合は Infinity
function sellSpeedHours(item) {{
  if (!item.soldout_at) return Infinity;
  const baseDate = item.published_at || item.first_seen;
  if (!baseDate) return Infinity;
  const diffMs = new Date(item.soldout_at) - new Date(baseDate);
  if (diffMs <= 0) return Infinity;
  return diffMs / 3600000;
}}

let currentStatus = "all";
let selectedSites = new Set(JSON.parse(localStorage.getItem("selectedSites") || "null") || ALL_SITES);

function matchStatus(item, status) {{
  if (status === "all")     return item.is_active;
  if (status === "new")     return item.is_active && !item.is_restock && item.in_stock && isRecentNew(item);
  if (status === "restock") return item.is_active && item.is_restock && isRecentRestock(item);
  if (status === "soldout") return item.is_active && !item.in_stock;
  if (status === "instock") return item.is_active && item.in_stock;
  return item.is_active;
}}

function cardHTML(item) {{
  const soldout  = !item.in_stock;
  const restock  = item.in_stock && item.is_restock && isRecentRestock(item);
  const newItem  = item.in_stock && !item.is_restock && isRecentNew(item);
  let badgeCls, badgeTxt;
  if (soldout)        {{ badgeCls = "badge-soldout"; badgeTxt = "SOLD OUT"; }}
  else if (restock)   {{ badgeCls = "badge-restock"; badgeTxt = "リストック"; }}
  else if (newItem)   {{ badgeCls = "badge-new";     badgeTxt = "新着"; }}
  else                {{ badgeCls = "badge-instock";  badgeTxt = "在庫あり"; }}
  const img = item.image_url
    ? `<img src="${{item.image_url}}" class="card-img-top" alt="${{item.name}}" loading="lazy"
         onerror="this.src='https://placehold.co/300x220/eeeeee/999999?text=No+Image'">`
    : `<div class="card-img-top d-flex align-items-center justify-content-center bg-light text-muted small">No Image</div>`;
  const priceTag = item.price
    ? `<p class="${{soldout ? 'price-soldout' : 'price'}} mb-0">${{item.price}}</p>` : "";
  const allV   = item.variants_all       ? JSON.parse(item.variants_all)       : [];
  const availV = item.variants_available ? JSON.parse(item.variants_available) : [];
  const variantTag = allV.length ? (() => {{
    return allV.map(v => {{
      const ok = availV.includes(v);
      return `<span style="font-size:.65rem;padding:1px 5px;border-radius:3px;margin:1px;display:inline-block;
        background:${{ok ? '#e0f2fe' : '#f3f4f6'}};color:${{ok ? '#0369a1' : '#9ca3af'}};
        text-decoration:${{ok ? 'none' : 'line-through'}}">${{v}}</span>`;
    }}).join("");
  }})() : "";
  const pubDate = item.published_at || item.first_seen;  // Shopify 以外は first_seen で代替
  const publishedTag = pubDate ? (() => {{
    const d = new Date(pubDate);
    const label = d.toLocaleString("ja-JP", {{timeZone:"Asia/Tokyo",month:"numeric",day:"numeric",hour:"2-digit",minute:"2-digit"}});
    const prefix = item.published_at ? "発売" : "初回確認";
    return `<p class="text-muted mb-0" style="font-size:.68rem;">${{prefix}} ${{label}}</p>`;
  }})() : "";
  const soldoutTag = (() => {{
    if (!soldout || !item.soldout_at) return "";
    const baseDate = item.published_at || item.first_seen;
    if (!baseDate) return "";
    const diffMs = new Date(item.soldout_at) - new Date(baseDate);
    if (diffMs <= 0) return "";
    const h = Math.floor(diffMs / 3600000);
    const m = Math.floor((diffMs % 3600000) / 60000);
    const d = Math.floor(h / 24);
    const label = d > 0 ? `${{d}}日${{h % 24}}時間で完売` : h > 0 ? `${{h}}時間${{m}}分で完売` : `${{m}}分で完売`;
    return `<p class="text-danger mb-0" style="font-size:.68rem;font-weight:600;">⏱ ${{label}}</p>`;
  }})();
  // 人気度バッジ（SOLD OUT 時のみ）
  const popularityBadge = (() => {{
    if (!soldout) return "";
    const h = sellSpeedHours(item);
    if (h <= 1)   return `<span class="badge badge-hot">🔥 即完売</span>`;
    if (h <= 24)  return `<span class="badge badge-fast">⚡ 当日完売</span>`;
    if (h <= 168) return `<span class="badge badge-quick">💨 数日完売</span>`;
    return "";
  }})();
  const restockBadge = (item.restock_count && item.restock_count > 0)
    ? `<span class="badge" style="background:#8b5cf6;font-size:.65rem;">🔄 ${{item.restock_count}}回リストック</span>`
    : "";
  const ts = (item.last_seen || "").slice(0,16).replace("T"," ");
  return `<div class="col">
  <a href="${{item.item_url}}" target="_blank" rel="noopener"
     class="card h-100${{soldout ? ' card-soldout' : ''}}">
    ${{img}}
    <div class="card-body p-2">
      <div class="d-flex gap-1 mb-1 flex-wrap">
        <span class="badge ${{badgeCls}}">${{badgeTxt}}</span>
        ${{popularityBadge}}
        <span class="badge site-tag">${{item.site_name}}</span>
        ${{restockBadge}}
      </div>
      <p class="item-name mb-1">${{item.name}}</p>
      ${{priceTag}}
      ${{variantTag ? `<div class="mt-1">${{variantTag}}</div>` : ""}}
      ${{publishedTag}}
      ${{soldoutTag}}
    </div>
  </a>
</div>`;
}}

function updateStats(filtered) {{
  const active = ALL_ITEMS.filter(i => i.is_active);
  document.getElementById("stat-new").textContent     = active.filter(i => !i.is_restock && i.in_stock && isRecentNew(i)).length;
  document.getElementById("stat-restock").textContent = active.filter(i => i.is_restock && isRecentRestock(i)).length;
  document.getElementById("stat-soldout").textContent = active.filter(i => !i.in_stock).length;
  document.getElementById("stat-sites").textContent   = ALL_SITES.length;
  document.getElementById("count-label").textContent  = filtered.length + " 件表示中";
}}

function itemPriority(i) {{
  if (!i.in_stock)                               return 3;  // SOLD OUT
  if (i.is_restock && isRecentRestock(i))        return 1;  // リストック
  if (!i.is_restock && isRecentNew(i))           return 0;  // 新着
  return 2;                                                  // 在庫あり
}}

function render() {{
  const filtered = ALL_ITEMS
    .filter(i => matchStatus(i, currentStatus))
    .filter(i => selectedSites.has(i.site_name))
    .sort((a, b) => {{
      const pd = itemPriority(a) - itemPriority(b);
      if (pd !== 0) return pd;
      // SOLD OUT タブ: 完売速度順（速いほど上）、次にリストック回数順
      if (currentStatus === "soldout") {{
        const sa = sellSpeedHours(a), sb = sellSpeedHours(b);
        if (sa !== sb) return sa - sb;
        if ((b.restock_count || 0) !== (a.restock_count || 0))
          return (b.restock_count || 0) - (a.restock_count || 0);
      }}
      return (b.first_seen || "").localeCompare(a.first_seen || "");
    }});
  document.getElementById("grid").innerHTML = filtered.length
    ? filtered.map(cardHTML).join("")
    : `<div class="col-12 text-center py-5 text-muted"><p>アイテムがありません。</p></div>`;
  updateStats(filtered);
}}

// サイトチェックボックス
function saveSites() {{
  localStorage.setItem("selectedSites", JSON.stringify([...selectedSites]));
}}
const cbContainer = document.getElementById("site-checkboxes");
ALL_SITES.forEach(s => {{
  const id = "cb_" + s.replace(/\s+/g, "_");
  const wrap = document.createElement("div");
  wrap.className = "site-check d-flex align-items-center gap-1";
  wrap.innerHTML = `<input type="checkbox" id="${{id}}" value="${{s}}"${{selectedSites.has(s) ? " checked" : ""}}>
    <label for="${{id}}">${{s}}</label>`;
  wrap.querySelector("input").addEventListener("change", e => {{
    if (e.target.checked) selectedSites.add(s); else selectedSites.delete(s);
    saveSites(); render();
  }});
  cbContainer.appendChild(wrap);
}});
document.getElementById("site-all-btn").addEventListener("click", () => {{
  selectedSites = new Set(ALL_SITES);
  cbContainer.querySelectorAll("input").forEach(cb => cb.checked = true);
  saveSites(); render();
}});
document.getElementById("site-none-btn").addEventListener("click", () => {{
  selectedSites = new Set();
  cbContainer.querySelectorAll("input").forEach(cb => cb.checked = false);
  saveSites(); render();
}});

// Status buttons
document.getElementById("status-filters").addEventListener("click", e => {{
  const btn = e.target.closest("button[data-status]");
  if (!btn) return;
  currentStatus = btn.dataset.status;
  document.querySelectorAll("#status-filters button").forEach(b => {{
    b.className = "btn btn-outline-secondary";
  }});
  const activeClass = {{all:"btn-dark",new:"btn-success",restock:"btn-warning",soldout:"btn-secondary"}}[currentStatus] || "btn-dark";
  btn.className = "btn " + activeClass;
  render();
}});

// Render scrape log
if (SCRAPE_LOG.length) {{
  document.getElementById("log-section").style.display = "";
  document.getElementById("log-body").innerHTML = SCRAPE_LOG.map(r => `
    <tr class="${{r.error ? 'table-danger' : ''}}">
      <td>${{r.site_name}}</td>
      <td>${{(r.scraped_at||"").slice(0,16).replace("T"," ")}}</td>
      <td>${{r.items_found}}</td>
      <td>${{r.new_items}}</td>
      <td>${{r.restock_items}}</td>
      <td>${{r.error || ""}}</td>
    </tr>`).join("");
}}

render();

// 自動リロード: 5分ごとにページの更新タイムスタンプを確認し、新しければリロード
const CURRENT_UPDATED = "{updated}";
setInterval(async () => {{
  try {{
    const res = await fetch(location.href, {{ cache: "no-store" }});
    const text = await res.text();
    const m = text.match(/const CURRENT_UPDATED = "([^"]+)"/);
    if (m && m[1] !== CURRENT_UPDATED) location.reload();
  }} catch (e) {{ /* ネットワークエラーは無視 */ }}
}}, 5 * 60 * 1000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    from storage.database import init_db
    init_db()
    generate()
