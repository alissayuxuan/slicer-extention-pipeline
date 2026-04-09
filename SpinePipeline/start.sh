#!/bin/bash
export PYTHONUNBUFFERED=1    # prints sofort ausgeben

Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!

DISPLAY=:99 /home/student/alissa/slicer/Slicer-5.10.0-linux-amd64/Slicer \
    --no-main-window \
    --no-splash \
    --additional-module-paths /home/student/alissa/SlicerExtension/SpinePipeline/SpinePipeline \
    --python-script /home/student/alissa/SlicerExtension/SpinePipeline/run_on_server.py \
    -- \
    /home/student/alissa/SlicerExtension/SpinePipeline/SpinePipeline/data/dataset-test \
    /home/student/miniconda3/envs/slicer_osim/bin/python3 \
    2>&1 | tee /home/student/alissa/pipeline.log

kill $XVFB_PID