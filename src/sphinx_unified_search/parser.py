import json
import re

PATTERN = re.compile(
    r"Search\.setIndex\((.*)\)\s*$",
    re.DOTALL,
)


def parse_searchindex(contents: str) -> dict:
    match = PATTERN.search(contents)

    if not match:
        raise ValueError("Invalid Sphinx search index")

    payload = match.group(1)

    return json.loads(payload)