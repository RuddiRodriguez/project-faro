"""Use one OpenMP runtime for FAISS and PyTorch in the demo's macOS environment."""
from importlib.util import find_spec
from pathlib import Path
import os
import sys


def share_openmp():
    if sys.platform != "darwin":
        return
    faiss_dir = Path(find_spec("faiss").origin).parent
    torch_dir = Path(find_spec("torch").origin).parent
    bundled = faiss_dir / ".dylibs/libomp.dylib"
    shared = torch_dir / "lib/libomp.dylib"
    if bundled.is_file() and shared.is_file() and not bundled.samefile(shared):
        bundled.replace(bundled.with_suffix(".dylib.original"))
        bundled.symlink_to(os.path.relpath(shared, bundled.parent))


if __name__ == "__main__":
    share_openmp()
