import asyncio
from pathlib import Path
from typing import Annotated
import sys

from treadmill_monitor.client import TreadmillClient
from treadmill_monitor.processors import (
    CompoundTreadmillUpdateProcessor,
    CsvSinkTreadmillUpdateProcessor,
    ResumeableTreadmillUpdateProcessor,
    TreadmillUpdateProcessor,
)
from treadmill_monitor.templates import HTML
import webview
from cyclopts import App, Parameter, validators
from loguru import logger


async def app_logic(
    window: webview.Window,
    closed_event: asyncio.Event,
    update_processor: TreadmillUpdateProcessor,
    address: str | None = None,
):
    client = TreadmillClient(address)

    await client.start()

    while not closed_event.is_set():
        try:
            async with asyncio.timeout(1):
                update = await client.update_queue.async_q.get()
                processed_value = update_processor.process(update.key, update.value)

                setattr(window.state, update.key, processed_value)
                logger.debug(f"Updated window state: {update.key} = {processed_value}")
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            window.destroy()
            raise e

    await client.stop()


app = App()


@app.default
async def main(
    address: str | None = None,
    resumable: bool = False,
    log_file: Annotated[
        Path | None, Parameter(validator=validators.Path(dir_okay=False))
    ] = None,
    debug: bool = False,
):
    """
    Monitor FTMS-enabled treadmill and display data in a GUI window.

    Args:
        address: Optional Bluetooth address of the FTMS device to connect to, specifying this will skip device scanning.
        resumable: Enable resumable mode that accumulates certain metrics across sessions until the application is closed.
        log_file: Path to a CSV file where treadmill data will be logged.
        debug: Enable WebView debug mode and verbose logging.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if debug else "INFO")

    processors: list[TreadmillUpdateProcessor] = []

    if log_file is not None:
        logger.info(f"Logging treadmill data to CSV file: {log_file}")
        processors.append(CsvSinkTreadmillUpdateProcessor(log_file))
    if resumable:
        logger.info("Enabling resumable mode for certain metrics.")
        processors.append(ResumeableTreadmillUpdateProcessor())

    processor = CompoundTreadmillUpdateProcessor(processors)

    closed_event = asyncio.Event()
    window = webview.create_window(
        title="Treadmill Monitor",
        html=HTML,
        width=150,
        height=510,
        frameless=True,
        confirm_close=resumable,
    )
    window.events.closed += lambda: closed_event.set()

    webview.start(
        lambda: asyncio.run(app_logic(window, closed_event, processor, address)),
        debug=debug,
    )
