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