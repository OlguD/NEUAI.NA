"""
NEUAI Launcher - Simple version with 'Q' key shutdown

This script launches the NEUAI Flask application and allows shutting it down
by pressing the 'Q' key.
"""

import subprocess
import time
import webbrowser
import os
import sys
import socket
import platform
import datetime
import threading
import msvcrt  # Windows-specific module for keyboard input
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("neuai_debug.log"),
        logging.StreamHandler()
    ]
)

def print_status(message, status="info"):
    """Print status messages with appropriate formatting"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    if status == "success":
        prefix = f"[{timestamp}] ✓ "
        logging.info(message)
    elif status == "error":
        prefix = f"[{timestamp}] ✗ "
        logging.error(message)
    elif status == "warning":
        prefix = f"[{timestamp}] ⚠ "
        logging.warning(message)
    else:
        prefix = f"[{timestamp}] → "
        logging.info(message)
    print(prefix + message)

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def print_system_info():
    """Print system information for diagnostics"""
    print("\nSystem Information:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  Interpreter: {sys.executable}")
    print()

def check_for_quit(proc):
    """Monitor for 'Q' key press to quit the application"""
    print_status("SERVER IS RUNNING - Press 'Q' key to stop and exit", "success")
    print("\n" + "=" * 60)
    print("  To stop the server and exit: PRESS THE 'Q' KEY")
    print("  For debug info if app freezes: PRESS THE 'D' KEY")
    print("=" * 60 + "\n")
    
    while proc.poll() is None:
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
            if key == 'Q':
                print_status("\nStopping server due to user request...", "info")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print_status("Server stopped successfully", "success")
                except subprocess.TimeoutExpired:
                    print_status("Server not responding, forcing shutdown", "warning")
                    proc.kill()
                print("\nThank you for using NEUAI Recognition System!")
                # Use os._exit to truly exit and return control to the batch file
                os._exit(0)
            elif key == 'D':
                print_status("\nGenerating debug information...", "info")
                print_status("Active threads: " + str(threading.active_count()), "info")
                print_status("Server process status: " + ("Running" if proc.poll() is None else f"Terminated ({proc.returncode})"), "info")
                try:
                    # Get current memory usage
                    import psutil
                    process = psutil.Process(proc.pid)
                    memory_info = process.memory_info()
                    print_status(f"Server memory usage: {memory_info.rss / 1024 / 1024:.2f} MB", "info")
                except ImportError:
                    print_status("psutil not installed. Install for detailed memory info.", "warning")
                except Exception as e:
                    print_status(f"Error getting process info: {str(e)}", "error")
        time.sleep(0.1)

# Main code
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("             NEUAI Recognition System")
    print("          Face and Document Analysis Suite")
    print("=" * 60)
    print("         Made by Olgu Degirmenci and")
    print("               Atakan Uzun")
    print("=" * 60 + "\n")

    # Print system info
    print_system_info()

    # Define Flask parameters
    port = 5000
    host = '127.0.0.1'
    url = f"http://{host}:{port}"
    
    # Check if running in debug mode
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        print_status("Running in DEBUG mode - verbose logging enabled", "warning")
        logging.getLogger().setLevel(logging.DEBUG)
        flask_debug = "1"
    else:
        flask_debug = "0"
        
    # Check if port is already in use
    if is_port_in_use(port):
        print_status(f"Port {port} is already in use. Application might already be running.", "warning")
        print_status(f"Opening browser to {url}", "info")
        webbrowser.open(url)
        sys.exit(0)

    # Start the Flask app
    try:
        print_status(f"Starting NEUAI server on {url}")
        
        # Get Python executable
        python_executable = sys.executable
        print_status(f"Using Python interpreter: {python_executable}")
        
        # Set environment variables
        flask_env = os.environ.copy()
        flask_env["FLASK_APP"] = "neuai.app"
        flask_env["FLASK_DEBUG"] = flask_debug
        flask_env["NEUAI_FACE_TIMEOUT"] = "30"  # Add timeout for face processing
        
        # Start the Flask server
        proc = subprocess.Popen(
            [python_executable, "-m", "flask", "run", "--host", host, "--port", str(port)],
            env=flask_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered output
        )
        
        # Give the process a moment to start
        time.sleep(1)
        if proc.poll() is not None:
            # Process has already terminated
            stdout, stderr = proc.communicate()
            print_status("Server failed to start", "error")
            print("\nError details:")
            if stderr:
                print(stderr)
                logging.error(f"Server stderr: {stderr}")
            sys.exit(1)
            
    except Exception as e:
        print_status(f"Failed to start Flask application: {e}", "error")
        logging.exception("Failed to start Flask application")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Wait for the server to initialize
    print_status("Waiting for server to initialize...")
    max_retries = 15
    retries = 0
    server_ready = False
    
    while retries < max_retries:
        if is_port_in_use(port):
            print_status("Server is running successfully", "success")
            server_ready = True
            break
        retries += 1
        sys.stdout.write(f"\rInitializing... {'.' * retries}")
        sys.stdout.flush()
        time.sleep(0.5)

    print()  # New line after progress indicator

    if not server_ready:
        print_status("Server did not start in the expected time", "error")
        print_status("Check the console output for more details", "info")
        input("\nPress Enter to exit...")
        proc.terminate()
        sys.exit(1)

    # Open the browser
    print_status("Opening web browser...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print_status(f"Failed to open browser: {e}", "error")
        print_status("Please open manually: " + url, "info")

    # Create a thread to monitor for the 'Q' key press
    quit_thread = threading.Thread(target=check_for_quit, args=(proc,), daemon=True)
    quit_thread.start()
    
    # Create a thread to read stderr and stdout
    def output_reader(stream, prefix):
        for line in stream:
            line = line.strip()
            if line:
                if "error" in line.lower() or "exception" in line.lower():
                    logging.error(f"{prefix}: {line}")
                    print(f"[ERROR] {prefix}: {line}")
                elif debug_mode or "warn" in line.lower():
                    logging.info(f"{prefix}: {line}")
                    print(f"{prefix}: {line}")
    
    stdout_thread = threading.Thread(
        target=output_reader,
        args=(proc.stdout, "STDOUT"),
        daemon=True
    )
    stderr_thread = threading.Thread(
        target=output_reader,
        args=(proc.stderr, "STDERR"),
        daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    try:
        # Wait for process to finish
        proc.wait()
        
        # If we get here, process has ended
        return_code = proc.returncode
        print_status(f"Server process exited with code {return_code}", 
                    "success" if return_code == 0 else "error")
        
    except KeyboardInterrupt:
        print_status("\nShutting down server...", "info")
        proc.terminate()
        try:
            proc.wait(timeout=5)
            print_status("Server stopped successfully", "success")
        except subprocess.TimeoutExpired:
            print_status("Server not responding, forcing shutdown", "warning")
            proc.kill()
        
    print("\nThank you for using NEUAI Recognition System!")
    # Use os._exit to truly exit and return control to the batch file
    os._exit(0)
