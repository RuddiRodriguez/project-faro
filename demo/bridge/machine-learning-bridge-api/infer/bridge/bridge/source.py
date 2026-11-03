"""Read only the sources Connector exposes within Gate's permissions."""
import json
import os
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from utils.connector_client import sources as connected_sources
from bridge.connected import execute_connected


def snapshot_id(catalogue):
    return sha256(json.dumps(catalogue, sort_keys=True).encode()).hexdigest()


def catalogue(path, request):
    result = connected_sources(request.company_id, request.permitted_scope_ids)
    connected = {item.id: item.model_dump() for item in result.items}
    today = os.getenv("FARO_REFERENCE_DATE") or datetime.now(timezone.utc).date().isoformat()
    return dict(connected=connected, reference_date=today,
                scopes=request.permitted_scope_ids,
                data_version=snapshot_id(connected))


def run_read(expression, records, columns):
    worker = Path(__file__).with_name("worker.py")
    command = [sys.executable, "-I", str(worker)]
    proc = subprocess.run(command, input=json.dumps(dict(expression=expression, records=records, columns=columns)),
        text=True, capture_output=True, env={"OPENBLAS_NUM_THREADS":"1", "OMP_NUM_THREADS":"1"})
    if proc.returncode:
        raise ValueError(proc.stderr.strip() or "The dataframe read stopped.")
    return json.loads(proc.stdout)



def execute(path, request, read):
    return execute_connected(request, read, catalogue(path, request), run_read)
