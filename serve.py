#!/usr/bin/env python3
"""Local preview.

    python3 serve.py          ->  http://localhost:4321
    python3 serve.py 4322     ->  a second server on another port

Threaded on purpose: the single-threaded TCPServer in the stdlib blocks on one
keep-alive connection, which makes the whole server appear dead while a browser
holds a socket open. Also sends no-store, so an edit to the CSS always shows up
on an ordinary reload — no need for a hard refresh.
"""
import functools, http.server, os, socketserver, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4321


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):          # quieter: errors only
        if not args or not str(args[0]).startswith(("GET", "HEAD")):
            super().log_message(fmt, *args)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


os.chdir(ROOT)
with Server(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)) as httpd:
    print(f"serving {ROOT} on http://localhost:{PORT}  (Ctrl+C to stop)")
    httpd.serve_forever()
