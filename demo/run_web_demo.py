"""Run the local web demo and its APIs together."""
import os
from pathlib import Path
import subprocess
import sys

from console.services import running_services, stop


if __name__ == "__main__":
    print("Starting Faro's ten local APIs…", flush=True)
    with running_services() as urls:
        print("All ten APIs are ready. Open http://localhost:8501", flush=True)
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(Path(__file__).parent / "web/app.py"),
             "--server.address=127.0.0.1", "--server.headless=true", "--browser.gatherUsageStats=false"],
            cwd=Path(__file__).resolve().parent,
            env={**os.environ, **{f"FARO_{name.upper()}_URL": url for name, url in urls.items()}})
        try:
            process.wait()
        except KeyboardInterrupt:
            pass
        finally:
            stop(process)
