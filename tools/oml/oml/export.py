"""Distribution exports: CASE 1.1, JSON Lines, CSV."""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .loader import load_records

CASE_ITEM_TYPE_MISCONCEPTION = "Misconception"
CASE_ITEM_TYPE_DOMAIN = "Domain"

# Education level vocabulary for CASE `educationLevel` (strings; CASE leaves the vocabulary open).
LEVEL_BAND_TO_CASE = {
    "early-primary": ["K", "01", "02"],
    "primary": ["03", "04", "05"],
    "middle": ["06", "07", "08"],
    "secondary": ["09", "10"],
    "upper-secondary": ["11", "12"],
    "undergraduate": ["UG"],
    "graduate": ["PG"],
    "adult": ["AE"],
    "any": [],
}

DOMAIN_TITLES = {
    "math": "Mathematics",
    "prog": "Programming",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_all(config: Config) -> list[dict]:
    records = [r.data for r in load_records(config.records_dir) if r.data]
    records.sort(key=lambda r: r["id"])
    return records


def _ns(config: Config) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, config.base_uri)


def stable_uuid(config: Config, *parts: str) -> str:
    return str(uuid.uuid5(_ns(config), "/".join(parts)))


def _link(config: Config, kind: str, identifier: str, title: str) -> dict:
    return {"title": title, "identifier": identifier, "uri": f"{config.base_uri}/ims/case/v1p1/{kind}/{identifier}"}


def build_case(config: Config, records: list[dict], version: str | None = None) -> dict:
    """Build a CASE 1.1 CFPackage for the whole library."""
    version = version or config.library_version
    now = _now()
    doc_id = stable_uuid(config, "CFDocument")
    doc_link = _link(config, "CFDocuments", doc_id, config.title)

    item_type_ids = {
        CASE_ITEM_TYPE_MISCONCEPTION: stable_uuid(config, "CFItemType", CASE_ITEM_TYPE_MISCONCEPTION),
        CASE_ITEM_TYPE_DOMAIN: stable_uuid(config, "CFItemType", CASE_ITEM_TYPE_DOMAIN),
    }

    def item_type_link(name: str) -> dict:
        return _link(config, "CFItemTypes", item_type_ids[name], name)

    license_id = stable_uuid(config, "CFLicense", config.license)
    license_link = _link(config, "CFLicenses", license_id, config.license)

    cf_document = {
        "identifier": doc_id,
        "uri": doc_link["uri"],
        "creator": config.creator,
        "title": config.title,
        "lastChangeDateTime": now,
        "officialSourceURL": config.base_uri,
        "publisher": config.creator,
        "description": (
            "A public catalogue of misconceptions with stable IDs. One CFItem per "
            "misconception; humanCodingScheme carries the oml: identifier."
        ),
        "subject": sorted({DOMAIN_TITLES.get(r["id"].split(".")[0], r["id"].split(".")[0]) for r in records}),
        "language": "en",
        "version": version,
        "adoptionStatus": "Draft",
        "licenseURI": license_link,
        "notes": f"Generated from records/ by oml export case. {len(records)} records.",
        "CFPackageURI": _link(config, "CFPackages", doc_id, config.title),
    }

    cf_items: list[dict] = []
    cf_associations: list[dict] = []
    seq = 0

    assoc_keys: set[str] = set()

    def assoc(kind: str, origin: dict, dest: dict, key: str, notes: str | None = None) -> None:
        nonlocal seq
        if key in assoc_keys:
            return
        assoc_keys.add(key)
        seq += 1
        ident = stable_uuid(config, "CFAssociation", key)
        a = {
            "identifier": ident,
            "uri": f"{config.base_uri}/ims/case/v1p1/CFAssociations/{ident}",
            "associationType": kind,
            "sequenceNumber": seq,
            "originNodeURI": origin,
            "destinationNodeURI": dest,
            "CFDocumentURI": doc_link,
            "lastChangeDateTime": now,
        }
        if notes:
            a["notes"] = notes
        cf_associations.append(a)

    # Per-domain grouping items, children of the document.
    domain_links: dict[str, dict] = {}
    for domain in sorted({r["id"].split(".")[0] for r in records}):
        ident = stable_uuid(config, "CFItem", "domain", domain)
        title = DOMAIN_TITLES.get(domain, domain)
        link = _link(config, "CFItems", ident, title)
        domain_links[domain] = link
        cf_items.append(
            {
                "identifier": ident,
                "uri": link["uri"],
                "fullStatement": title,
                "humanCodingScheme": f"oml:{domain}",
                "CFItemType": CASE_ITEM_TYPE_DOMAIN,
                "CFItemTypeURI": item_type_link(CASE_ITEM_TYPE_DOMAIN),
                "language": "en",
                "lastChangeDateTime": now,
                "CFDocumentURI": doc_link,
            }
        )
        assoc("isChildOf", link, doc_link, f"isChildOf/{domain}/document")

    record_links: dict[str, dict] = {}
    for r in records:
        record_links[r["id"]] = _link(config, "CFItems", r["uuid"], r["title"])

    for r in records:
        domain = r["id"].split(".")[0]
        link = record_links[r["id"]]
        first = r["evidence_patterns"][0]
        notes = (
            f"kind: {r['kind']}. status: {r['status']}. trust: {r.get('trust', 'low')}. "
            f"Evidence: on '{first['item_shape']}', {first['signature']}. "
            f"Example: {first['example']['item']} -> {first['example']['response']} "
            f"(expected {first['example']['expected']})."
        )
        education = sorted({lvl for band in r.get("level_band", []) for lvl in LEVEL_BAND_TO_CASE.get(band, [])})
        item = {
            "identifier": r["uuid"],
            "uri": link["uri"],
            "fullStatement": r["statement"],
            "abbreviatedStatement": r["title"],
            "humanCodingScheme": f"oml:{r['id']}",
            "CFItemType": CASE_ITEM_TYPE_MISCONCEPTION,
            "CFItemTypeURI": item_type_link(CASE_ITEM_TYPE_MISCONCEPTION),
            "notes": notes,
            "language": r.get("locale", "en"),
            "lastChangeDateTime": now,
            "CFDocumentURI": doc_link,
            "statusStartDate": None,
        }
        item = {k: v for k, v in item.items() if v is not None}
        if education:
            item["educationLevel"] = education
        cf_items.append(item)

        # Hierarchy: a record that specializes another sits under it; otherwise under its domain.
        specializes = [t for t in (r.get("relations") or {}).get("specializes", []) if t in record_links]
        if specializes:
            parent = record_links[specializes[0]]
            assoc("isChildOf", link, parent, f"isChildOf/{r['id']}/{specializes[0]}", notes="oml relation: specializes")
            for extra in specializes[1:]:
                assoc("isRelatedTo", link, record_links[extra], f"isRelatedTo/{r['id']}/specializes/{extra}", notes="oml relation: specializes (secondary parent)")
        else:
            assoc("isChildOf", link, domain_links[domain], f"isChildOf/{r['id']}/{domain}")

        for al in r.get("alignments", []):
            if al.get("uri"):
                dest = {"title": al.get("code") or al["scheme"], "identifier": al.get("guid") or stable_uuid(config, "ext", al["uri"]), "uri": al["uri"]}
                assoc(
                    "isRelatedTo",
                    link,
                    dest,
                    f"isRelatedTo/{r['id']}/{al['scheme']}/{al['uri']}",
                    notes=f"alignment scheme={al['scheme']} relation={al.get('relation', 'about')}",
                )

        for rel_name, targets in (r.get("relations") or {}).items():
            if rel_name == "specializes":
                continue  # exported as isChildOf above
            for t in targets:
                if isinstance(t, str) and t in record_links:
                    # confusable_with is symmetric: emit both directions, deduplicated by key.
                    for a, b in ((r["id"], t), (t, r["id"])):
                        assoc(
                            "isRelatedTo",
                            record_links[a],
                            record_links[b],
                            f"isRelatedTo/{a}/{rel_name}/{b}",
                            notes=f"oml relation: {rel_name}",
                        )
                elif isinstance(t, dict) and t.get("external"):
                    dest = {"title": t.get("label") or t["external"], "identifier": stable_uuid(config, "ext", t["external"]), "uri": t["external"]}
                    assoc(
                        "isRelatedTo",
                        link,
                        dest,
                        f"isRelatedTo/{r['id']}/{rel_name}/{t['external']}",
                        notes=f"oml relation: {rel_name}",
                    )

    cf_definitions = {
        "CFConcepts": [],
        "CFSubjects": [],
        "CFLicenses": [
            {
                "identifier": license_id,
                "uri": license_link["uri"],
                "title": "Creative Commons Attribution 4.0 International",
                "description": config.license_uri,
                "licenseText": f"This work is licensed under CC BY 4.0. See {config.license_uri}",
                "lastChangeDateTime": now,
            }
        ],
        "CFItemTypes": [
            {
                "identifier": item_type_ids[name],
                "uri": item_type_link(name)["uri"],
                "title": name,
                "description": desc,
                "hierarchyCode": code,
                "typeCode": name,
                "lastChangeDateTime": now,
            }
            for name, desc, code in (
                (CASE_ITEM_TYPE_DOMAIN, "Grouping of misconceptions by subject domain.", "1"),
                (CASE_ITEM_TYPE_MISCONCEPTION, "A false but stable belief that produces predictable wrong answers.", "2"),
            )
        ],
        "CFAssociationGroupings": [],
    }

    return {
        "CFDocument": cf_document,
        "CFItems": cf_items,
        "CFAssociations": cf_associations,
        "CFDefinitions": cf_definitions,
    }


CSV_COLUMNS = [
    "id", "uri", "uuid", "version", "status", "title", "statement", "kind", "domain",
    "level_band", "example_item", "example_expected", "example_response",
    "n_evidence_patterns", "n_sources", "first_source", "trust", "n_reviews", "last_review_date", "license",
]


def record_to_csv_row(r: dict) -> dict:
    ex = r["evidence_patterns"][0]["example"]
    sources = r["provenance"]["sources"]
    return {
        "id": r["id"],
        "uri": r["uri"],
        "uuid": r["uuid"],
        "version": r["version"],
        "status": r["status"],
        "title": r["title"],
        "statement": r["statement"],
        "kind": r["kind"],
        "domain": r["domain"],
        "level_band": ";".join(r.get("level_band", [])),
        "example_item": ex["item"],
        "example_expected": ex["expected"],
        "example_response": ex["response"],
        "n_evidence_patterns": len(r["evidence_patterns"]),
        "n_sources": len(sources),
        "first_source": sources[0]["citation"] if sources else "",
        "trust": r.get("trust", "low"),
        "n_reviews": len(r.get("reviews") or []),
        "last_review_date": max((rv["date"] for rv in (r.get("reviews") or [])), default=""),
        "license": r["license"],
    }


def export(config: Config, fmt: str, version: str | None = None, out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or config.dist_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    records = load_all(config)
    written: list[Path] = []

    if fmt in ("case", "all"):
        from .case_check import check_case_package

        pkg = build_case(config, records, version)
        problems = check_case_package(pkg)
        if problems:
            raise ValueError("CASE package failed structural check:\n  " + "\n  ".join(problems))
        path = out_dir / "oml.case.json"
        path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(path)

    if fmt in ("jsonl", "all"):
        path = out_dir / "oml.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps({k: v for k, v in r.items() if k != "$schema"}, ensure_ascii=False) + "\n")
        written.append(path)

    if fmt in ("csv", "all"):
        path = out_dir / "oml.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            w.writeheader()
            for r in records:
                w.writerow(record_to_csv_row(r))
        written.append(path)

    return written
