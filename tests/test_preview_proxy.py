import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

import pytest

from sphinx_unified_search import preview_proxy as pp


# ---------------------------------------------------------------- unit tests


def test_target_matches_only_under_base_path():
    t = pp.Target("https://ubuntu.com/kernel/docs/")
    assert t.matches("https://ubuntu.com/kernel/docs/")
    assert t.matches("https://ubuntu.com/kernel/docs/how-to/x/")
    assert t.matches("https://ubuntu.com/kernel/docs")
    assert not t.matches("https://ubuntu.com/kernel/docs-evil/")
    assert not t.matches("https://ubuntu.com/other/")
    assert not t.matches("http://ubuntu.com/kernel/docs/")  # scheme differs
    assert not t.matches("https://ubuntu.com.evil.test/kernel/docs/")


def test_origin_allowed():
    assert pp.origin_allowed(None, [])
    assert pp.origin_allowed("http://127.0.0.1:8000", [])
    assert pp.origin_allowed("http://localhost:9999", [])
    assert pp.origin_allowed("http://[::1]:8000", [])
    assert not pp.origin_allowed("https://evil.example", [])
    assert pp.origin_allowed("https://dev.example", ["https://dev.example"])


def test_host_allowed():
    assert pp.host_allowed("127.0.0.1:8010", "127.0.0.1")
    assert pp.host_allowed("localhost:8010", "127.0.0.1")
    assert not pp.host_allowed("rebind.evil.example:8010", "127.0.0.1")
    assert not pp.host_allowed(None, "127.0.0.1")


def test_parse_allow():
    t = pp.parse_allow("https://x.test/docs/=MY_COOKIE")
    assert (t.netloc, t.path) == ("x.test", "/docs/")
    assert t.cookie_sources == [(None, "MY_COOKIE")]
    t = pp.parse_allow("https://x.test/docs/=A_ONE,B_TWO")
    assert t.cookie_sources == [(None, "A_ONE"), (None, "B_TWO")]
    t = pp.parse_allow("https://x.test/docs/?a=b")  # '=' inside the URL
    assert t.cookie_sources == [] and t.netloc == "x.test"
    assert pp.parse_allow("https://x.test/docs/").cookie_sources == []


def test_targets_from_conf_reads_projects_and_cookie_env():
    conf = {
        "unified_search_projects": [
            {"name": "A", "base_url": "https://a.test/docs/"},
            {
                "name": "B",
                "base_url": "https://b.test/x/",
                "preview_cookie_env": "B_COOKIE",
            },
            {"name": "no-base"},
        ]
    }
    a, b = pp.targets_from_conf(conf)
    assert a.cookie_sources == [] and b.cookie_sources == [(None, "B_COOKIE")]


def test_cookie_single_variable_header_value(monkeypatch):
    monkeypatch.setenv("C1", "sessionid=abc; csrftoken=def")
    assert pp.Target("https://a.test/", cookie_env="C1").cookie() == (
        "sessionid=abc; csrftoken=def"
    )


def test_cookie_header_pasted_with_prefix_is_cleaned(monkeypatch):
    monkeypatch.setenv("C1", "Cookie: sessionid=abc;")
    assert pp.Target("https://a.test/", cookie_env="C1").cookie() == "sessionid=abc"


def test_cookie_multiple_variables_are_joined(monkeypatch):
    monkeypatch.setenv("C1", "sessionid=abc")
    monkeypatch.setenv("C2", "csrftoken=def")
    t = pp.Target("https://a.test/", cookie_env=["C1", "C2", "C_UNSET"])
    assert t.cookie() == "sessionid=abc; csrftoken=def"
    assert t.missing_env() == ["C_UNSET"]


def test_cookie_dict_maps_names_to_variables(monkeypatch):
    monkeypatch.setenv("SESS", "abc")
    monkeypatch.setenv("CSRF", "def")
    t = pp.Target("https://a.test/", cookie_env={"sessionid": "SESS", "csrftoken": "CSRF"})
    assert t.cookie() == "sessionid=abc; csrftoken=def"


def test_cookie_with_control_characters_is_dropped(monkeypatch):
    monkeypatch.setenv("C1", "a=b\r\nX-Evil: 1")
    monkeypatch.setenv("C2", "ok=1")
    assert pp.Target("https://a.test/", cookie_env=["C1", "C2"]).cookie() == "ok=1"


@pytest.mark.parametrize(
    "bad", [{"bad name": "ENV"}, {"ok": "not-an-env"}, ["has space"], 42]
)
def test_invalid_cookie_config_is_rejected(bad):
    with pytest.raises(ValueError):
        pp.Target("https://a.test/", cookie_env=bad)


def test_two_cookie_sets_for_two_projects_stay_separate(monkeypatch):
    monkeypatch.setenv("ONE", "s=1")
    monkeypatch.setenv("TWO", "s=2")
    targets = [
        pp.Target("https://a.test/docs/", cookie_env="ONE"),
        pp.Target("https://b.test/docs/", cookie_env="TWO"),
    ]
    assert pp.find_target("https://a.test/docs/x/", targets).cookie() == "s=1"
    assert pp.find_target("https://b.test/docs/x/", targets).cookie() == "s=2"


def test_load_conf(tmp_path):
    (tmp_path / "conf.py").write_text(
        'unified_search_preview_proxy = "http://127.0.0.1:9123/"\n'
        'unified_search_projects = [{"name": "A", "base_url": "https://a.test/"}]\n'
    )
    conf = pp.load_conf(str(tmp_path))
    assert conf["unified_search_preview_proxy"] == "http://127.0.0.1:9123/"
    assert len(pp.targets_from_conf(conf)) == 1


def test_main_refuses_non_loopback_listen():
    with pytest.raises(SystemExit) as e:
        pp.main(["--no-conf", "--allow", "https://a.test/", "--listen", "http://0.0.0.0:1/"])
    assert "loopback" in str(e.value)


def test_main_requires_something_to_proxy():
    with pytest.raises(SystemExit):
        pp.main(["--no-conf"])


# ------------------------------------------------------------- end-to-end


class _Remote(BaseHTTPRequestHandler):
    seen_cookies: list = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        _Remote.seen_cookies.append((self.path, self.headers.get("Cookie")))
        if self.path.startswith("/private/"):
            if self.headers.get("Cookie") != "session=secret":
                body = b"<main>Log in to view this documentation</main>"
            else:
                body = b"<main>private content</main>"
        elif self.path == "/public/redirect":
            self.send_response(302)
            # redirect to a *different origin* (different port)
            self.send_header("Location", f"http://localhost:{self.server.server_port}/public/x")
            self.end_headers()
            return
        elif self.path == "/public/missing":
            self.send_response(404)
            self.end_headers()
            return
        else:
            body = b"<main>public content</main>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def stack(monkeypatch):
    """A fake remote site plus a running proxy in front of it."""
    monkeypatch.setenv("PRIV_COOKIE", "session=secret")
    _Remote.seen_cookies = []
    remote = ThreadingHTTPServer(("127.0.0.1", 0), _Remote)
    rport = remote.server_port
    threading.Thread(target=remote.serve_forever, daemon=True).start()

    targets = [
        pp.Target(f"http://127.0.0.1:{rport}/public/"),
        pp.Target(f"http://127.0.0.1:{rport}/private/", cookie_env="PRIV_COOKIE"),
    ]
    proxy = ThreadingHTTPServer(("127.0.0.1", 0), pp.make_handler(targets, [], "127.0.0.1"))
    pport = proxy.server_port
    threading.Thread(target=proxy.serve_forever, daemon=True).start()

    def get(remote_path, origin="http://127.0.0.1:8000", host=None):
        conn = http.client.HTTPConnection("127.0.0.1", pport, timeout=5)
        headers = {"Origin": origin} if origin else {}
        if host:
            headers["Host"] = host
        url = quote(f"http://127.0.0.1:{rport}{remote_path}", safe="")
        conn.request("GET", f"/?url={url}", headers=headers)
        r = conn.getresponse()
        return r.status, dict(r.getheaders()), r.read()

    yield get
    remote.shutdown()
    proxy.shutdown()


def test_public_page_gets_cors_header(stack):
    status, headers, body = stack("/public/page/")
    assert status == 200 and b"public content" in body
    assert headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:8000"
    assert headers["Vary"] == "Origin"


def test_cookie_sent_only_to_its_project(stack):
    _, _, body = stack("/private/page/")
    assert b"private content" in body
    stack("/public/page/")
    cookies = dict(_Remote.seen_cookies)
    assert cookies["/private/page/"] == "session=secret"
    assert cookies["/public/page/"] is None


def test_redirects_are_followed(stack):
    status, _, body = stack("/public/redirect")
    assert status == 200 and b"public content" in body


def test_redirect_handler_strips_cookie_cross_origin():
    import urllib.request

    h = pp._NoCookieLeakRedirect()
    req = urllib.request.Request("https://a.test/x", headers={"Cookie": "s=1"})
    same = h.redirect_request(req, None, 302, "Found", {}, "https://a.test/y")
    other = h.redirect_request(req, None, 302, "Found", {}, "https://b.test/y")
    downgrade = h.redirect_request(req, None, 302, "Found", {}, "http://a.test/y")
    assert same.headers.get("Cookie") == "s=1"
    assert "Cookie" not in other.headers
    assert "Cookie" not in downgrade.headers


def test_upstream_status_is_passed_through(stack):
    status, _, _ = stack("/public/missing")
    assert status == 404


def test_url_outside_allow_list_is_blocked(stack):
    status, _, _ = stack("/elsewhere/")
    assert status == 403


def test_foreign_web_origin_is_rejected(stack):
    status, headers, body = stack("/public/page/", origin="https://evil.example")
    assert status == 403 and "Access-Control-Allow-Origin" not in headers


def test_dns_rebinding_host_is_rejected(stack):
    status, _, _ = stack("/public/page/", host="rebind.evil.example")
    assert status == 403
