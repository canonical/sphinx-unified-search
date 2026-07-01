import json
from pathlib import Path

from sphinx.util import logging

from .downloader import download_searchindex
from .exceptions import SearchIndexError
from .parser import parse_searchindex

logger = logging.getLogger(__name__)


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
    # Maps merged document IDs to remote projects.
    #
    project_mapping = {}

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
        # Record which documents belong to this remote project.
        #
        for i, docname in enumerate(remote_index["docnames"]):
            project_mapping[offset + i] = {
                "project": remote["name"],
                "base_url": remote["base_url"],
                "docname": docname,
            }

        #
        # IMPORTANT:
        #
        # Keep remote docnames untouched.
        # Do NOT rewrite them to absolute URLs.
        #
        merged["docnames"].extend(
            remote_index["docnames"]
        )

        merged["titles"].extend(
            remote_index["titles"]
        )

        logger.info(
            "[unified-search] merged %d docnames from '%s'",
            len(remote_index["docnames"]),
            remote["name"],
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
