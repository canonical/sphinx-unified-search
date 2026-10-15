import json
import os
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from sphinx_unified_search.parser import parse_searchindex
from test_merger import REMOTE, _js


def wait_for(check, process, log):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        assert process.poll() is None, log.read_text()
        if check():
            return
        time.sleep(0.1)
    pytest.fail(f"Timed out waiting for autobuild:\n{log.read_text()}")


@contextmanager
def autobuild(source, output, log):
    with log.open("w") as stream:
        process = subprocess.Popen(
            [
                sys.executable, "-m", "sphinx_autobuild",
                "--host", "127.0.0.1", "--port", "0",
                str(source), str(output),
            ],
            stdout=stream,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        try:
            wait_for(
                lambda: "Waiting to detect changes" in log.read_text(),
                process, log,
            )
            # Confirm the server is responsive and its watcher has started.
            def responsive():
                text = log.read_text()
                match = re.search(r"Serving on http://127\.0\.0\.1:(\d+)", text)
                if match is None:
                    return False
                port = match.group(1)
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                        return response.status == 200
                except URLError:
                    return False

            wait_for(responsive, process, log)
            yield process
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


@pytest.mark.parametrize("enabled", [True, False])
def test_real_autobuild_rebuild_and_restart(tmp_path, enabled):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            body = _js(REMOTE).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        source = tmp_path / "docs"
        source.mkdir()
        output = tmp_path / "html"
        log = tmp_path / "autobuild.log"
        url = f"http://127.0.0.1:{server.server_port}/searchindex.js"
        projects = [{"name": "Remote", "base_url": "https://example.com/",
                     "searchindex_url": url}]
        (source / "conf.py").write_text(
            "extensions = ['sphinx_unified_search']\n"
            f"unified_search_projects = {projects!r}\n"
            f"unified_search_cache_remote_indexes = {enabled!r}\n",
            encoding="utf-8",
        )
        page = source / "index.rst"
        page.write_text("First\n=====\n\nInitial content.\n", encoding="utf-8")
        with autobuild(source, output, log) as process:
            assert len(requests) == 1
            page.write_text("Updated\n=======\n\nNew content.\n", encoding="utf-8")

            def rebuilt():
                index = output / "searchindex.js"
                try:
                    data = parse_searchindex(index.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    return False
                return (
                    data["titles"] == ["Updated", *REMOTE["titles"]]
                    and "new" in data["terms"]
                )

            wait_for(rebuilt, process, log)
            assert len(requests) == (1 if enabled else 2)
            mappings = json.loads(
                (output / "_static" / "unified_search_projects.json").read_text()
            )
            assert len(mappings) == 2
        previous_requests = len(requests)
        with autobuild(source, output, log):
            assert len(requests) == previous_requests + 1
            data = parse_searchindex((output / "searchindex.js").read_text())
            assert data["titles"] == ["Updated", *REMOTE["titles"]]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
