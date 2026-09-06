"""Static site: one page per record at its stable URI, plus home and schema pages.

Output layout (GitHub Pages serves `m/<id>.html` at `/m/<id>`):

    index.html
    m/<id>.html           human page
    m/<id>.json           the record
    schema/index.html     both schemas rendered
    schema/*.schema.json
    oml.case.json, oml.jsonl, oml.csv
    records.json          [{id, uri, title, kind, status}]
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .config import Config
from .export import build_case, export, load_all

CSS = """
:root{--fg:#1a1a1a;--bg:#fff;--muted:#555;--line:#ddd;--accent:#0b5cad;--code:#f4f4f4;color-scheme:light dark}
@media (prefers-color-scheme:dark){:root{--fg:#e8e8e8;--bg:#121212;--muted:#aaa;--line:#333;--accent:#7ab7ff;--code:#1e1e1e}}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--fg);background:var(--bg)}
header,main,footer{max-width:60rem;margin:0 auto;padding:1rem 1.25rem}
header{border-bottom:1px solid var(--line)} footer{border-top:1px solid var(--line);color:var(--muted);font-size:.9rem}
header nav a{margin-right:1rem}
a{color:var(--accent)} a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
h1{font-size:1.75rem;line-height:1.25;margin:.5rem 0} h2{font-size:1.2rem;margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.25rem}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.95em;background:var(--code);border-radius:4px}
code{padding:.1em .3em} pre{padding:.75rem;overflow-x:auto}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.35rem 1.25rem} dt{color:var(--muted)} dd{margin:0}
table{border-collapse:collapse;width:100%} th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid var(--line);vertical-align:top}
.statement{font-size:1.15rem;padding:1rem;border-left:4px solid var(--accent);background:var(--code);margin:1rem 0}
.badge{display:inline-block;padding:.1em .5em;border:1px solid var(--line);border-radius:999px;font-size:.85rem}
.example{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:.5rem;margin:.5rem 0}
.example div{padding:.5rem;background:var(--code);border-radius:4px} .example span{display:block;color:var(--muted);font-size:.85rem}
.muted{color:var(--muted)}
.disputed{padding:.75rem 1rem;border-left:4px solid #b8860b;background:var(--code);border-radius:4px}
@media (prefers-color-scheme:dark){.disputed{border-left-color:#e0b040}}
@media (max-width:40rem){dl{grid-template-columns:1fr} dt{margin-top:.5rem}}
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def page(config: Config, title: str, body: str, *, description: str = "", canonical: str = "", extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{f'<meta name="description" content="{esc(description)}">' if description else ''}
{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''}
{extra_head}
<style>{CSS}</style>
</head>
<body>
<header>
<nav aria-label="Site"><a href="{config.base_uri}/">{esc(config.title)}</a> <a href="{config.base_uri}/records.html">Records</a> <a href="{config.base_uri}/schema/">Schema</a> <a href="https://github.com/open-misconceptions/oml">GitHub</a></nav>
</header>
<main id="main">
{body}
</main>
<footer>
<p>Records are <a href="{esc(config.license_uri)}">{esc(config.license)}</a>. Tooling is MIT. Library version {esc(config.library_version)}.</p>
<p><a href="https://github.com/open-misconceptions/oml/blob/main/GOVERNANCE.md">Governance</a> · <a href="https://github.com/open-misconceptions/oml/blob/main/CONTRIBUTING.md">How to propose a record</a> · <a href="https://github.com/open-misconceptions/oml">Source</a></p>
</footer>
</body>
</html>
"""


def _record_link(config: Config, rid: str, by_id: dict[str, dict]) -> str:
    if rid in by_id:
        return f'<a href="{config.record_uri(rid)}"><code>{esc(rid)}</code></a>'
    return f"<code>{esc(rid)}</code>"


def _target_html(config: Config, t, by_id: dict[str, dict]) -> str:
    if isinstance(t, str):
        return _record_link(config, t, by_id)
    label = t.get("label") or t["external"]
    return f'<a href="{esc(t["external"])}" rel="external">{esc(label)}</a> <span class="muted">(external)</span>'


def render_record(config: Config, r: dict, by_id: dict[str, dict]) -> str:
    rid = r["id"]
    parts: list[str] = []
    parts.append(f'<p class="muted"><code>oml:{esc(rid)}</code> · <span class="badge">{esc(r["status"])}</span> · trust <span class="badge">{esc(r.get("trust", "low"))}</span> · v{esc(r["version"])} · kind <code>{esc(r["kind"])}</code>' + (' · <span class="badge">disputed</span>' if r.get("disputed") else "") + '</p>')
    parts.append(f"<h1>{esc(r['title'])}</h1>")
    parts.append(f'<blockquote class="statement"><p>{esc(r["statement"])}</p></blockquote>')
    if r.get("notes"):
        parts.append(f'<p class="muted">{esc(r["notes"])}</p>')
    if r.get("disputed"):
        links = " ".join(f'<a href="{esc(u)}" rel="external">dispute</a>' for u in (r.get("disputes") or []))
        parts.append(
            '<p class="disputed"><strong>Disputed.</strong> An open dispute challenges this record. '
            "It stays live and citable while the argument runs; the ruling is recorded in its changelog. "
            f"{links}</p>"
        )

    dl = [
        ("Stable URI", f'<a href="{esc(r["uri"])}">{esc(r["uri"])}</a>'),
        ("UUID", f"<code>{esc(r['uuid'])}</code>"),
        ("Domain", f"<code>{esc(r['domain'])}</code>"),
    ]
    if r.get("level_band"):
        dl.append(("Level band", ", ".join(esc(x) for x in r["level_band"])))
    if r.get("locale"):
        dl.append(("Locale", esc(r["locale"])))
    if r.get("about"):
        dl.append(("About", "<br>".join(f'<a href="{esc(a["uri"])}">{esc(a.get("label") or a["uri"])}</a> <span class="muted">({esc(a["scheme"])})</span>' for a in r["about"])))
    parts.append("<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in dl) + "</dl>")

    parts.append("<h2>Evidence patterns</h2>")
    for i, ep in enumerate(r["evidence_patterns"]):
        ex = ep["example"]
        parts.append(f"<h3>Pattern {i}: {esc(ep['item_shape'])}</h3>")
        parts.append(f"<p>{esc(ep['signature'])}</p>")
        parts.append(
            '<div class="example" role="group" aria-label="Example">'
            f'<div><span>Item</span><code>{esc(ex["item"])}</code></div>'
            f'<div><span>Expected</span><code>{esc(ex["expected"])}</code></div>'
            f'<div><span>Response</span><code>{esc(ex["response"])}</code></div></div>'
        )
        if ep.get("notes"):
            parts.append(f'<p class="muted">{esc(ep["notes"])}</p>')

    disc = r.get("discriminators") or {}
    if disc:
        parts.append("<h2>Discriminators</h2>")
        if disc.get("vs_slip"):
            parts.append(f"<p><strong>vs a slip.</strong> {esc(disc['vs_slip'])}</p>")
        for nid, text in (disc.get("vs") or {}).items():
            parts.append(f"<p><strong>vs {_record_link(config, nid, by_id)}.</strong> {esc(text)}</p>")

    rels = r.get("relations") or {}
    if rels:
        parts.append("<h2>Relations</h2><dl>")
        for name, targets in rels.items():
            parts.append(f"<dt><code>{esc(name)}</code></dt><dd>" + "<br>".join(_target_html(config, t, by_id) for t in targets) + "</dd>")
        parts.append("</dl>")

    if r.get("alignments"):
        parts.append("<h2>Alignments</h2><ul>")
        for al in r["alignments"]:
            label = f"{al['scheme']} {al.get('code', '')}".strip()
            href = al.get("uri")
            li = f'<a href="{esc(href)}" rel="external">{esc(label)}</a>' if href else f"{esc(label)} <code>{esc(al.get('guid', ''))}</code>"
            if al.get("relation"):
                li += f' <span class="muted">({esc(al["relation"])})</span>'
            if al.get("note"):
                li += f"<br><span class='muted'>{esc(al['note'])}</span>"
            parts.append(f"<li>{li}</li>")
        parts.append("</ul>")

    prov = r["provenance"]
    parts.append(f"<h2>Provenance</h2><p>Origin: <code>{esc(prov['origin'])}</code></p><ol>")
    for s in prov["sources"]:
        li = esc(s["citation"])
        if s.get("doi"):
            li += f' <a href="https://doi.org/{esc(s["doi"])}" rel="external">doi:{esc(s["doi"])}</a>'
        elif s.get("url"):
            li += f' <a href="{esc(s["url"])}" rel="external">link</a>'
        if s.get("identifier"):
            li += f" <code>{esc(s['identifier'])}</code>"
        if s.get("note"):
            li += f"<br><span class='muted'>{esc(s['note'])}</span>"
        parts.append(f"<li>{li}</li>")
    parts.append("</ol>")
    if prov.get("notes"):
        parts.append(f'<p class="muted">{esc(prov["notes"])}</p>')

    parts.append("<h2>Review status</h2>")
    parts.append(f"<p>Status <span class='badge'>{esc(r['status'])}</span>, trust <span class='badge'>{esc(r.get('trust', 'low'))}</span> (computed from the reviews below against the reviewer registry).</p>")
    reviews = r.get("reviews") or []
    if reviews:
        parts.append("<table><thead><tr><th scope='col'>kind</th><th scope='col'>by</th><th scope='col'>date</th><th scope='col'>scope</th><th scope='col'>verdict</th><th scope='col'>notes</th></tr></thead><tbody>")
        srcs = r["provenance"]["sources"]
        for rv in reviews:
            by = rv["by"]
            if rv["kind"] == "attested" and isinstance(by, int) and 0 <= by < len(srcs):
                by = f"source {by}: {srcs[by]['citation'][:80]}"
            parts.append(f"<tr><td>{esc(rv['kind'])}</td><td>{esc(by)}</td><td>{esc(rv['date'])}</td><td>{esc(', '.join(rv['scope']))}</td><td>{esc(rv['verdict'])}</td><td>{esc(rv.get('notes', ''))}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p>No reviews yet.</p>")
    hist = r.get("history") or {}
    if hist.get("merged_into"):
        parts.append(f"<p>Merged into {_record_link(config, hist['merged_into'], by_id)}.</p>")
    if hist.get("deprecated_reason"):
        parts.append(f"<p>Deprecated: {esc(hist['deprecated_reason'])}</p>")
    if hist.get("supersedes"):
        parts.append("<p>Supersedes " + ", ".join(_record_link(config, x, by_id) for x in hist["supersedes"]) + ".</p>")

    domain, _, rest = rid.partition(".")
    parts.append("<h2>Formats</h2><ul>")
    parts.append(f'<li><a href="{esc(r["uri"])}.json">Raw JSON</a></li>')
    parts.append(f'<li><a href="{config.base_uri}/oml.case.json">CASE 1.1 package</a> (CFItem <code>{esc(r["uuid"])}</code>)</li>')
    parts.append(f'<li><a href="https://github.com/open-misconceptions/oml/blob/main/records/{esc(domain)}/{esc(rest)}.json">Source on GitHub</a></li>')
    parts.append("</ul>")
    parts.append(f"<h2>Cite</h2><pre><code>oml:{esc(rid)}\n{esc(r['uri'])}</code></pre>")

    ld = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": r["title"],
        "description": r["statement"],
        "termCode": f"oml:{rid}",
        "url": r["uri"],
        "identifier": r["uuid"],
        "inDefinedTermSet": {"@type": "DefinedTermSet", "name": config.title, "url": config.base_uri},
        "license": config.license_uri,
    }
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return page(config, f"{r['title']} · oml:{rid}", "\n".join(parts), description=r["statement"], canonical=r["uri"], extra_head=extra)


def render_home(config: Config, records: list[dict], readme_paragraph: str) -> str:
    n = len(records)
    by_status: dict[str, int] = {}
    for r in records:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    status_line = ", ".join(f"{v} {k}" for k, v in sorted(by_status.items()))
    body = f"""
<h1>{esc(config.title)}</h1>
<p>{esc(readme_paragraph)}</p>
<p><strong>{n} records</strong> ({esc(status_line)}). <a href="{config.base_uri}/records.html">See the index.</a></p>
<h2>How to cite a record</h2>
<pre><code>oml:math.frac.add-across
{config.base_uri}/m/math.frac.add-across</code></pre>
<h2>How to consume</h2>
<ul>
<li>One record: <code>{config.base_uri}/m/&lt;id&gt;.json</code></li>
<li>All records: <a href="{config.base_uri}/oml.jsonl">JSON Lines</a> · <a href="{config.base_uri}/oml.csv">CSV</a> · <a href="{config.base_uri}/records.json">index JSON</a></li>
<li>CASE 1.1 framework: <a href="{config.base_uri}/oml.case.json">oml.case.json</a></li>
<li>Schemas: <a href="{config.base_uri}/schema/">record and diagnosis</a></li>
</ul>
<h2>How to contribute</h2>
<p>One record per pull request. Read <a href="https://github.com/open-misconceptions/oml/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a> for the review checklist.</p>
"""
    return page(config, config.title, body, description=readme_paragraph, canonical=config.base_uri + "/")


def render_records_index(config: Config, records: list[dict]) -> str:
    rows = "".join(
        f'<tr><td><a href="{esc(r["uri"])}"><code>{esc(r["id"])}</code></a></td><td>{esc(r["title"])}</td><td><code>{esc(r["kind"])}</code></td><td><span class="badge">{esc(r["status"])}</span></td><td><span class="badge">{esc(r.get("trust", "low"))}</span></td></tr>'
        for r in records
    )
    body = f"""
<h1>Records</h1>
<p>{len(records)} records. Also as <a href="{config.base_uri}/records.json">JSON</a>.</p>
<table><caption class="muted">All records, by id</caption><thead><tr><th scope="col">id</th><th scope="col">title</th><th scope="col">kind</th><th scope="col">status</th><th scope="col">trust</th></tr></thead><tbody>{rows}</tbody></table>
"""
    return page(config, f"Records · {config.title}", body, canonical=config.base_uri + "/records.html")


def render_schema_page(config: Config, schemas: dict[str, dict]) -> str:
    parts = ["<h1>Schemas</h1><p>JSON Schema 2020-12. Field-by-field notes are in <a href='https://github.com/open-misconceptions/oml/blob/main/schema/README.md'>schema/README.md</a>.</p>"]
    for name, schema in schemas.items():
        parts.append(f"<h2 id='{esc(name)}'>{esc(schema.get('title', name))}</h2>")
        parts.append(f"<p>{esc(schema.get('description', ''))} <a href='{config.base_uri}/schema/{esc(name)}'>Download</a></p>")
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        parts.append("<table><thead><tr><th scope='col'>field</th><th scope='col'>required</th><th scope='col'>description</th></tr></thead><tbody>")
        for field, spec in props.items():
            if field == "$schema":
                continue
            parts.append(f"<tr><td><code>{esc(field)}</code></td><td>{'yes' if field in required else ''}</td><td>{esc(spec.get('description', ''))}</td></tr>")
        parts.append("</tbody></table>")
        parts.append(f"<details><summary>Full schema</summary><pre><code>{esc(json.dumps(schema, indent=2))}</code></pre></details>")
    return page(config, f"Schemas · {config.title}", "\n".join(parts), canonical=config.base_uri + "/schema/")


def readme_first_paragraph(config: Config) -> str:
    text = (config.root / "README.md").read_text(encoding="utf-8")
    paras = [p.strip() for p in text.split("\n\n")]
    for p in paras:
        if p and not p.startswith("#") and not p.startswith("[!"):
            return " ".join(p.split())
    return config.title


def build_site(config: Config, out_dir: Path | None = None) -> Path:
    out = out_dir or (config.site_dir / "_build")
    if out.exists():
        shutil.rmtree(out)
    (out / "m").mkdir(parents=True)
    (out / "schema").mkdir(parents=True)

    records = load_all(config)
    by_id = {r["id"]: r for r in records}

    for r in records:
        (out / "m" / f"{r['id']}.html").write_text(render_record(config, r, by_id), encoding="utf-8")
        (out / "m" / f"{r['id']}.json").write_text(json.dumps({k: v for k, v in r.items() if k != "$schema"}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (out / "index.html").write_text(render_home(config, records, readme_first_paragraph(config)), encoding="utf-8")
    (out / "records.html").write_text(render_records_index(config, records), encoding="utf-8")
    (out / "records.json").write_text(
        json.dumps([{"id": r["id"], "uri": r["uri"], "uuid": r["uuid"], "title": r["title"], "kind": r["kind"], "status": r["status"], "trust": r.get("trust", "low")} for r in records], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    schemas = {}
    for name in ("oml-record.schema.json", "diagnosis-record.schema.json"):
        src = config.schema_dir / name
        shutil.copy(src, out / "schema" / name)
        schemas[name] = json.loads(src.read_text(encoding="utf-8"))
    (out / "schema" / "index.html").write_text(render_schema_page(config, schemas), encoding="utf-8")

    export(config, "all", out_dir=out)
    (out / ".nojekyll").write_text("")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {config.base_uri}/sitemap.txt\n")
    (out / "sitemap.txt").write_text("\n".join([config.base_uri + "/", config.base_uri + "/records.html", config.base_uri + "/schema/", *[r["uri"] for r in records]]) + "\n")
    static = config.site_dir / "static"
    if static.is_dir():
        shutil.copytree(static, out, dirs_exist_ok=True)
    return out
