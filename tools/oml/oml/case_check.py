"""Structural conformance check for a CASE 1.1 CFPackage.

This is not the official 1EdTech JSON Schema (which is distributed to members);
it checks the required fields and vocabularies of the CASE 1.1 REST/JSON
binding that a CASE consumer relies on to import a package.
"""

from __future__ import annotations

import re

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")

ASSOCIATION_TYPES = {
    "isChildOf", "isPeerOf", "isPartOf", "exactMatchOf", "precedes", "isRelatedTo",
    "replacedBy", "exemplar", "hasSkillLevel",
}
ADOPTION_STATUSES = {"Draft", "Private Draft", "Adopted", "Deprecated"}

LINK_URI_REQUIRED = ("title", "identifier", "uri")
CFDOCUMENT_REQUIRED = ("identifier", "uri", "creator", "title", "lastChangeDateTime")
CFITEM_REQUIRED = ("identifier", "uri", "lastChangeDateTime", "CFDocumentURI")
CFASSOCIATION_REQUIRED = (
    "identifier", "uri", "associationType", "originNodeURI", "destinationNodeURI", "lastChangeDateTime",
)


def _require(obj: dict, keys, where: str, errors: list[str]) -> None:
    for k in keys:
        if k not in obj or obj[k] in (None, ""):
            errors.append(f"{where}: missing {k}")


def _check_link(obj, where: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{where}: LinkURI must be an object")
        return
    _require(obj, LINK_URI_REQUIRED, where, errors)


def check_case_package(pkg: dict) -> list[str]:
    errors: list[str] = []
    for key in ("CFDocument", "CFItems", "CFAssociations"):
        if key not in pkg:
            errors.append(f"package: missing {key}")
    if errors:
        return errors

    doc = pkg["CFDocument"]
    _require(doc, CFDOCUMENT_REQUIRED, "CFDocument", errors)
    if not UUID_RE.match(str(doc.get("identifier", ""))):
        errors.append("CFDocument: identifier is not a UUID")
    if not DATETIME_RE.match(str(doc.get("lastChangeDateTime", ""))):
        errors.append("CFDocument: lastChangeDateTime is not an ISO 8601 datetime")
    if doc.get("adoptionStatus") and doc["adoptionStatus"] not in ADOPTION_STATUSES:
        errors.append(f"CFDocument: adoptionStatus {doc['adoptionStatus']!r} not in {sorted(ADOPTION_STATUSES)}")
    if "licenseURI" in doc:
        _check_link(doc["licenseURI"], "CFDocument.licenseURI", errors)

    item_ids: set[str] = set()
    for i, item in enumerate(pkg["CFItems"]):
        where = f"CFItems[{i}]"
        _require(item, CFITEM_REQUIRED, where, errors)
        if not UUID_RE.match(str(item.get("identifier", ""))):
            errors.append(f"{where}: identifier is not a UUID")
        if item.get("identifier") in item_ids:
            errors.append(f"{where}: duplicate identifier {item['identifier']}")
        item_ids.add(item.get("identifier"))
        if not item.get("fullStatement") and not item.get("humanCodingScheme"):
            errors.append(f"{where}: needs fullStatement or humanCodingScheme")
        _check_link(item.get("CFDocumentURI"), f"{where}.CFDocumentURI", errors)
        if (item.get("CFDocumentURI") or {}).get("identifier") != doc.get("identifier"):
            errors.append(f"{where}: CFDocumentURI does not point at the package CFDocument")
        if "CFItemTypeURI" in item:
            _check_link(item["CFItemTypeURI"], f"{where}.CFItemTypeURI", errors)
        if "educationLevel" in item and not (
            isinstance(item["educationLevel"], list) and all(isinstance(x, str) for x in item["educationLevel"])
        ):
            errors.append(f"{where}: educationLevel must be a list of strings")

    parents_seen: set[str] = set()
    assoc_ids: set[str] = set()
    for i, a in enumerate(pkg["CFAssociations"]):
        where = f"CFAssociations[{i}]"
        _require(a, CFASSOCIATION_REQUIRED, where, errors)
        if a.get("identifier") in assoc_ids:
            errors.append(f"{where}: duplicate identifier {a['identifier']}")
        assoc_ids.add(a.get("identifier"))
        if a.get("associationType") not in ASSOCIATION_TYPES:
            errors.append(f"{where}: associationType {a.get('associationType')!r} not in CASE vocabulary")
        _check_link(a.get("originNodeURI"), f"{where}.originNodeURI", errors)
        _check_link(a.get("destinationNodeURI"), f"{where}.destinationNodeURI", errors)
        origin = (a.get("originNodeURI") or {}).get("identifier")
        if origin not in item_ids and origin != doc.get("identifier"):
            errors.append(f"{where}: originNodeURI {origin} is not an item in this package")
        if a.get("associationType") == "isChildOf":
            if origin in parents_seen:
                errors.append(f"{where}: item {origin} has more than one isChildOf")
            parents_seen.add(origin)
            dest = (a.get("destinationNodeURI") or {}).get("identifier")
            if dest not in item_ids and dest != doc.get("identifier"):
                errors.append(f"{where}: isChildOf destination {dest} is not in this package")

    for item_id in item_ids:
        if item_id not in parents_seen:
            errors.append(f"CFItem {item_id} has no isChildOf association (orphan)")

    defs = pkg.get("CFDefinitions", {})
    for t in defs.get("CFItemTypes", []):
        _require(t, ("identifier", "uri", "title", "lastChangeDateTime"), "CFItemTypes", errors)
    for lic in defs.get("CFLicenses", []):
        _require(lic, ("identifier", "uri", "title", "licenseText", "lastChangeDateTime"), "CFLicenses", errors)

    return errors
