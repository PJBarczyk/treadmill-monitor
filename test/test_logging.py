import tempfile
from pathlib import Path

from freezegun import freeze_time

from treadmill_monitor.processors import CsvSinkTreadmillUpdateProcessor


@freeze_time("2012-12-21")
def test_logging():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "log.csv"
        processor = CsvSinkTreadmillUpdateProcessor(tmp_path)
        processor.process("speed_current", 5.5)

        assert tmp_path.read_text() == "2012-12-21T00:00:00,speed_current,5.5\n"
