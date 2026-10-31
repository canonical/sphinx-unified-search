"""Optional local proxy for search-result previews (development only).

Result previews are fetched by the visitor's browser straight from the remote
documentation site. When you preview your docs locally (http://127.0.0.1:8000),
that is a cross-origin request, so it fails unless the remote site sends CORS
headers, and private sites answer with a login page because the browser has no
credentials for them.

This proxy runs on your machine, fetches the remote page for the browser, adds
the CORS header, and (for projects that need it) attaches a cookie read from an
environment variable. It is NOT used unless you both:

1. set ``unified_search_preview_proxy`` in ``conf.py``, and
2. start this proxy yourself (``sphinx-unified-search-proxy``).

Remove the setting, or don't start the proxy, to turn it off.

The proxy only fetches pages under the ``base_url`` of the projects in
``unified_search_projects`` (plus any ``--allow`` URLs), only listens on
loopback, and only answers requests that come from a loopback web page.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_LISTEN = "http://127.0.0.1:8010/"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_BYTES = 10 * 1024 * 1024
TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
)
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


_COOKIE_NAME = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_`|~-]+$")


def _cookie_sources(spec) -> list[tuple[str | None, str]]:
    """Normalise ``preview_cookie_env`` into ``[(cookie_name | None, env_var)]``.

    * ``"ENV"``                   one variable holding a whole ``Cookie`` header
    * ``["ENV1", "ENV2"]``       several such variables, joined with ``; ``
    * ``{"sessionid": "ENV"}``    ``ENV`` holds just the value of that cookie
    """
    if not spec:
        return []
    if isinstance(spec, str):
        pairs = [(None, spec)]
    elif isinstance(spec, (list, tuple)):
        pairs = [(None, e) for e in spec]
    elif isinstance(spec, dict):
        pairs = list(spec.items())
    else:
        raise ValueError(f"preview_cookie_env must be a string, list or dict: {spec!r}")
    for name, env in pairs:
        if not isinstance(env, str) or not _ENV_NAME.match(env):
            raise ValueError(f"not an environment variable name: {env!r}")
        if name is not None and not _COOKIE_NAME.match(str(name)):
            raise ValueError(f"not a valid cookie name: {name!r}")
    return pairs


class Target:
    """A remote docs site the proxy is allowed to fetch from."""

    def __init__(self, base_url: str, cookie_env=None, name: str = ""):
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"not a valid http(s) URL: {base_url!r}")
        self.name = name or parsed.netloc
        self.scheme = parsed.scheme
        self.netloc = parsed.netloc
        self.path = parsed.path if parsed.path.endswith("/") else parsed.path + "/"
        self.cookie_sources = _cookie_sources(cookie_env)

    def matches(self, url: str) -> bool:
        u = urlparse(url)
        path = u.path if u.path.endswith("/") else u.path + "/"
        return (u.scheme, u.netloc) == (self.scheme, self.netloc) and path.startswith(
            self.path
        )

    def missing_env(self) -> list[str]:
        """Names of configured cookie variables that are unset or empty."""
        return [e for _, e in self.cookie_sources if not os.environ.get(e, "").strip()]

    def cookie(self) -> str:
        """Build the ``Cookie`` header value from the environment."""
        parts = []
        for cookie_name, env in self.cookie_sources:
            value = os.environ.get(env, "").strip()
            if not value:
                continue
            if cookie_name is None:
                # Tolerate a value pasted straight from the browser dev tools.
                value = re.sub(r"^cookie:\s*", "", value, flags=re.I).strip().rstrip(";")
            else:
                value = f"{cookie_name}={value}"
            if any(ord(c) < 32 or ord(c) == 127 for c in value):
                continue  # never let a bad value inject extra headers
            parts.append(value)
        return "; ".join(parts)


def find_target(url: str, targets: list[Target]) -> Target | None:
    return next((t for t in targets if t.matches(url)), None)


def origin_allowed(origin: str | None, extra: list[str]) -> bool:
    """Accept requests from loopback web pages (any port), or listed origins."""
    if not origin:
        return True  # not a browser cross-origin request (e.g. curl)
    if origin in extra:
        return True
    return urlparse(origin).hostname in LOOPBACK_HOSTS


def host_allowed(host_header: str | None, listen_host: str) -> bool:
    """Reject DNS-rebinding attempts: the Host must be a loopback name."""
    hostname = urlparse("//" + (host_header or "")).hostname
    return hostname in LOOPBACK_HOSTS or hostname == listen_host


class _NoCookieLeakRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects, but never send the cookie to a different site."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            old, dest = urlparse(req.full_url), urlparse(newurl)
            if (old.scheme, old.netloc) != (dest.scheme, dest.netloc):
                new.headers.pop("Cookie", None)
        return new


def fetch(url: str, cookie: str = "") -> tuple[int, str, bytes]:
    headers = {"User-Agent": USER_AGENT}
    if cookie:
        headers["Cookie"] = cookie
    opener = urllib.request.build_opener(_NoCookieLeakRedirect)
    try:
        with opener.open(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as r:
            body = r.read(MAX_BYTES + 1)
            return r.status, r.headers.get("Content-Type", "text/html"), body[:MAX_BYTES]
    except urllib.error.HTTPError as e:
        return e.code, "text/plain", e.read(MAX_BYTES)
    except Exception as e:  # network error, timeout, bad redirect...
        return 502, "text/plain", str(e).encode()


def make_handler(targets: list[Target], extra_origins: list[str], listen_host: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "unified-search-proxy"

        def log_message(self, *args):  # we print our own, cookie-free log line
            pass

        def _reply(self, status, body=b"", ctype="text/plain", origin=None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            origin = self.headers.get("Origin")
            if not origin_allowed(origin, extra_origins):
                return self._reply(403, b"origin not allowed")
            self._reply(204, origin=origin)

        def do_GET(self):
            origin = self.headers.get("Origin")
            if not host_allowed(self.headers.get("Host"), listen_host):
                return self._reply(403, b"host not allowed")
            if not origin_allowed(origin, extra_origins):
                return self._reply(403, b"origin not allowed")

            url = parse_qs(urlparse(self.path).query).get("url", [""])[0]
            target = find_target(url, targets)
            if target is None:
                print(f"[blocked] {url or '(no url)'}", flush=True)
                return self._reply(
                    403,
                    b"URL is not under a configured project base_url",
                    origin=origin,
                )

            status, ctype, body = fetch(url, target.cookie())
            print(f"[{status}] {url}", flush=True)
            self._reply(status, body, ctype, origin)

    return Handler


class _Tags:
    """Stand-in for Sphinx's ``tags`` object, in case conf.py uses it."""

    def has(self, tag: str) -> bool:
        return False

    __contains__ = has


def load_conf(conf_dir: str) -> dict:
    """Run conf.py and return its namespace.

    This deliberately doesn't call Sphinx's own ``eval_config_file``: its
    signature differs between Sphinx versions (``str`` vs ``Path``), and the
    proxy only needs a few plain values from conf.py.
    """
    path = Path(conf_dir).resolve() / "conf.py"
    if not path.is_file():
        raise SystemExit(f"error: no conf.py in {path.parent} (use --conf-dir)")

    namespace = {"__file__": str(path), "tags": _Tags()}
    old_cwd = os.getcwd()
    os.chdir(path.parent)  # like Sphinx, run conf.py from its own directory
    try:
        exec(compile(path.read_bytes(), str(path), "exec"), namespace)  # noqa: S102
    except (Exception, SystemExit) as e:
        raise SystemExit(
            f"error: could not run {path}: {type(e).__name__}: {e}\n"
            "Use --no-conf with --allow to skip reading conf.py."
        )
    finally:
        os.chdir(old_cwd)
    return namespace


def targets_from_conf(conf: dict) -> list[Target]:
    targets = []
    for project in conf.get("unified_search_projects", []) or []:
        base = project.get("base_url")
        if not base:
            continue
        targets.append(
            Target(
                base,
                cookie_env=project.get("preview_cookie_env"),
                name=project.get("name", ""),
            )
        )
    return targets


def parse_allow(spec: str) -> Target:
    """``URL`` or ``URL/=ENV[,ENV...]`` (the URL part must end with ``/``)."""
    m = re.match(r"^(.*/)=([A-Za-z_]\w*(?:,[A-Za-z_]\w*)*)$", spec)
    if m:
        return Target(m.group(1), cookie_env=m.group(2).split(","))
    return Target(spec)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sphinx-unified-search-proxy",
        description="Local CORS/cookie proxy for sphinx-unified-search result "
        "previews. Development only.",
    )
    p.add_argument(
        "--conf-dir",
        default=".",
        help="directory containing conf.py (default: current directory)",
    )
    p.add_argument(
        "--no-conf",
        action="store_true",
        help="do not read conf.py; use only --allow",
    )
    p.add_argument(
        "--listen",
        help="URL to listen on, e.g. http://127.0.0.1:8010/ (default: the "
        "unified_search_preview_proxy value in conf.py, else " + DEFAULT_LISTEN + ")",
    )
    p.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="URL[=ENV_VAR[,ENV_VAR...]]",
        help="also proxy pages under this base URL; to send a cookie, append "
        "=ENV_VAR after the trailing slash, e.g. "
        "https://example.com/docs/=DOCS_COOKIE, or several variables "
        "separated by commas (repeatable)",
    )
    p.add_argument(
        "--allow-origin",
        action="append",
        default=[],
        metavar="ORIGIN",
        help="also accept requests from this non-loopback web origin (repeatable)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    conf = {} if args.no_conf else load_conf(args.conf_dir)
    targets = targets_from_conf(conf)
    try:
        targets += [parse_allow(spec) for spec in args.allow]
    except ValueError as e:
        raise SystemExit(f"error: {e}")
    if not targets:
        raise SystemExit(
            "error: nothing to proxy. Configure unified_search_projects in "
            "conf.py or pass --allow URL."
        )

    listen = urlparse(
        args.listen or conf.get("unified_search_preview_proxy") or DEFAULT_LISTEN
    )
    host, port = listen.hostname or "127.0.0.1", listen.port or 8010
    if host not in LOOPBACK_HOSTS:
        raise SystemExit(
            f"error: refusing to listen on {host!r}; this proxy may carry "
            "credentials and only runs on loopback (127.0.0.1 / localhost)."
        )

    print(f"unified-search preview proxy on http://{host}:{port}/")
    for t in targets:
        if not t.cookie_sources:
            cookie = "no cookie"
        else:
            missing = t.missing_env()
            names = ", ".join("$" + e for _, e in t.cookie_sources)
            cookie = f"cookie from {names}"
            if missing:
                cookie += "; WARNING not set: " + ", ".join("$" + m for m in missing)
        print(f"  {t.scheme}://{t.netloc}{t.path}  ({t.name}; {cookie})")

    handler = make_handler(targets, args.allow_origin, host)
    try:
        ThreadingHTTPServer((host, port), handler).serve_forever()
    except KeyboardInterrupt:
        print()
    except OSError as e:
        raise SystemExit(f"error: cannot listen on {host}:{port}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
