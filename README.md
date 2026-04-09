# SpinePipeline — 3D Slicer Extension


## Requirements

- 3D Slicer
- conda / Anaconda
- Python (inside conda) 

**Note:** OpenSim is only installable via the `opensim-org` conda channel — it cannot be installed with pip. The provided `slicer_osim.yml` handles this automatically.

---

## Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/alissayuxuan/slicer-extention-pipeline.git
```

This gives you the following structure:

```
SpinePipeline/
├── slicer_osim_linux.yml    ← conda environment definition for linux
├── slicer_osim_windows.yml  ← conda environment definition for windows
├── run_on_server.py         ← headless launcher (Linux server)
├── start.sh                 ← shell script for headless start
└── SpinePipeline/
    ├── SpinePipeline.py     ← main extension module
    ├── Resources/
    │   └── UI/
    │       └── SpinePipeline.ui
    └── lib/
        ├── preprocessing_pipeline.py
        └── opensim_pipeline/
            └── ...
        └── slicer_pipeline/
            └── ...
```

---

### Step 2: Load the extension in 3D Slicer

1. Open 3D Slicer
2. Go to **Edit → Application Settings → Modules**
3. Under **Additional module paths**, click the **add** button
4. Navigate to and select the **inner** `SpinePipeline/` folder (the one containing `SpinePipeline.py`):
   ```
   /path/to/SpinePipeline/SpinePipeline/
   ```
5. Click **OK** and **restart Slicer**

After restart, find the module via **Modules → Examples → SpinePipeline**.

![folder_structure](figures/slicer_module_readme.png?raw=true)

---

### Step 3: Create the conda environment

For windows users:
```bash
conda env create -f slicer_osim_windows.yml
```

For linux users:
```bash
conda env create -f slicer_osim_linux.yml
```

This installs all required dependencies, including `opensim`, `TPTBox`, `pandas`, `scipy`, `lxml`, and `openpyxl` into a conda environment named `slicer_osim`.

After installation, find the path to the Python executable in the new environment:

```bash
# Linux / macOS:
conda activate slicer_osim
which python3
# → e.g. /home/user/anaconda3/envs/slicer_osim/bin/python3

# Or without activating:
conda env list
# slicer_osim  /home/user/anaconda3/envs/slicer_osim
```

Save this path — you will need to enter it in the extension GUI.

---

## Dataset Structure

SpinePipeline expects your data to be organized as follows:

![folder_structure](figures/folder_structure.jpg?raw=true)

To process a subject, we need 
- derivatives: segmentations of the full vertebra and the subregions (segmentation pipeline spineps https://github.com/Hendrik-code/spineps)
- output_muscles: muscle segmentation
- rawdata: raw CT
- _Stats file: including patient_id, age, sex, height (in cm), mass of the subjects

## Usage

### In the 3D Slicer GUI

1. Open the **SpinePipeline** module
2. Fill in the following fields:

   | Field | Description | Example |
   |---|---|---|
   | **Data Folder** | Root folder containing patient subfolders | `/data/dataset/` |
   | **Conda Python** | Path to Python in your `slicer_osim` conda env | `/home/user/anaconda3/envs/slicer_osim/bin/python3` |

3. Click **Run Pipeline**

Progress and log output appear in the Slicer Python console.

---

### Headless (Linux server, no display)

This mode is intended for remote Linux servers accessed via SSH, where no graphical interface is available. The two scripts `start.sh` and `run_on_server.py` work together:

- **`start.sh`** — starts Xvfb (virtual display), launches Slicer headlessly, and passes the pipeline arguments through to `run_on_server.py`
- **`run_on_server.py`** — runs inside Slicer's Python, loads the extension, and calls `SpinePipelineLogic.process()`

#### 1. Install 3D Slicer on the server

Download the Linux build from [https://download.slicer.org](https://download.slicer.org) and unpack it.

Example (Linux Slicer 5.10.0):

```bash
wget "https://download.slicer.org/bitstream/6911b598ac7b1c95e7934427" -O slicer.tar.gz
tar -xzf slicer.tar.gz
```

Make sure you have Xvfb (X Virtual Framebuffer) installed. It's a virtual display server that simulates a screen in memory, allowing graphical applications like 3D Slicer to run on a headless server without a physical monitor or display:

```bash
sudo apt-get install xvfb
```

You might also need to install the following X11/Qt-libraries:

```bash
sudo apt-get install -y libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0 libpcre2-16-0 libglib2.0-0 libpulse-mainloop-glib0 libnss3 libxcomposite1 libxrender1 libxrandr2 libfontconfig1 libxcursor1 libxi6 libxtst6 libasound2 libopengl0 libglu1
```

#### 2. Adapt the paths in `start.sh`

Open `start.sh` and update the hardcoded paths to match your server setup:

```bash
# Path to your Slicer executable:
/home/<user>/slicer/Slicer-5.10.0-linux-amd64/Slicer

# Path to the inner SpinePipeline module folder (containing SpinePipeline.py):
--additional-module-paths /path/to/SpinePipeline/SpinePipeline

# Path to run_on_server.py:
--python-script /path/to/SpinePipeline/run_on_server.py
```

Also update the two pipeline arguments passed after `--`:

```bash
-- \
/path/to/your/dataset \
/path/to/anaconda3/envs/slicer_osim/bin/python3
```

#### 3. Run the pipeline

Make `start.sh` executable and launch it:

```bash
chmod +x start.sh

# Run in the foreground (log output goes to pipeline.log and stdout):
bash start.sh

# Or in the background so it keeps running after SSH disconnect:
nohup bash start.sh > pipeline.log 2>&1 &
```

(optional) Monitor progress with:

```bash
tail -f pipeline.log
```

> **How it works internally:** `start.sh` starts Xvfb on display `:99`, then launches Slicer with `--no-main-window` and `--python-script run_on_server.py`. Slicer executes `run_on_server.py`, which loads the extension via `importlib` and calls `SpinePipelineLogic.process(data_path, conda_python)` directly — no GUI required.

---

## Architecture

```
SpinePipeline.py (Slicer module)
│
├── SpinePipelineWidget       → GUI: input fields, Run button
│
└── SpinePipelineLogic        → orchestrates the pipeline
    │
    ├── _validate_conda_python()
    │     Checks that the provided conda Python path is valid
    │     and that opensim is importable from it
    │
    ├── subprocess → preprocessing_pipeline.py
    │     Runs in the conda environment (outside Slicer)
    │     because TPTBox uses ProcessPoolExecutor, which
    │     conflicts with Slicer's Qt runtime.
    │     Communicates results via: derivatives/<id>/preproc_result.json
    │
    ├── slicer_pipeline_TUM.py
    │     Runs inside Slicer's Python (via script call)
    │     Reads preproc_result.json, performs Slicer-based
    │     calculations, writes opensim_input.json
    │
    └── subprocess → Header_CreateModel_3D.py
          Runs in the conda environment (outside Slicer)
          Needs a clean environment (strips PYTHONHOME,
          PYTHONPATH, LD_LIBRARY_PATH from Slicer).
          Generates OpenSim models.
```

**Why subprocesses?**

Slicer ships its own isolated Python environment. Two key libraries cannot run inside it:
- **TPTBox** uses `ProcessPoolExecutor` internally, which conflicts with Slicer's Qt-modified `sys.stdin`.
- **OpenSim** can only be installed via the `opensim-org` conda channel, not via Slicer's pip.

Both are therefore executed as external subprocesses using the user-supplied conda Python.

---


## Notes

- **Muscle segmentation** steps are currently disabled due to unavailability of muscle segmentation data. The pipeline runs with generic baseline muscle parameters.
- The extension has been developed and tested on **Linux (Ubuntu 22.04)** with **Slicer 5.10.0**. Windows support is not guaranteed.
