import json
import pytest
import requests
from threading import Thread

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class MockConsulServer(BaseHTTPRequestHandler):
    """
    Mock Consul server to response to test queries.
    """
    def do_GET(self):

        # Datacenter catalog
        if self.path == '/v1/catalog/datacenters':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(['dc1', 'dc2']).encode('utf-8'))
            return

def serve_consul():
    server = HTTPServer(('localhost', 8500), MockConsulServer)
    server_thread = Thread(target=server.serve_forever)
    server_thread.setDaemon(True)
    server_thread.start()
