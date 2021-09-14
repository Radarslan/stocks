from typing import List

from pydantic import BaseModel

Targets = List[str]


class GrafanaQuery(BaseModel):
    target: str
    refId: str
    type: str


class CreateQuery(BaseModel):
    targets: List[GrafanaQuery]
