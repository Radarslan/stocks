from decimal import Decimal
from typing import Any
from typing import Optional


from app.crud.in_memory_base import get_all_keys
from app.crud.in_memory_base import get_all_sources
from app.crud.in_memory_base import read_data_from_list
from app.schemas.grafana.datapoints import Datapoint


def get_timeserie_datapoints(key: str) -> Optional[Datapoint]:
    if key.find(":") == -1:
        pass
    else:
        source = key.split(":")[0]
        asset = key.split(":")[1]
        asset_quotes = read_data_from_list(source, asset)
        if asset_quotes:
            return Datapoint(
                target=key,
                datapoints=[
                    [asset_quote.rate, asset_quote.timestamp]
                    for asset_quote in asset_quotes
                ],
            )
        return Datapoint(target=key, datapoints=[[]])


def get_table_rows(target: str) -> Optional[Any]:
    if target.find(":") == -1:

        all_keys = get_all_keys()
        result = {
            source: [
                {
                    "columns": [
                        {"text": "Asset", "type": "string"},
                        {"text": "Messages for 30 minutes", "type": "number"},
                        {
                            "text": "Average messages per second"
                                    "(last 5 minutes)",
                            "type": "number",
                        },
                    ],
                    "rows": [],
                    "type": "table-old",
                }
            ]
            for source in get_all_sources(all_keys)
        }
        for key in all_keys:
            source = key.split(":")[0]
            asset = key.split(":")[1]
            asset_quotes = read_data_from_list(source, asset)
            if asset_quotes:
                messages_for_30_minutes = len(asset_quotes)
                the_1st_timestamp = asset_quotes[-1].timestamp
                number_of_messages = 0
                five_minutes_in_milliseconds = 5 * 60 * 1000
                for i in range(len(asset_quotes) - 1, -1, -1):
                    if (
                            asset_quotes[i].timestamp - the_1st_timestamp
                            >= five_minutes_in_milliseconds
                    ):
                        break
                    else:
                        number_of_messages += 1
                average_number_of_messages_per_second_last_5_minutes = (
                        Decimal(number_of_messages)
                        / Decimal(five_minutes_in_milliseconds)
                )
                result[source][0]["rows"].append(
                    [
                        asset,
                        messages_for_30_minutes,
                        average_number_of_messages_per_second_last_5_minutes,
                    ]
                )
        return result[target]

    else:
        pass
