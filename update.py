import os
import subprocess

def check_for_updates():
    result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
    if 'Already up to date.' in result.stdout:
        print("No updates available.")
    else:
        print("Updates applied. Please restart the application.")

if __name__ == '__main__':
    check_for_updates()