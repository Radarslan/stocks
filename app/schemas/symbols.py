from datetime import datetime
from decimal import Decimal
from typing import Any
from typing import Dict

from pydantic import BaseModel
from pydantic import condecimal

SYMBOL_QUOTE = Dict[str, Any]


class Asset(BaseModel):
    timestamp: datetime = 0
    symbol: str = ""
    rate: condecimal(gt=Decimal("0.0")) = Decimal("0.0")


class DXFeedAsset(Asset):
    market: str = ""


class MCFixAsset(Asset):
    pass
