import subprocess
import sys
import time

def main():
    print("Starting Support Ticket AI System...")
    print("-> API will be at:        http://127.0.0.1:8000/docs")
    print("-> UI will be at:         http://127.0.0.1:8501")
    print("(Press Ctrl+C to stop both)\n")

    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"]
    )
    ui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.headless", "false"]
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down both servers...")
        api_process.terminate()
        ui_process.terminate()
        api_process.wait()
        ui_process.wait()
        print("Stopped.")


if __name__ == "__main__":
    main()