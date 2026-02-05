import threading
import time
from collections import deque
from datetime import datetime

import psutil
from flask import Flask, jsonify, render_template

try:
    import GPUtil  # optional
except Exception:
    GPUtil = None

# --- Flask app ---
app = Flask(__name__, static_folder='static', template_folder='templates')

# --- Ring buffers ---
MAX_SAMPLES = 240          # ~4 minutes @ 1s
SAMPLE_INTERVAL = 1.0      # seconds

cpu_series  = deque(maxlen=MAX_SAMPLES)
mem_series  = deque(maxlen=MAX_SAMPLES)
usage_ts    = deque(maxlen=MAX_SAMPLES)

read_series = deque(maxlen=MAX_SAMPLES)    # Disk MB/s
write_series= deque(maxlen=MAX_SAMPLES)
disk_ts     = deque(maxlen=MAX_SAMPLES)

rx_series   = deque(maxlen=MAX_SAMPLES)    # Net MB/s
tx_series   = deque(maxlen=MAX_SAMPLES)
net_ts      = deque(maxlen=MAX_SAMPLES)

# init so arrays are never empty
for _ in range(2):
    now = datetime.now().strftime('%H:%M:%S')
    cpu_series.append(0.0)
    mem_series.append(psutil.virtual_memory().percent)
    usage_ts.append(now)

    read_series.append(0.0)
    write_series.append(0.0)
    disk_ts.append(now)

    rx_series.append(0.0)
    tx_series.append(0.0)
    net_ts.append(now)

# --- Background sampler ---

def sampler():
    last_disk = psutil.disk_io_counters()
    last_net  = psutil.net_io_counters()
    last_time = time.time()

    psutil.cpu_percent(interval=None)  # establish baseline

    while True:
        now = time.time()
        elapsed = max(1e-6, now - last_time)
        now_dt = datetime.now().strftime('%H:%M:%S')

        # CPU/MEM
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        # Disk deltas -> MB/s
        cur_disk = psutil.disk_io_counters()
        read_mbs  = (cur_disk.read_bytes  - last_disk.read_bytes ) / (1024*1024) / elapsed
        write_mbs = (cur_disk.write_bytes - last_disk.write_bytes) / (1024*1024) / elapsed
        last_disk = cur_disk

        # Net deltas -> MB/s
        cur_net = psutil.net_io_counters()
        rx_mbs = (cur_net.bytes_recv - last_net.bytes_recv) / (1024*1024) / elapsed
        tx_mbs = (cur_net.bytes_sent - last_net.bytes_sent) / (1024*1024) / elapsed
        last_net = cur_net

        # Push
        cpu_series.append(float(cpu));   mem_series.append(float(mem));   usage_ts.append(now_dt)
        read_series.append(float(read_mbs)); write_series.append(float(write_mbs)); disk_ts.append(now_dt)
        rx_series.append(float(rx_mbs));     tx_series.append(float(tx_mbs));       net_ts.append(now_dt)

        last_time = now
        time.sleep(SAMPLE_INTERVAL)

threading.Thread(target=sampler, daemon=True).start()

# --- Lightweight caches for expensive endpoints ---
_PROCS_CACHE = {"data": None, "ts": 0.0}
_PROCS_TTL   = 2.0  # seconds


def _top_procs(n=5):
    global _PROCS_CACHE
    now = time.time()
    if _PROCS_CACHE["data"] and (now - _PROCS_CACHE["ts"] < _PROCS_TTL):
        return _PROCS_CACHE["data"]

    procs = []
    for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            info = p.info
            cpu = float(info.get('cpu_percent') or 0.0)
            rss = info.get('memory_info').rss if info.get('memory_info') else 0
            procs.append({
                'pid': int(info.get('pid')), 'name': (info.get('name') or 'proc')[:40],
                'cpu': cpu, 'mem_mb': float(rss) / (1024*1024)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    cpu_top = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:n]
    mem_top = sorted(procs, key=lambda x: x['mem_mb'], reverse=True)[:n]
    data = {'cpu_top': cpu_top, 'mem_top': mem_top, 'ts': datetime.now().strftime('%H:%M:%S')}
    _PROCS_CACHE = {"data": data, "ts": now}
    return data


def _read_temps():
    temps = []
    try:
        sensors = psutil.sensors_temperatures(fahrenheit=False)  # may not exist on win
        for label, entries in sensors.items():
            vals = [e.current for e in entries if getattr(e, 'current', None) is not None]
            if vals:
                temps.append({'label': label, 'current': float(max(vals))})
    except Exception:
        pass
    return temps


def _read_gpus():
    gpus = []
    if not GPUtil:
        return {'available': False, 'gpus': []}
    try:
        for g in GPUtil.getGPUs():
            gpus.append({
                'id': int(getattr(g, 'id', 0)),
                'name': getattr(g, 'name', 'GPU'),
                'load': float(getattr(g, 'load', 0.0) * 100.0),
                'mem_used_mb': float(getattr(g, 'memoryUsed', 0.0)),
                'mem_total_mb': float(getattr(g, 'memoryTotal', 0.0)),
                'temp': float(getattr(g, 'temperature', 0.0) or 0.0)
            })
        return {'available': bool(gpus), 'gpus': gpus}
    except Exception:
        return {'available': False, 'gpus': []}

# --- Routes ---
@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/usage')
def api_usage():
    return jsonify({'cpu': list(cpu_series), 'memory': list(mem_series), 'timestamps': list(usage_ts)})

@app.route('/api/disk')
def api_disk():
    return jsonify({'read': list(read_series), 'write': list(write_series), 'timestamps': list(disk_ts)})

@app.route('/api/net')
def api_net():
    return jsonify({'rx': list(rx_series), 'tx': list(tx_series), 'timestamps': list(net_ts)})

@app.route('/api/procs/top')
def api_procs_top():
    return jsonify(_top_procs(n=5))

@app.route('/api/temps')
def api_temps():
    return jsonify({'temps': _read_temps()})

@app.route('/api/gpu')
def api_gpu():
    return jsonify(_read_gpus())

@app.route('/health')
def health():
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)