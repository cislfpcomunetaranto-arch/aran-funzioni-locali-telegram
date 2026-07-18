\
from dataclasses import dataclass


@dataclass(frozen=True)
class AranItem:
    item_id: str
    previous_id: str
    title: str
    area: str
    topic: str
    publication_date: str
    body: str
    url: str
