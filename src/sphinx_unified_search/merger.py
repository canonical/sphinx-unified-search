import json
import re
from pathlib import Path

from sphinx.util import logging

from .downloader import download_searchindex
from .exceptions import SearchIndexError
from .parser import parse_searchindex

logger = logging.getLogger(__name__)


def _project_key(name: str) -> str:
    """
    Turn a project name into a filesystem/URL-safe, unique-ish slug
    used to namespace that project's docnames in the merged index.
    """
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "project"


def merge_indexes(local_index: Path, remotes: list[dict]):
    logger.info(
        "[unified-search] reading local index %s",
        local_index,
    )

    merged = parse_searchindex(
        local_index.read_text(encoding="utf-8")
    )

    logger.info(
        "[unified-search] local index contains %d docs",
        len(merged["docnames"]),
    )

    next_doc_id = len(merged["docnames"])

    #
    # Maps a namespaced, collision-proof docname to its remote
    # project info. Keyed by string, not by doc id, so the client
    # can do an exact lookup instead of a fuzzy scan.
    #
    project_mapping = {}

    used_keys = set()

    for remote in remotes:
        logger.info(
            "[unified-search] merging project '%s'",
            remote["name"],
        )

        try:
            raw = download_searchindex(remote)

            remote_index = parse_searchindex(raw)

            logger.info(
                "[unified-search] remote project '%s' contains %d docs",
                remote["name"],
                len(remote_index["docnames"]),
            )

        except SearchIndexError as exc:
            #
            # Auth-related failures are treated as fatal by default,
            # since a bad/missing token should not silently produce
            # an incomplete search index. Set "required": False on a
            # project to downgrade this to a warning instead.
            #
            if remote.get("required", True):
                logger.warning(
                    "[unified-search] required project '%s' failed: %s",
                    remote["name"],
                    exc,
                )
                raise

            logger.warning(
                "[unified-search] skipping optional project '%s': %s",
                remote["name"],
                exc,
            )
            continue

        except Exception as exc:
            logger.warning(
                "[unified-search] skipping project '%s': %s",
                remote["name"],
                exc,
            )
            continue

        offset = next_doc_id

        #
        # Namespace this project's docnames so two remote projects
        # (or a remote project and the local docs) can never collide
        # on the same relative path, e.g. both having root/tutorial/index.
        #
        # A collision here doesn't just cause a display glitch — it
        # causes the WRONG remote project's base_url to be used when
        # building a result's link, because the client-side lookup
        # previously matched on the raw docname string alone.
        #
        base_key = _project_key(remote["name"])

        project_key = base_key
        suffix = 2
        while project_key in used_keys:
            project_key = f"{base_key}-{suffix}"
            suffix += 1
        used_keys.add(project_key)

        namespaced_docnames = [
            f"__unified__/{project_key}/{docname}"
            for docname in remote_index["docnames"]
        ]

        #
        # IMPORTANT:
        #
        # The ORIGINAL docname (unprefixed) is what gets used to
        # build the real remote URL, so it's preserved untouched in
        # project_mapping. Only the copy stored in merged["docnames"]
        # is namespaced — that's the string Sphinx's own search UI
        # uses to build hrefs, which is what makes it possible for
        # the client to look projects up unambiguously.
        #
        for namespaced, original in zip(
            namespaced_docnames,
            remote_index["docnames"],
        ):
            project_mapping[namespaced] = {
                "project": remote["name"],
                "base_url": remote["base_url"],
                "docname": original,
            }

        merged["docnames"].extend(namespaced_docnames)

        merged["titles"].extend(
            remote_index["titles"]
        )

        logger.info(
            "[unified-search] merged %d docnames from '%s' (namespace: %s)",
            len(remote_index["docnames"]),
            remote["name"],
            project_key,
        )

        #
        # Merge terms
        #
        for term, refs in remote_index["terms"].items():
            if isinstance(refs, int):
                refs = [refs]

            refs = [r + offset for r in refs]

            existing = merged["terms"].setdefault(
                term,
                [],
            )

            if isinstance(existing, int):
                existing = [existing]

            merged["terms"][term] = sorted(
                set(existing + refs)
            )

        logger.info(
            "[unified-search] merged terms from '%s'",
            remote["name"],
        )

        #
        # Merge titleterms
        #
        for term, refs in remote_index["titleterms"].items():
            if isinstance(refs, int):
                refs = [refs]

            refs = [r + offset for r in refs]

            existing = merged["titleterms"].setdefault(
                term,
                [],
            )

            if isinstance(existing, int):
                existing = [existing]

            merged["titleterms"][term] = sorted(
                set(existing + refs)
            )

        logger.info(
            "[unified-search] merged titleterms from '%s'",
            remote["name"],
        )

        next_doc_id += len(
            remote_index["docnames"]
        )

    logger.info(
        "[unified-search] final merged index contains %d docs",
        len(merged["docnames"]),
    )

    return merged, project_mapping


def write_searchindex(path: Path, index: dict):
    logger.info(
        "[unified-search] writing merged search index to %s",
        path,
    )

    path.write_text(
        "Search.setIndex("
        + json.dumps(index)
        + ")",
        encoding="utf-8",
    )

    logger.info(
        "[unified-search] search index successfully written"
    )
