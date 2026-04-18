#!/usr/bin/env python3
"""
ASTRA Auto-Start Module
Ensures ASTRA server starts and opens display when imported
"""
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# Add ASTRA to path
ASTRA_DIR = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")
sys.path.insert(0, str(ASTRA_DIR))

def is_server_running():
    """Check if ASTRA server is already running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "astra_live_backend.server"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def start_server():
    """Start ASTRA server in background"""
    if is_server_running():
        print("ASTRA server is already running")
        return True

    print("Starting ASTRA server...")
    os.chdir(ASTRA_DIR)

    # Start server in background
    log_file = open("/tmp/astra_server.log", "w")
    subprocess.Popen(
        [sys.executable, "-m", "astra_live_backend.server"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

    # Wait for server to initialize
    print("Waiting for server to start...")
    for i in range(10):
        time.sleep(1)
        if is_server_running():
            print("ASTRA server started successfully!")
            return True

    print("Failed to start ASTRA server")
    return False

def open_dashboard():
    """Open ASTRA dashboard in browser"""
    print("Opening ASTRA dashboard...")
    webbrowser.open("http://localhost:8787")
    print("Dashboard: http://localhost:8787")

def auto_start():
    """Auto-start ASTRA server and open dashboard"""
    if start_server():
        time.sleep(2)  # Give server time to fully initialize
        open_dashboard()
        return True
    return False

if __name__ == "__main__":
    auto_start()
