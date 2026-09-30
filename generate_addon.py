#!/usr/bin/env python3
"""Generate the static AJO Live Stremio addon files from the AJO channel feed.

Reads channels.json ({updated, channels:[{n,l,u,c,ms}]}), writes a static site:
  manifest.json
  catalog/channel/<catalogId>.json            (skip=0 page)
  catalog/channel/<catalogId>/skip=<N>.json   (pages 2+)
  meta/channel/<id>.json
  stream/channel/<id>.json

Channel ids are slugified names; collisions get a -2, -3 suffix.
Categories come from the semicolon-separated 'c' field (first token = primary).
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

FEED_URL = "https://new.ajo.co.in/channels/channels.json"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("addon")
PAGE = 100
BASE = "https://raw.githubusercontent.com/imakshayjoshi/ajo-live/main/addon"

def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "channel"

def main() -> int:
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if src and src.exists():
        data = json.loads(src.read_text())
    else:
        import urllib.request
        with urllib.request.urlopen(FEED_URL, timeout=60) as r:
            data = json.loads(r.read())
    channels = [c for c in data.get("channels", []) if c.get("u")]
    print(f"channels: {len(channels)}")

    # unique ids
    seen = {}
    metas = []
    for ch in channels:
        s = slug(ch["n"])
        if s in seen:
            seen[s] += 1
            sid = f"{s}-{seen[s]}"
        else:
            seen[s] = 1
            sid = s
        cats = [t.strip() for t in (ch.get("c") or "").split(";") if t.strip() and t.strip().lower() != "undefined"]
        primary = cats[0] if cats else "General"
        metas.append({
            "_id": sid,
            "name": ch["n"],
            "logo": ch.get("l") or "",
            "url": ch["u"],
            "cats": cats,
            "primary": primary,
            "ms": ch.get("ms"),
        })

    # catalogs
    catalogs = []
    counts = {}
    for m in metas:
        counts[m["primary"]] = counts.get(m["primary"], 0) + 1
    for cat, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        catalogs.append({"id": "cat-" + slug(cat), "name": cat, "count": n})
    catalogs.insert(0, {"id": "live", "name": "All Channels", "count": len(metas)})
    cats_list = catalogs[1:]

    OUT.mkdir(parents=True, exist_ok=True)

    manifest = {
        "id": "com.ajo.live",
        "version": "1.0.0",
        "name": "AJO Live",
        "description": "AJO live TV: Indian, sports, news, movies, kids - {} channels".format(len(metas)),
        "logo": f"{BASE}/logo.png",
        "background": f"{BASE}/logo.png",
        "types": ["channel"],
        "resources": ["catalog", "meta", "stream"],
        "idPrefixes": [],
        "catalogs": [
            {"type": "channel", "id": c["id"], "name": c["name"]}
            for c in catalogs
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))

    def write_catalog(cid: str, items):
        d = OUT / "catalog" / "channel"
        (d / cid).mkdir(parents=True, exist_ok=True)
        # skip=0 page
        arr = [{"id": m["_id"], "name": m["name"], "type": "channel",
                "logo": m["logo"], "poster": m["logo"]} for m in items[:PAGE]]
        (d / f"{cid}.json").write_text(json.dumps({"metas": arr}, ensure_ascii=False))
        # subsequent pages
        for i in range(PAGE, len(items), PAGE):
            chunk = [{"id": m["_id"], "name": m["name"], "type": "channel",
                      "logo": m["logo"], "poster": m["logo"]} for m in items[i:i+PAGE]]
            (d / cid / f"skip={i}.json").write_text(json.dumps({"metas": chunk}, ensure_ascii=False))

    write_catalog("live", metas)
    for c in cats_list:
        write_catalog(c["id"], [m for m in metas if m["primary"] == c["name"]])

    # meta + stream per channel
    md = OUT / "meta" / "channel"
    sd = OUT / "stream" / "channel"
    md.mkdir(parents=True, exist_ok=True)
    sd.mkdir(parents=True, exist_ok=True)
    for m in metas:
        meta = {
            "id": m["_id"],
            "name": m["name"],
            "type": "channel",
            "logo": m["logo"],
            "background": m["logo"],
            "poster": m["logo"],
            "description": " / ".join(m["cats"]) or "Live channel",
            "genres": m["cats"] or ["General"],
            "releaseInfo": "",
        }
        (md / f"{m['_id']}.json").write_text(json.dumps({"meta": meta}, ensure_ascii=False))
        stream = {
            "streams": [{
                "url": m["url"],
                "name": "AJO Live",
                "description": " / ".join(m["cats"] or ["General"]),
                "behaviorHints": {"isLive": True, "notWebReady": False},
            }]
        }
        (sd / f"{m['_id']}.json").write_text(json.dumps(stream, ensure_ascii=False))

    print(f"catalogs: {len(catalogs)} ({[c['id'] + ':' + str(c['count']) for c in catalogs[:8]]}...)")
    print(f"meta+stream files: {len(metas) * 2}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
