#!/usr/bin/env python3
"""Local preview only: python3 serve.py  ->  http://localhost:4321"""
import functools, http.server, os, socketserver

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 4321), Handler) as httpd:
    print(f"serving {ROOT} on http://localhost:4321")
    httpd.serve_forever()
