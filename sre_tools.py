import psutil
import subprocess
from langchain_core.tools import tool

@tool
def get_system_metrics() -> str:
    """
    Returns current system health metrics including CPU, Memory, and Disk usage.
    Call this tool first when investigating performance degradation or system crashes.
    """
    # Grab CPU usage over a 1-second interval for accuracy
    cpu = psutil.cpu_percent(interval=1)
    
    # Grab RAM metrics
    memory = psutil.virtual_memory()
    mem_used_gb = memory.used / (1024**3)
    mem_total_gb = memory.total / (1024**3)
    
    # Grab Disk metrics for the root volume
    disk = psutil.disk_usage('/')
    
    return (
        f"CPU Usage: {cpu}%\n"
        f"Memory Usage: {memory.percent}% ({mem_used_gb:.2f}GB / {mem_total_gb:.2f}GB)\n"
        f"Root Disk Usage: {disk.percent}%"
    )

@tool
def read_local_log(file_path: str, lines: int = 20) -> str:
    """
    Safely reads the last N lines of a log file to look for errors or stack traces.
    Args:
        file_path: The absolute path to the log file (e.g., '/var/log/system.log').
        lines: The number of recent lines to read. Default is 20.
    """
    try:
        # We use standard macOS 'tail' via subprocess. 
        # This is safer and vastly more memory-efficient than reading the whole file in Python.
        result = subprocess.run(
            ['tail', '-n', str(lines), file_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: Command failed. {e.stderr}"
    except Exception as e:
        return f"Error accessing {file_path}: {str(e)}"

# Quick manual test block (will only run if you execute this file directly)
if __name__ == "__main__":
    print("--- Testing get_system_metrics ---")
    print(get_system_metrics.invoke({}))
    
    print("\n--- Testing read_local_log ---")
    # We will test reading the standard macOS install log as a safe dummy target
    print(read_local_log.invoke({"file_path": "/var/log/install.log", "lines": 5}))
