import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Resolve paths (adjust as needed)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(BASE_DIR, "logs", "system_log.csv")
OUT_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(OUT_DIR, exist_ok=True)

def plot_metrics():
    df = pd.read_csv(LOG_PATH, parse_dates=["timestamp"])
    # CPU
    plt.figure()
    plt.plot(df["timestamp"], df["cpu_percent"], linewidth=2)
    plt.xlabel("Time"); plt.ylabel("CPU Usage (%)"); plt.title("CPU Usage Over Time")
    plt.tight_layout()
    cpu_png = os.path.join(OUT_DIR, "cpu_usage.png")
    plt.savefig(cpu_png, transparent=True)
    plt.close()

    # Memory
    plt.figure()
    plt.plot(df["timestamp"], df["memory_percent"], linewidth=2)
    plt.xlabel("Time"); plt.ylabel("Memory Usage (%)"); plt.title("Memory Usage Over Time")
    plt.tight_layout()
    mem_png = os.path.join(OUT_DIR, "memory_usage.png")
    plt.savefig(mem_png, transparent=True)
    plt.close()
