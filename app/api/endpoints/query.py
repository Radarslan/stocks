from typing import Any

from fastapi import APIRouter

from app.core.business_logic_layer.assets import get_table_rows
from app.core.business_logic_layer.assets import get_timeserie_datapoints
from app.schemas.grafana.queries import CreateQuery

router = APIRouter()


@router.post("", tags=["query"])
async def query(*, query: CreateQuery) -> Any:
    if query and query.targets and query.targets[0].target:
        if query.targets[0].type == "table":
            return get_table_rows(query.targets[0].target)
        elif query.targets[0].type == "timeserie":
            return [
                get_timeserie_datapoints(target_query.target)
                for target_query in query.targets
            ]