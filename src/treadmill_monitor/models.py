from dataclasses import dataclass
import datetime as dt

__all__ = ["TreadmillUpdate", "UpdateValue"]

UpdateValue = int | float


@dataclass
class TreadmillUpdate:
    timestamp: dt.datetime
    key: str
    value: UpdateValue
