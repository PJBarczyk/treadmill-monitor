<img align="right" width="200" src="preview.png" />

# Treadmill Monitor

A cross-platform desktop application to monitor and log data from FTMS-enabled treadmills over Bluetooth Low Energy (BLE).

## Features

- Auto-discovery of FTMS devices
- Support for accumulating metrics after treadmill resets
- Real-time display of treadmill metrics
- [DaisyUI](https://daisyui.com/)-based user interface
- Logging data in CSV or JSONL format
- Integration with other applications via standard output

## Usage

The recommended way to run the application is via the `uvx` command shipped with [uv](https://docs.astral.sh/uv/):

```sh
uvx --python 3.13 https://github.com/PJBarczyk/treadmill-monitor.git
```

or by installing it to path using `uv tool install`:

```sh
uv tool install --python 3.13 https://github.com/PJBarczyk/treadmill-monitor.git
treadmill-monitor
```

*Python 3.13 is recommended due to 3.14 not being fully supported by some dependencies at the time of writing.*

---

Use `--resumable` flag to enable accumulation of metrics after treadmill resets (e.g. distance, calories) while the application is running.

```sh
treadmill-monitor --resumable
```

To skip device discovery and connect directly to a treadmill with known MAC address, use `--address <MAC_ADDRESS>`; check the logs for the address when the device is discovered.

```sh
treadmill-monitor --address <MAC_ADDRESS>
```

## Logging Data

The tool offers the ability to send treadmill data to standard output in CSV or JSONL format with `--output <format>`. To log data to a file, you can redirect the output when starting the application:

```bash
treadmill-monitor --output csv > log.csv
```

## Integration with other applications

You can use the `--output` option to send treadmill data to other scripts or applications. For example, publish data to NATS broker:

```sh
treadmill-monitor --output jsonl | nats pub -q --send-on newline treadmill.updates
```

or process events with a custom Python script, as showcased in the [examples](examples) directory. For instance, to show Windows 11 toast notifications for distance updates every 100 meters:

```pwsh
treadmill-monitor -o csv | Tee-Object NUL | uv run .\examples\distance_toast_win11.py --every 100
```

*Because of how PowerShell handles output, you may need to use `Tee-Object` to properly pass data to downstream commands without buffering issues.*

If you're interested only in streaming data without the GUI, use the `--headless` option to disable the graphical interface.

## Limitations

- Only one BLE client can reliably connect to a treadmill at a time. Ensure no other applications (e.g. smartphone apps) are connected to the treadmill while using this application.
- *Fitness Machine Control Point* characteristic is not supported; the application is read-only.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.