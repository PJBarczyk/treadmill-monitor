from abc import ABC, abstractmethod
import datetime as dt
import json

from treadmill_monitor.models import TreadmillUpdate


def parse_value(value_str: str):
    try:
        if "." in value_str:
            return float(value_str)
        else:
            return int(value_str)
    except ValueError:
        raise ValueError(f"Invalid value: {value_str}")


class UpdateSerializer(ABC):
    @abstractmethod
    def serialize(self, update: TreadmillUpdate) -> str:
        pass

    @abstractmethod
    def deserialize(self, data: str) -> TreadmillUpdate:
        pass


class CsvSerializer(UpdateSerializer):
    def __init__(self, allow_missing_timestamp: bool = False):
        self.allow_missing_timestamp = allow_missing_timestamp

    def serialize(self, update: TreadmillUpdate) -> str:
        return f"{update.timestamp.isoformat()},{update.key},{update.value}"

    def deserialize(self, data: str) -> TreadmillUpdate:
        match data.strip().split(","):
            case [timestamp_str, key, value]:
                timestamp = dt.datetime.fromisoformat(timestamp_str)
                value_parsed = parse_value(value)
                return TreadmillUpdate(timestamp=timestamp, key=key, value=value_parsed)
            case [key, value] if self.allow_missing_timestamp:
                value_parsed = parse_value(value)
                return TreadmillUpdate(key=key, value=value_parsed)
            case _:
                raise ValueError(f"Invalid CSV row: {data.strip()}")


class JsonlSerializer(UpdateSerializer):
    def serialize(self, update: TreadmillUpdate) -> str:
        data = {
            "ts": update.timestamp.isoformat(),
            "key": update.key,
            "value": update.value,
        }
        return json.dumps(data, indent=None)

    def deserialize(self, data: str) -> TreadmillUpdate:
        import json

        obj = json.loads(data)
        try:
            timestamp = dt.datetime.fromisoformat(obj["timestamp"])
            key = obj["key"]
            value = parse_value(str(obj["value"]))
            return TreadmillUpdate(timestamp=timestamp, key=key, value=value)
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid JSON data: {data}") from e
