"""Tests for serve.py: the small web server that shows the dashboard."""
import http.client
import threading
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

import serve


@pytest.fixture(scope="module")
def port():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(serve.DashboardHandler, directory=serve.HERE))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def get(port, path, host=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path, headers={"Host": host or f"localhost:{port}"})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, resp, body


def test_home_page_is_served(port):
    status, resp, body = get(port, "/")
    assert status == 200 and b"<html" in body.lower()
    assert "default-src 'self'" in resp.getheader("Content-Security-Policy")


def test_demo_data_is_served(port):
    status, _, body = get(port, "/demo_data.json")
    assert status == 200 and b'"demo"' in body


@pytest.mark.parametrize("path", ["/google_tokens.json", "/profile.json", "/serve.py", "/../serve.py"])
def test_private_and_unlisted_files_are_not_served(port, path):
    assert get(port, path)[0] == 404


def test_wrong_host_header_is_refused(port):
    assert get(port, "/", host="evil.example.com")[0] == 403  # DNS-rebinding protection
