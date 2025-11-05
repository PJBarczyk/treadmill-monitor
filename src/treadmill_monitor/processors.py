from pathlib import Path
from loguru import logger
from treadmill_monitor.client import UpdateValue
import datetime as dt


class TreadmillUpdateProcessor:
    def process(self, key: str, value: UpdateValue) -> UpdateValue:
        return value


class CsvSinkTreadmillUpdateProcessor(TreadmillUpdateProcessor):
    def __init__(self, path: Path):
        self.path = path
        self.last_written: dict[str, UpdateValue] = dict()

    def process(self, key: str, value: UpdateValue) -> UpdateValue:
        if self.last_written.get(key) == value:
            return value

        self.last_written[key] = value

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(f"{dt.datetime.now().isoformat()},{key},{value}\n")

        return value


class CompoundTreadmillUpdateProcessor:
    def __init__(self, processors: list[TreadmillUpdateProcessor]):
        self.processors = processors

    def process(self, key: str, value: UpdateValue) -> UpdateValue:
        for processor in self.processors:
            value = processor.process(key, value)
        return value


class ResumeableTreadmillUpdateProcessor(TreadmillUpdateProcessor):
    KEYS_TO_ACCUMULATE = {"time_elapsed", "distance_total", "energy_total"}

    def __init__(self):
        self.active = dict()
        self.accumulate = dict()

    def process(self, key: str, value: UpdateValue) -> UpdateValue:
        if key not in self.KEYS_TO_ACCUMULATE:
            return value

        if value == 0 and self.active.get(key, False):
            last_value = self.active.pop(key)
            self.accumulate[key] = self.accumulate.get(key, 0) + last_value
            logger.info(
                f"Detected reset for '{key}'. Accumulated value is now {self.accumulate[key]}."
            )

        self.active[key] = value
        return value + self.accumulate.get(key, 0)
