import janus
from loguru import logger
import bleak
import pyftms
from dataclasses import dataclass


FTMS_SERVICE_UUID = "00001826-0000-1000-8000-00805f9b34fb"

UpdateValue = int | float

@dataclass
class TreadmillUpdate:
    key: str
    value: UpdateValue


class TreadmillClient:
    def __init__(self, address: str | None = None):
        self.address = address
        self.update_queue = janus.Queue[TreadmillUpdate]()
        self.client: pyftms.FitnessMachine | None = None

    def _on_ftms_event(self, event: pyftms.FtmsEvents):
        if isinstance(event, pyftms.UpdateEvent):
            for key, value in event.event_data.items():
                self.update_queue.sync_q.put(TreadmillUpdate(key=key, value=value))
                logger.debug(f"Received FTMS event: {key} = {value}")

    async def start(self):
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
            device = await bleak.BleakScanner.find_device_by_address(
                self.address, service_uuids=[FTMS_SERVICE_UUID]
            )

        logger.info(f"Connecting to device: {device.name} ({device.address})")

        self.client = pyftms.get_client(
            device, pyftms.MachineType.TREADMILL, on_ftms_event=self._on_ftms_event
        )

        await self.client.connect()

        logger.info("Connected successfully.")

    async def stop(self):
        if self.client is not None:
            logger.info("Disconnecting from treadmill...")
            await self.client.disconnect()
            logger.info("Disconnected successfully.")
