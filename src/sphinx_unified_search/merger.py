import json
from pathlib import Path

from .downloader import download_searchindex
from .parser import parse_searchindex


def merge_indexes(local_index: Path, remotes: list[dict]):

    merged = parse_searchindex(local_index.read_text())

    next_doc_id = len(merged["docnames"])

    for remote in remotes:

        raw = download_searchindex(
            remote["searchindex_url"]
        )

        remote_index = parse_searchindex(raw)

        offset = next_doc_id

        #
        # rewrite docnames to absolute URLs
        #

        rewritten = []

        for doc in remote_index["docnames"]:
            rewritten.append(
                remote["base_url"].rstrip("/")
                + "/"
                + doc
            )

        remote_index["docnames"] = rewritten

        #
        # merge docnames and titles
        #

        merged["docnames"].extend(
            remote_index["docnames"]
        )

        merged["titles"].extend(
            remote_index["titles"]
        )

        #
        # merge terms
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

        #
        # merge titleterms
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

        next_doc_id += len(
            remote_index["docnames"]
        )

    return merged


def write_searchindex(path, index):

    path.write_text(
        "Search.setIndex("
        + json.dumps(index)
        + ")"
    )