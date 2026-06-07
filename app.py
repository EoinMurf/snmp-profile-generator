#!/usr/bin/env python3
"""
SNMP Profile Generator — local backend
Serves the UI and proxies OID lookups to mibs.observium.org (no CORS restriction).

Usage:
    pip install flask
    python app.py
    open http://localhost:7788
"""
import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

_cache: dict = {}  # simple in-process OID → result cache

HERE = os.path.dirname(os.path.abspath(__file__))


def _fetch_one(oid: str):
    """Resolve a single numeric OID via the Observium MIB browser API."""
    if oid in _cache:
        return oid, _cache[oid]

    url = f"https://mibs.observium.org/v2/api/search.php?q={oid}&limit=1"
    req = urllib.request.Request(
        url, headers={"User-Agent": "SNMP-Profile-Generator/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
    except (urllib.error.URLError, json.JSONDecodeError):
        _cache[oid] = None
        return oid, None

    result = None
    for res in data.get("results", []):
        if res.get("oid") == oid:  # exact OID match only
            result = {
                "name": res["name"],
                "mib": res["mib"],
                "object_type": res.get("object_type", ""),
                "syntax": res.get("syntax_name", ""),
                "description": (res.get("description") or "")[:160].replace("\n", " "),
                "units": res.get("units", ""),
            }
            break

    _cache[oid] = result
    return oid, result


@app.route("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.route("/health")
def health():
    return jsonify({"ok": True, "mib_source": "mibs.observium.org"})


@app.route("/resolve-oids", methods=["POST"])
def resolve_oids():
    """
    Body: { "oids": ["1.3.6.1.4.1.9.9.109.1.1.1.1.2", ...] }
    Returns: { "1.3.6.1...": { name, mib, object_type, syntax, description, units } }
    """
    oids = list(set(request.json.get("oids", [])))[:120]  # cap per request
    results = {}

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch_one, oid): oid for oid in oids}
        for f in as_completed(futures):
            oid, result = f.result()
            if result:
                results[oid] = result

    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7788))
    print("─" * 50)
    print(f"  SNMP Profile Generator  →  http://localhost:{port}")
    print("  MIB lookup: mibs.observium.org")
    print("─" * 50)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
