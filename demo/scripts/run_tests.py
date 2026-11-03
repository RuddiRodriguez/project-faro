"""Run every unittest directory in its own process to avoid module-name collisions."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
folders = sorted(p for p in ROOT.rglob("tests") if p.is_dir() and any(p.glob("test_*.py"))
                 and not any(part in ("venv", "local_data", "__pycache__") for part in p.parts))
failed = []
for folder in folders:
    print(f"\nTests: {folder.relative_to(ROOT)}", flush=True)
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(folder), "-v"],
                            cwd=ROOT,env={**os.environ,"FARO_RUN_LIVE_TESTS":os.getenv("FARO_RUN_LIVE_TESTS","0")})
    if result.returncode:
        failed.append(str(folder.relative_to(ROOT)))
print("\nFailed suites:", failed or "none")
sys.exit(bool(failed))
