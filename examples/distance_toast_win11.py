# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "cyclopts",
#     "loguru",
#     "win11toast",
# ]
# ///
from win11toast import toast
from loguru import logger
from cyclopts import App
import sys


app = App()


@app.default
def main(every: int):
    """
    Show a Windows 11 toast notification with the specified distance every given number of seconds. Expects treadmill data in CSV format on standard input.

    Args:
        every: Distance in meters between notifications.
    """
    next_milestone: float | None = None

    logger.info(f"Starting distance toast notifications every {every} meters.")

    def on_distance_update(distance: int):
        nonlocal next_milestone

        if next_milestone is None:
            next_milestone = (distance // every) * every + every
            logger.debug(f"Initial milestone set to {next_milestone} meters.")

        if distance >= next_milestone:
            logger.info(f"Reached milestone: {next_milestone} meters.")
            milestone_km = next_milestone / 1000
            toast(
                "Milestone Reached!",
                f"You have reached {milestone_km:.2f}km.",
            )
            next_milestone += every
            logger.debug(f"Next milestone set to {next_milestone} meters.")

    for line in sys.stdin:
        match line.strip().split(",", 3):
            case [_, "distance_total", value_str]:
                try:
                    logger.debug(f"Received distance_total update: {value_str}")
                    distance = float(value_str) / 10
                    on_distance_update(int(distance))
                except ValueError:
                    logger.error(f"Invalid distance value: {value_str}")
            case _:
                continue


if __name__ == "__main__":
    app()
