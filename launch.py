"""
AuditDesk One-Click Python Launcher
Starts the server and automatically opens the user's browser.
"""

import os
import sys
import webbrowser
import threading

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from server import run_server, PORT

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port=port, auto_open=True)
