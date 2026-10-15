import hashlib
import json
from pathlib import Path

import psutil
from sphinx.util import logging

from .downloader import _build_headers

logger = logging.getLogger(__name__)


def autobuild_cache_dir(doctreedir: Path) -> Path | None:
    """Identify the nearest autobuild process, including in-process builders."""
    try:
        process = psutil.Process()
        while process is not None:
            command = process.cmdline()
            script = any(
                Path(arg).name in (
                    "sphinx-autobuild",
                    "sphinx-autobuild.exe",
                )
                for arg in command[:2]
            )
            module = any(
                flag == "-m" and name == "sphinx_autobuild"
                for flag, name in zip(command, command[1:])
            )
            if script or module:
                # Creation time prevents reuse if the OS recycles a process ID.
                session = f"{process.pid}:{process.create_time()}"
                key = hashlib.sha256(session.encode()).hexdigest()
                return Path(doctreedir) / "unified-search-cache" / key
            process = process.parent()
    except psutil.Error as exc:
        logger.warning(
            "[unified-search] cannot identify autobuild session; "
            "remote indexes will be downloaded on every build: %s",
            exc,
        )
    return None


def searchindex_cache_path(project: dict, cache_dir: Path) -> Path:
    """Key downloads by URL and resolved authentication, without saving tokens."""
    request = json.dumps(
        [project["searchindex_url"], _build_headers(project)],
        sort_keys=True,
    )
    key = hashlib.sha256(request.encode()).hexdigest()
    return cache_dir / f"{key}.js"
