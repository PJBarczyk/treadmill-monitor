from collections.abc import Callable
import multiprocessing
import queue
import threading

import webview

from treadmill_monitor.models import TreadmillUpdate


class Gui:
    def __init__(self, debug: bool = False, confirm_close: bool = False):
        self.debug = debug
        self.confirm_close = confirm_close

        self._update_queue: queue.Queue[TreadmillUpdate] = multiprocessing.Queue()
        self._closed_event: threading.Event = multiprocessing.Event()
        self._process: multiprocessing.Process | None = None
        self._on_close_callbacks: list[Callable[[], None]] = []

    def push_update(self, update: TreadmillUpdate):
        self._update_queue.put(update)

    def start(self):
        assert self._process is None, "GuiMonitor is already started."

        def handle_close_callbacks():
            self._closed_event.wait()
            [cb() for cb in self._on_close_callbacks]

        threading.Thread(target=handle_close_callbacks, daemon=True).start()

        self._process = multiprocessing.Process(
            target=self._run_webview,
            args=(
                self._update_queue,
                self._closed_event,
                self.debug,
                self.confirm_close,
            ),
        )
        self._process.start()

    def stop(self):
        assert self._process is not None, "GuiMonitor is not started."
        self._closed_event.set()
        self._process.terminate()
        self._process.join()
        self._process = None

    @staticmethod
    def _run_webview(
        update_queue: queue.Queue[TreadmillUpdate],
        closed_event: threading.Event,
        debug: bool,
        confirm_close: bool,
    ):
        loaded_event = threading.Event()
        window = webview.create_window(
            title="Treadmill Monitor",
            html=HTML,
            width=150,
            height=510,
            frameless=True,
            confirm_close=confirm_close,
        )

        window.events.loaded += lambda: loaded_event.set()
        window.events.closed += lambda: closed_event.set()

        def wait_for_close():
            closed_event.wait()
            window.destroy()

        threading.Thread(target=wait_for_close, daemon=True).start()

        def func():
            loaded_event.wait()
            while not closed_event.is_set():
                try:
                    update = update_queue.get(timeout=0.1)
                    setattr(window.state, update.key, update.value)
                except queue.Empty:
                    pass

        webview.start(func, debug=debug)

    def on_close(self, callable: Callable[[], None]):
        self._on_close_callbacks.append(callable)
        return callable


HTML = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <title>Treadmill Monitor</title>
</head>
<body class="p-2">
  <div class="mt-2 flex flex-col">
    <div class="ms-6 flex gap-2 items-center">
      <div id="status" class="status"></div>
      <span data-stat="training_status">Offline</span>
    </div>

    <div class="stats stats-vertical shadow">      
      <div class="stat">
        <div class="stat-title">Current speed</div>
        <div class="stat-value">
          <span data-stat="speed_instant">0.0</span>
          <span class="text-xl">km/h</span> 
        </div>
      </div>
      
      <div class="stat">
        <div class="stat-title">Elapsed time</div>
        <div class="stat-value text-3xl mt-1" data-stat="time_elapsed">00:00:00</div>
      </div>
      
      <div class="stat">
        <div class="stat-title">Total distance</div>
        <div class="stat-value">
          <span data-stat="distance_total">0.00</span>
          <span class="text-xl">km</span>
        </div>
      </div>

      <div class="stat">
        <div class="stat-title">Calories burned</div>
        <div class="stat-value">
          <span data-stat="energy_total">0</span>
          <span class="text-xl">kcal</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    window.addEventListener('pywebviewready', function() {
      window.pywebview.state.addEventListener('change', e => {
        const key = e.detail.key;
        let value = e.detail.value;

        let statusIndicator = document.getElementById('status');
        if (statusIndicator && key === 'training_status') {
          statusIndicator.className = 'status' + {
            0: ' status-warning',
            1: ' status-error',
            2: ' status-warning',
            3: ' status-success',
            4: ' status-success',
            5: ' status-success',
            6: ' status-success',
            7: ' status-success',
            8: ' status-success',
            9: ' status-warning',
            10: ' status-warning',
            11: ' status-success',
            12: ' status-success',
            13: ' status-success',
            14: ' status-warning',
            15: ' status-warning',
          }[value] || '';
        }

        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
          if (key === 'training_status') {
            value = {
              0: 'Other',
              1: 'Idle',
              2: 'Warming Up',
              3: 'Low Intensity Interval',
              4: 'High Intensity Interval',
              5: 'Recovery Interval',
              6: 'Isometric',
              7: 'Heart Rate Control',
              8: 'Fitness Test',
              9: 'Speed Too Low',
              10: 'Speed Too High',
              11: 'Cool Down',
              12: 'Watt Control',
              13: 'Manual Mode',
              14: 'Pre-Workout',
              15: 'Post-Workout',
            }[value] || 'Unknown';
          }
          else if (key === 'time_elapsed') {
            value = new Date(value * 1000).toISOString().slice(11, 19);
          }
          else if (key === 'speed_instant') {
            value = parseFloat(value).toFixed(1);
          }
          else if (key === 'distance_total') {
            value = parseFloat(value / 10000).toFixed(2);
          }
          else if (key === 'energy_total') {
            value = Math.floor(value / 10);
          }

          element.textContent = value;
        }
      });
    });
  </script>
</body>
</html>
"""
