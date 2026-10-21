"""检查 research-map.yaml 的外链与素材是否还活着。失败时退出码 1。"""

import concurrent.futures as cf
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
UA = "awesome-world-model-memory/1.0 (+https://github.com/ghf2458526136-sys/awesome-world-model-memory)"


def head(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://ghf2458526136-sys.github.io/"})
    req.get_method = lambda: "HEAD"
    try:
        with OPENER.open(req, timeout=25) as r:
            return r.status, r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        if e.code in (403, 405):
            return e.code, "head-blocked"
        return e.code, str(e.reason)[:60]
    except Exception as e:
        return 0, type(e).__name__


def main():
    doc = yaml.safe_load((ROOT / "research-map.yaml").read_text(encoding="utf-8"))
    targets = []
    for n in doc["nodes"]:
        for u in (n.get("media") or []) + (n.get("links") or []):
            if isinstance(u, str) and u.startswith("http"):
                targets.append((n["id"], u))
    uniq = sorted(set(targets))
    print(f"检查 {len(uniq)} 个链接…")
    bad = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for (nid, url), (code, info) in zip(uniq, ex.map(lambda t: head(t[1]), uniq)):
            if code == 0 or code >= 400:
                bad.append({"id": nid, "url": url, "status": code, "info": info})
    print(f"失效 {len(bad)} / {len(uniq)}")
    for b in bad[:25]:
        print(f"  - {b['id']}: {b['status']} {b['url'][:90]}")
    if "--json" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--json") + 1])
        out.write_text(json.dumps(bad, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
