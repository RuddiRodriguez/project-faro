"""Start a private local set of Faro APIs for one console run."""
from contextlib import ExitStack, contextmanager
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx


DEMO = Path(__file__).resolve().parents[1]
SERVICES = ("gate", "connector", "thread", "scout", "signal", "guide", "bridge", "shield", "voice", "compass")


@contextmanager
def running_services():
    with ExitStack() as stack:
        processes = []
        urls = {}
        for name in SERVICES:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                listener.listen()
                fd = listener.fileno()
                url = f"http://127.0.0.1:{listener.getsockname()[1]}"
                settings = {f"FARO_{s.upper()}_URL": u for s, u in urls.items()}
                process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", f"{name}_api.infer:app",
                     "--fd", str(fd), "--log-level", "error", "--no-access-log"],
                    pass_fds=(fd,), cwd=DEMO, env={**os.environ, **settings})
                urls[name] = url
                processes.append((name, process))
                stack.callback(stop, process)
        deadline = time.monotonic() + 240
        with httpx.Client(timeout=1, trust_env=False) as client:
            for name, process in processes:
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError(f"{name} stopped during startup.")
                    try:
                        if client.get(urls[name] + "/openapi.json").is_success:
                            break
                    except httpx.RequestError:
                        pass
                    time.sleep(0.15)
                else:
                    raise RuntimeError(f"{name} did not become ready.")
        yield urls


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
