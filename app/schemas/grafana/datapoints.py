from typing import Any
from typing import List

from pydantic import BaseModel


class Datapoint(BaseModel):
    target: str = ""
    datapoints: List[List[Any]] = [[]]
