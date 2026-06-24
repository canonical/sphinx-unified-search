from dataclasses import dataclass


@dataclass
class RemoteProject:
    name: str
    searchindex_url: str
    base_url: str