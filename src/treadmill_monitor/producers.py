import asyncio
import datetime as dt
import sys

import bleak
import janus
import pyftms
from loguru import logger

from treadmill_monitor.models import TreadmillUpdate
from treadmill_monitor.serializers import UpdateSerializer

__all__ = ["UpdateProducer", "StdinProducer", "MtfsProducer"]


class UpdateProducer:
    async def start(self, queue: janus.Queue[TreadmillUpdate]):
        pass

    async def stop(self):
        pass


class StdinProducer(UpdateProducer):
    def __init__(self, serializer: UpdateSerializer):
        self.serializer = serializer
        self._stdin_task: asyncio.Task | None = None

    async def start(self, queue: janus.Queue[TreadmillUpdate]):
        loop = asyncio.get_running_loop()

        def read_stdin():
            for line in sys.stdin:
                try:
                    update = self.serializer.deserialize(line)
                    queue.sync_q.put(update)
                except ValueError as e:
                    logger.error(e)

        self._stdin_task = loop.run_in_executor(None, read_stdin)

    async def stop(self):
        if self._stdin_task is not None:
            self._stdin_task.cancel()
            try:
                await self._stdin_task
            except asyncio.CancelledError:
                pass


FTMS_SERVICE_UUID = "00001826-0000-1000-8000-00805f9b34fb"


class MtfsProducer(UpdateProducer):
    def __init__(self, address: str | None = None):
        self.address = address
        self.client: pyftms.FitnessMachine | None = None

    async def start(self, queue: janus.Queue[TreadmillUpdate]):
        if self.address is None:
            logger.info("Scanning for MTFS-enabled treadmill devices...")
            devices = await bleak.BleakScanner.discover(
                service_uuids=[FTMS_SERVICE_UUID],
            )

            if not devices:
                raise RuntimeError("No MTFS devices found.")

            if len(devices) > 1:
                logger.warning(
                    "Multiple MTFS-enabled treadmill devices found. Connecting to the first one."
                )

            device = devices[0]
        else:
            logger.info(f"Looking for device with address {self.address}...")
            device = await bleak.BleakScanner.find_device_by_address(
                self.address, service_uuids=[FTMS_SERVICE_UUID]
            )

            if device is None:
                logger.error(f"Could not find device with address {self.address}")
                return

        logger.info(f"Connecting to device: {device.name} ({device.address})")

        def on_ftms_event(event: pyftms.FtmsEvents):
            if isinstance(event, pyftms.UpdateEvent):
                for key, value in event.event_data.items():
                    update = TreadmillUpdate(
                        timestamp=dt.datetime.now(),
                        key=key,
                        value=value,
                    )
                    queue.sync_q.put(update)

        self.client = pyftms.get_client(
            device, pyftms.MachineType.TREADMILL, on_ftms_event=on_ftms_event
        )

        await self.client.connect()

        logger.info("Connected successfully.")

    async def stop(self):
        if self.client is not None:
            logger.info("Disconnecting from treadmill...")
            await self.client.disconnect()
            logger.info("Disconnected successfully.")
