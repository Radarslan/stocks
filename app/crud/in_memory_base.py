from typing import Any
from typing import List
from typing import Optional

from app.schemas.grafana.queries import Targets


def get_all_keys() -> Targets:
    from app.api.main import app
    return sorted(
        [
            ":".join([source, asset])
            for source in app.stocks_client.asset_quotes
            for asset in app.stocks_client.asset_quotes[source]
        ]
    )


def get_all_sources(all_keys: List[str]) -> Targets:
    return sorted(list(set([key.split(":")[0] for key in all_keys])))


def read_data_from_list(source: str, asset: str) -> Optional[List[Any]]:
    from app.api.main import app
    assets = app.stocks_client.asset_quotes.get(source, {})
    if assets:
        return assets.get(asset, None)

