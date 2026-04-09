# run_on_server.py
import sys
import os

# Fix für stdin Problem
import io
sys.stdin = io.StringIO()


# ── Load Slicer Extension  ─────────────────────────────────────────────
extension_path = "/home/student/alissa/SlicerExtension/SpinePipeline/SpinePipeline"
sys.path.insert(0, extension_path)

lib_path = os.path.join(extension_path, "lib")
sys.path.insert(0, lib_path)

# ── Start Pipeline ───────────────────────────────────────────────────
data_path = sys.argv[1] if len(sys.argv) > 1 else "/home/student/alissa/OpenSim-Spine-Project/data/dataset-test"
conda_path = sys.argv[2] if len(sys.argv) > 2 else "/home/student/miniconda3/envs/slicer_osim/bin/python3"


import importlib.util
spec = importlib.util.spec_from_file_location(
    "SpinePipeline",
    os.path.join(extension_path, "SpinePipeline.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

logic = mod.SpinePipelineLogic()
logic.process(data_path, conda_path)

sys.exit(0)