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


def _merge_doc_ref_dict(merged: dict, remote: dict, key: str, offset: int):
    """
    Merge a "term -> [[docId, anchor, ...], ...]" style dict such as
    "alltitles" or "indexentries".

    Each entry's first element is a doc ID, so it must be shifted by
    ``offset``; the remaining elements (anchor, isMain flag) are kept
    as-is. Entries under a key that already exists (e.g. the same
    section heading in local docs) are appended, never replaced.
    """
    target = merged.setdefault(key, {})

    for name, entries in remote.get(key, {}).items():
        shifted = [[entry[0] + offset, *entry[1:]] for entry in entries]
        target.setdefault(name, []).extend(shifted)


def _merge_objects(merged: dict, remote: dict, offset: int):
    """
    Merge domain objects ("objects", "objnames", "objtypes").

    "objects" maps a prefix to entries of
    [docId, objTypeIndex, priority, anchor, name]. Both docId and
    objTypeIndex need remapping: docId by ``offset``, and objTypeIndex
    because each index has its own numbering of object types. Types
    are de-duplicated by their "domain:objtype" string so a remote's
    "py:function" reuses the local one instead of adding a copy.
    """
    if not remote.get("objects"):
        return

    m_types = merged.setdefault("objtypes", {})
    m_names = merged.setdefault("objnames", {})
    m_objects = merged.setdefault("objects", {})

    by_name = {value: idx for idx, value in m_types.items()}
    next_type = max((int(i) for i in m_types), default=-1) + 1

    type_map = {}
    for idx, value in remote.get("objtypes", {}).items():
        if value in by_name:
            type_map[int(idx)] = int(by_name[value])
            continue

        m_types[str(next_type)] = value
        if idx in remote.get("objnames", {}):
            m_names[str(next_type)] = remote["objnames"][idx]
        by_name[value] = str(next_type)
        type_map[int(idx)] = next_type
        next_type += 1

    for prefix, entries in remote["objects"].items():
        for entry in entries:
            doc_id, type_idx, *rest = entry
            m_objects.setdefault(prefix, []).append(
                [doc_id + offset, type_map.get(type_idx, type_idx), *rest]
            )


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

        #
        # Merge the remaining doc-ID-bearing structures. All of these
        # reference documents by position, so each must be shifted by
        # this remote's offset or they would point at the wrong docs.
        #
        # "filenames" runs parallel to "docnames"; pad with empty
        # strings if an older Sphinx didn't emit it, so positions stay
        # aligned for every doc that follows.
        #
        remote_filenames = remote_index.get("filenames") or [
            "" for _ in remote_index["docnames"]
        ]
        merged.setdefault("filenames", [""] * offset)
        merged["filenames"].extend(remote_filenames)

        _merge_doc_ref_dict(merged, remote_index, "alltitles", offset)
        _merge_doc_ref_dict(merged, remote_index, "indexentries", offset)
        _merge_objects(merged, remote_index, offset)

        logger.info(
            "[unified-search] merged filenames, alltitles, "
            "indexentries and objects from '%s'",
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
