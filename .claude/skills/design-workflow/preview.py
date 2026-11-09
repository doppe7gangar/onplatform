#!/usr/bin/env python3
"""Serve a design folder with live reload, to watch it come together.

    python3 preview.py ./design                 # http://127.0.0.1:8765
    python3 preview.py ./design --phone         # also on this Wi-Fi, to open on a phone
    python3 preview.py ./design --port 9000

Every page reloads itself a moment after any file in the folder changes, so
the person can keep the browser open while the design is built and edited.
?state=empty and the other prototype.js parameters work as in a file.

--phone listens on every network interface and prints the address to open
on an iPhone or Android phone on the same network: a design reads very
differently in the hand than in a desktop browser. Only do that on a network
you trust; the folder is readable by anyone on it while the server runs.

Nothing is installed and nothing is written; Ctrl-C stops it.
"""

import argparse
import functools
import http.server
import os
import socket
import socketserver
import sys
import time

RELOAD = b"""<script>/* preview.py: reload when the design changes */
(function () {
  var seen = null;
  setInterval(function () {
    fetch('/__preview/version', {cache: 'no-store'}).then(function (r) { return r.text(); })
      .then(function (v) { if (seen === null) seen = v; else if (v !== seen) location.reload(); })
      .catch(function () {});
  }, 700);
})();
</script>
"""
SKIP = {".git", "node_modules", "__pycache__", ".visual-review"}


def version(root):
    """Changes whenever a file in the folder is added, removed or edited."""
    newest, count = 0.0, 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            try:
                newest = max(newest, os.stat(os.path.join(dirpath, f)).st_mtime)
                count += 1
            except OSError:
                pass
    return f"{newest:.3f}-{count}"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, root, **kwargs):
        self.root = root
        super().__init__(*args, directory=root, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path == "/__preview/version":
            body = version(self.root).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        local = self.translate_path(path)
        if os.path.isdir(local):
            local = os.path.join(local, "index.html")
        if local.endswith((".html", ".htm")) and os.path.isfile(local):
            html = open(local, "rb").read()
            i = html.lower().rfind(b"</body>")
            html = html[:i] + RELOAD + html[i:] if i >= 0 else html + RELOAD
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        pass  # quiet: the person is looking at the page, not the log


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def lan_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 80))  # no packet is sent; it picks the outgoing interface
            return s.getsockname()[0]
    except OSError:
        return None


def serve(root, port, host):
    """Bind the first free port from `port` on; return the server."""
    handler = functools.partial(Handler, root=root)
    for p in range(port, port + 50):
        try:
            return Server((host, p), handler)
        except OSError:
            continue
    sys.exit(f"no free port between {port} and {port + 49}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("design", nargs="?", default="design", help="the design folder (default ./design)")
    ap.add_argument("--port", type=int, default=8765, help="first port to try (default 8765)")
    ap.add_argument("--phone", action="store_true",
                    help="also serve on this network, to open the design on a phone")
    a = ap.parse_args()
    root = os.path.abspath(a.design)
    if not os.path.isfile(os.path.join(root, "index.html")):
        sys.exit(f"no index.html in {a.design}: scaffold the design first (new_project.py)")
    server = serve(root, a.port, "0.0.0.0" if a.phone else "127.0.0.1")
    port = server.server_address[1]
    print(f"preview: http://127.0.0.1:{port}/  (live reload on; Ctrl-C to stop)", flush=True)
    if a.phone:
        ip = lan_address()
        print(f"on a phone on this network: http://{ip}:{port}/" if ip else
              "couldn't find this machine's network address; use its IP with port "
              f"{port}", flush=True)
    print(f"  states: http://127.0.0.1:{port}/?state=empty   ?state=loading   ?state=error", flush=True)
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
