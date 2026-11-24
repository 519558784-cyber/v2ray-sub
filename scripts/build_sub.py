#!/usr/bin/env python3
"""Build links.txt (base64 v2rayN subscription) from public free node sources.

Runs on GitHub Actions daily. Uses only the Python standard library.
Sources were hand-picked from ~2 weeks of daily test data (highest yield first).
Verified seed nodes in core_nodes.txt (if present) are always placed first.
"""
import base64
import re
import urllib.request

SOURCES = [
    "https://raw.githubusercontent.com/free18/v2ray/main/v.txt",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/v2ray-2.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/base64.txt",
    "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/sub",
]

PROTO = re.compile(r"^\s*(vmess|vless|trojan|ss|hy2|hysteria2|tuic)://", re.I)
URI_RE = re.compile(r"(?:vmess|vless|trojan|ss|hy2|hysteria2|tuic)://\S+", re.I)
HOSTPORT_RE = re.compile(r"@([^/@\s:]+):(\d+)")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sub-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def extract_uris(data: bytes):
    """Extract share-link URIs; fall back to whole-body base64 decode."""
    text = data.decode("utf-8", "ignore")
    uris = [u.strip() for u in URI_RE.findall(text)]
    if not uris:
        try:
            pad = "=" * (-len(text.strip()) % 4)
            dec = base64.b64decode(text.strip().replace("\n", "") + pad)
            uris = [u.strip() for u in URI_RE.findall(dec.decode("utf-8", "ignore"))]
        except Exception:
            pass
    return [u for u in uris if PROTO.match(u)]

def load_seeds():
    try:
        with open("core_nodes.txt", "r", encoding="utf-8") as f:
            return [l.strip() for l in f if PROTO.match(l.strip())]
    except FileNotFoundError:
        return []

def main():
    seen_uri, seen_hp = set(), set()
    links = []

    def add(u):
        if u in seen_uri:
            return
        m = HOSTPORT_RE.search(u)
        if m and not u.lower().startswith("vmess://"):
            key = (m.group(1).lower(), m.group(2))
            if key in seen_hp:
                return
            seen_hp.add(key)
        seen_uri.add(u)
        links.append(u)

    for u in load_seeds():
        add(u)
    seed_count = len(links)

    per_source = {}
    for url in SOURCES:
        try:
            uris = extract_uris(fetch(url))
        except Exception as e:
            uris = []
            per_source[url] = f"error: {e}"
            continue
        for u in uris:
            add(u)
        per_source[url] = len(uris)

    body = "\n".join(links) + "\n"
    b64 = base64.b64encode(body.encode("utf-8")).decode("ascii")
    with open("links.txt", "w", encoding="ascii") as f:
        f.write(b64)

    print(f"seeds (verified): {seed_count}")
    for url, n in per_source.items():
        print(f"  {url} -> {n}")
    print(f"total links: {len(links)}")
    print(f"base64 length: {len(b64)}")

if __name__ == "__main__":
    main()
