import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(BASE_DIR, "logs", "system_log.csv")
OUT_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(OUT_DIR, exist_ok=True)

# load data once
df = pd.read_csv(LOG_PATH, parse_dates=["timestamp"])

# CPU Usage
plt.figure()
plt.plot(df["timestamp"], df["cpu_percent"], label="CPU %")
plt.xlabel("Time"); plt.ylabel("CPU Usage (%)")
plt.title("CPU Usage Over Time"); plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "cpu_usage.png"))
plt.close()

# Memory Usage
plt.figure()
plt.plot(df["timestamp"], df["memory_percent"], label="Mem %")
plt.xlabel("Time"); plt.ylabel("Memory Usage (%)")
plt.title("Memory Usage Over Time"); plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "memory_usage.png"))
plt.close()

# Disk I/O
plt.figure()
plt.plot(df["timestamp"], df["disk_read_bytes"],  label="Read Bytes")
plt.plot(df["timestamp"], df["disk_write_bytes"], label="Write Bytes")
plt.xlabel("Time"); plt.ylabel("Bytes")
plt.title("Disk I/O Over Time"); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "disk_io.png"))
plt.close()

# Network I/O
plt.figure()
plt.plot(df["timestamp"], df["net_bytes_sent"], label="Sent Bytes")
plt.plot(df["timestamp"], df["net_bytes_recv"], label="Recv Bytes")
plt.xlabel("Time"); plt.ylabel("Bytes")
plt.title("Network I/O Over Time"); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "network_io.png"))
plt.close()
