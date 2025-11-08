import asyncio
import sys
import threading
from typing import Annotated
from typing_extensions import Literal

import janus
from treadmill_monitor.gui import Gui
from cyclopts import App, Parameter
from loguru import logger

from treadmill_monitor.interceptors import (
    GuiUpdateInterceptor,
    LoggingInterceptor,
    ResumableInterceptor,
    StdoutInterceptor,
    UpdateInterceptor,
    run_interceptor_chain,
)
from treadmill_monitor.models import TreadmillUpdate
from treadmill_monitor.producers import MtfsProducer, StdinProducer, UpdateProducer
from treadmill_monitor.serializers import (
    CsvSerializer,
    JsonlSerializer,
    UpdateSerializer,
)


app = App()


Format = Literal["csv", "jsonl"]


def get_serializer(format: Format) -> UpdateSerializer:
    match format:
        case "csv":
            return CsvSerializer(allow_missing_timestamp=True)
        case "jsonl":
            return JsonlSerializer()
        case _:
            raise ValueError(f"Unsupported format: {format}")


@app.default
async def main(
    address: str | None = None,
    input: Annotated[Format, Parameter(name=["-i", "--input"])] = None,
    output: Annotated[Format, Parameter(name=["-o", "--output"])] = None,
    resumable: Annotated[
        bool, Parameter(name=["-r", "--resumable"], negative="")
    ] = False,
    headless: Annotated[bool, Parameter(negative="")] = False,
    verbose: Annotated[bool, Parameter(negative="")] = False,
    debug: Annotated[bool, Parameter(negative="")] = False,
):
    """
    Monitor FTMS-enabled treadmill and display data in a GUI window.

    Args:
        address: Optional Bluetooth address of the FTMS device to connect to, specifying this will skip device scanning.
        input: Optional format of treadmill data to read from standard input.
        output: Optional format of treadmill data to write to standard output.
        resumable: Enable resumable mode that accumulates certain metrics across sessions until the application is closed.
        headless: Run in headless mode without GUI.
        verbose: Enable verbose logging.
        debug: Enable WebView debug mode and verbose logging.
    """
    log_level = "DEBUG" if debug or verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    interceptors: list[UpdateInterceptor] = [LoggingInterceptor("DEBUG")]
    close_event = threading.Event()

    if resumable:
        logger.info("Enabling resumable mode for certain metrics.")
        keys_to_accumulate = ["time_elapsed", "distance_total", "energy_total"]
        interceptors.append(ResumableInterceptor(keys_to_accumulate))

    if output:
        logger.info("Enabling stdout output for treadmill data.")
        interceptors.append(StdoutInterceptor(get_serializer(output)))

    gui: Gui | None = None
    if not headless:
        gui = Gui(
            debug=debug,
            confirm_close=resumable,
        )
        gui.on_close(lambda: close_event.set())
        gui.start()

        interceptors.append(GuiUpdateInterceptor(gui))

    producers: list[UpdateProducer] = [MtfsProducer(address)]

    if input:
        logger.info("Enabling stdin input for treadmill data.")
        producers.append(StdinProducer(get_serializer(input)))

    queue = janus.Queue[TreadmillUpdate]()
    producer_start_task = asyncio.gather(
        *[producer.start(queue) for producer in producers]
    )

    async def process_updates():
        while not close_event.is_set():
            try:
                async with asyncio.timeout(1):
                    update = await queue.async_q.get()
                    run_interceptor_chain(interceptors, update)

            except asyncio.TimeoutError:
                continue

    try:
        await process_updates()
    finally:
        logger.info("Shutting down...")
        close_event.set()

        await producer_start_task
        await asyncio.gather(*[producer.stop() for producer in producers])

        if gui is not None:
            gui.stop()
