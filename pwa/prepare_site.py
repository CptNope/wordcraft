#!/usr/bin/env python3
"""Wrap the WordCraft Rust/WASM build as an installable GitHub Pages PWA."""
from pathlib import Path
import json
import os
import shutil
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]

def icon(path, size):
    """Generate an original geometric document icon, without external fonts."""
    pixels = bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            u = (x + 0.5) / size
            v = (y + 0.5) / size
            color = (35, 60, 116, 255)
            if .17 < u < .83 and .10 < v < .90:
                color = (241, 245, 255, 255)
            if .67 < u < .83 and .10 < v < .26:
                color = (150, 183, 231, 255)
            if (.30 < u < .69 and .37 < v < .41) or (.30 < u < .69 and .49 < v < .53) or (.30 < u < .58 and .61 < v < .65):
                color = (58, 99, 171, 255)
            pixels.extend(color)
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" +
        chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress(bytes(pixels), 9)) +
        chunk(b"IEND", b"")
    )

def main(site):
    index = site / "index.html"
    if not index.is_file():
        raise SystemExit("WordCraft Trunk build missing index.html")
    icons = site / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    for filename, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
        icon(icons / filename, size)
    for filename in ("LICENSE-MIT", "LICENSE-APACHE", "NOTICE", "ATTRIBUTION.md"):
        source = ROOT / filename
        if source.is_file():
            shutil.copy2(source, site / filename)
    shutil.copy2(ROOT / "pwa" / "manifest.webmanifest", site / "manifest.webmanifest")
    shutil.copy2(ROOT / "pwa" / "install-ui.js", site / "install-ui.js")
    (site / ".nojekyll").touch()
    html = index.read_text(encoding="utf-8")
    if "</head>" not in html or "</body>" not in html:
        raise SystemExit("WordCraft index.html missing head/body tags")
    html = html.replace("</head>", """<link rel="manifest" href="./manifest.webmanifest">
<meta name="theme-color" content="#233c74">
<link rel="apple-touch-icon" href="./icons/apple-touch-icon.png">
</head>""", 1)
    html = html.replace("</body>", """<script defer src="./install-ui.js"></script>
<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js")
    .catch(error => console.warn("WordCraft PWA service worker:", error)));
}
</script>
</body>""", 1)
    index.write_text(html, encoding="utf-8")
    built = ["./" + p.relative_to(site).as_posix() for p in site.rglob("*")
             if p.is_file() and p.suffix.lower() in (".wasm", ".js", ".css")]
    if not any(p.endswith(".wasm") for p in built):
        raise SystemExit("WordCraft PWA has no compiled .wasm file")
    precache = ["./", "./index.html", "./manifest.webmanifest", "./install-ui.js",
                "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png"]
    version = (os.environ.get("GITHUB_SHA") or "local")[:12]
    sw = (ROOT / "pwa" / "sw.js").read_text(encoding="utf-8")
    sw = sw.replace("__BUILD_VERSION__", version)
    sw = sw.replace("__PRECACHE_ASSETS__", json.dumps(sorted(set(precache + built))))
    (site / "sw.js").write_text(sw, encoding="utf-8")
    print(f"Prepared WordCraft PWA with {len(built)} compiled assets, cache {version}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 pwa/prepare_site.py dist/web")
    main(Path(sys.argv[1]).resolve())
