import psutil
import time
import pandas as pd
from datetime import datetime
import os

# Resolve absolute path to the logs directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(BASE_DIR, "logs", "system_log.csv")

def log_metrics():
    while True:
        # gather system metrics
        counters = psutil.disk_io_counters()
        net     = psutil.net_io_counters()
        data = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'num_processes': len(psutil.pids()),
            'disk_read_bytes': counters.read_bytes,
            'disk_write_bytes': counters.write_bytes,
            'net_bytes_sent': net.bytes_sent,
            'net_bytes_recv': net.bytes_recv
        }
        # append to CSV
        df = pd.DataFrame([data])
        df.to_csv(LOG_PATH,
                  mode='a',
                  header=not os.path.exists(LOG_PATH),
                  index=False)
        time.sleep(5)

if __name__ == "__main__":
    log_metrics()
