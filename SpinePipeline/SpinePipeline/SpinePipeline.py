import logging
import os

# Alissa
import sys
sys.path.insert(0, os.path.dirname(__file__))


from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

import qt # Alissa


#
# SpinePipeline
#

# TODO: METADATA - Name, Category, Description

class SpinePipeline(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("SpinePipeline")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#SpinePipeline">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # SpinePipeline1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="SpinePipeline",
        sampleName="SpinePipeline1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "SpinePipeline1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="SpinePipeline1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="SpinePipeline1",
    )

    # SpinePipeline2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="SpinePipeline",
        sampleName="SpinePipeline2",
        thumbnailFileName=os.path.join(iconsPath, "SpinePipeline2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="SpinePipeline2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="SpinePipeline2",
    )


#
# SpinePipelineParameterNode
#


@parameterNodeWrapper
class SpinePipelineParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# SpinePipelineWidget
#

# TODO: GUI

class SpinePipelineWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/SpinePipeline.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = SpinePipelineLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        # TODO: do I need this?

    def setParameterNode(self, inputParameterNode: Optional[SpinePipelineParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        
        self.ui.applyButton.toolTip = "Run Spine Pipeline"
        self.ui.applyButton.enabled = True

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""

        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
            data_path = self.ui.dataPathLineEdit.currentPath 
            conda_path = self.ui.condaPythonLineEdit.currentPath
            
            if not data_path:
                slicer.util.errorDisplay("Please specify a valid data path.")
                return

            if not conda_path:
                slicer.util.errorDisplay(
                    "Please specify a valid path to conda python.\n"
                    "e.g. ~/anaconda3/envs/slicer_osim/bin/python3"
                )
                return
            
            self.logic.process(data_path, conda_path)

    def onDownloadEnvButtonWindows(self) -> None:
        self._downloadEnvFile(windows=True)

    def onDownloadEnvButtonLinux(self) -> None:
        self._downloadEnvFile(windows=False)

    def _downloadEnvFile(self, windows: bool) -> None:
        """Copies the seleted slicer_osim.yml to the user selected location"""
        import shutil
        from pathlib import Path

        if windows:
            yml_filename = "slicer_osim_windows.yml"
            install_cmd  = "conda env create -f slicer_osim_windows.yml"
            python_hint  = r"C:\Users\<user>\anaconda3\envs\slicer_osim\python.exe"
            which_cmd    = "where python"
        else:
            yml_filename = "slicer_osim_linux.yml"
            install_cmd  = "conda env create -f slicer_osim_linux.yml"
            python_hint  = "~/anaconda3/envs\slicer_osim\bin\python3"
            which_cmd    = "which python3"

        # finding file
        env_yml_source = Path(__file__).parent.parent / yml_filename
        if not env_yml_source.exists():
            slicer.util.errorDisplay(
                f"{yml_filename} nicht gefunden:\n{env_yml_source}\n\n"
                "Stelle sicher dass die Datei im Extension-Ordner liegt."
            )
            return

        # user selects storage location 
        save_path = qt.QFileDialog.getSaveFileName(
            None,
            f"Save {yml_filename}",
            str(Path.home() / yml_filename),
            "YAML Files (*.yml)"
        )
        if not save_path:
            return  # User cancelled

        shutil.copy(str(env_yml_source), save_path)

        slicer.util.infoDisplay(
            f"{yml_filename} saved to:\n{save_path}\n\n"
            f"Open a terminal and run:\n\n"
            f"  conda activate base\n"
            f"  {install_cmd}\n\n"
            f"Then find the Python path:\n\n"
            f"  conda activate slicer_osim\n"
            f"  {which_cmd}\n\n"
            f"Example path:\n"
            f"  {python_hint}\n\n"
            f"Enter this path in the 'Conda Python path' field.",
            windowTitle="Conda Environment Setup"
        )


#
# SpinePipelineLogic
#

# TODO: LOGIC -  pipeline implementation

class SpinePipelineLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return SpinePipelineParameterNode(super().getParameterNode())

    # Code to create a python env using python that is installed on the computer -> but now I
    # need to install opensim and it can only be installed via conda -> python venv not necessary
    """
    @classmethod
    def _setup_venv(cls):
        import subprocess
        import shutil
        import os
        from pathlib import Path

        venv_dir = Path(__file__).parent / "venv"
        is_windows = sys.platform == "win32"
        python_in_venv = venv_dir / ("Scripts/python.exe" if is_windows else "bin/python")

        if python_in_venv.exists():
            print("[SpinePipeline] Venv bereits vorhanden, überspringe Setup.")
            return str(python_in_venv)

        system_python = cls._find_system_python()

        # Slicer-Umgebungsvariablen bereinigen
        clean_env = cls._get_clean_env()

        print(f"[SpinePipeline] Erstelle venv in: {venv_dir}")
        try:
            subprocess.run(
                [system_python, '-m', 'venv', str(venv_dir)],
                check=True,
                capture_output=True,
                text=True,
                env=clean_env   # <-- bereinigtes Environment übergeben
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Venv-Erstellung fehlgeschlagen:\n{e.stderr}\n"
                "Stelle sicher, dass das Python-venv-Modul installiert ist:\n"
                "  Linux: sudo apt install python3-venv\n"
                "  Mac:   brew install python3"
            )

        print("[SpinePipeline] Upgrade pip...")
        try:
            subprocess.run(
                [str(python_in_venv), '-m', 'pip', 'install', '--upgrade', 'pip'],
                check=True,
                capture_output=True,
                text=True,
                env=clean_env   # <-- auch hier
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"pip-Upgrade fehlgeschlagen:\n{e.stderr}")

        packages = ['TPTBox', 'lxml', 'scipy', 'pandas', 'openpyxl']
        print(f"[SpinePipeline] Installiere Pakete: {packages}")
        try:
            result = subprocess.run(
                [str(python_in_venv), '-m', 'pip', 'install'] + packages,
                check=True,
                capture_output=True,
                text=True,
                env=clean_env   # <-- auch hier
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            shutil.rmtree(venv_dir, ignore_errors=True)
            raise RuntimeError(
                f"Paket-Installation fehlgeschlagen:\n{e.stderr}\n"
                "Prüfe deine Internetverbindung und versuche es erneut."
            )

        print("[SpinePipeline] Venv-Setup erfolgreich abgeschlossen.")
        return str(python_in_venv)
    """

    @staticmethod
    def _get_clean_env():
        """
        Returns a cleaned-up copy of the environment variables,
        excluding Slicer-specific Python variables that might confuse the system Python.
        """
        import os
        env = os.environ.copy()

        # These variables override where Python looks for its libraries
        for var in ['PYTHONHOME', 'PYTHONPATH', 'PYTHONSTARTUP', 'PYTHONNOUSERSITE']:
            env.pop(var, None)

        # Remove slicer-specific library paths from LD_LIBRARY_PATH
        if 'LD_LIBRARY_PATH' in env:
            paths = env['LD_LIBRARY_PATH'].split(':')
            clean_paths = [p for p in paths if 'slicer' not in p.lower() and 'Slicer' not in p]
            if clean_paths:
                env['LD_LIBRARY_PATH'] = ':'.join(clean_paths)
            else:
                del env['LD_LIBRARY_PATH']

        return env
    
    # Finds a suitable system python (was necessary for the python env) -> not needed anymore
    """
    @staticmethod
    def _find_system_python():
        ""
        Find a suitable Python system (>= 3.9) that is not Slicer's Python.
        Throws a RuntimeError with clear instructions if none are found.
        ""
        import subprocess
        import shutil

        is_windows = sys.platform == "win32"

        if is_windows:
            candidates = ['python3.12', 'python3.11', 'python3.10', 'python3.9', 'python3', 'python']
        else:
            candidates = ['python3.12', 'python3.11', 'python3.10', 'python3.9', 'python3', 'python']

        slicer_executable = sys.executable  # z.B. .../Slicer-5.x/bin/PythonSlicer

        for candidate in candidates:
            path = shutil.which(candidate)
            if not path:
                continue

            # Slicer-eigenes Python ausschließen
            if path == slicer_executable:
                continue
            if 'slicer' in path.lower():
                continue

            # Prüfen: läuft es und ist es neu genug?
            try:
                result = subprocess.run(
                    [path, '-c',
                    'import sys; assert sys.version_info >= (3, 9), "zu alt"; print(sys.version)'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"[SpinePipeline] System-Python gefunden: {path} ({version})")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        # Nichts gefunden → klare Fehlermeldung
        raise RuntimeError(
            "Kein geeignetes System-Python (>= 3.9) gefunden.\n\n"
            "Bitte installiere Python 3.10 oder neuer:\n"
            "  Linux:   sudo apt install python3 python3-venv\n"
            "  Mac:     brew install python3\n"
            "  Windows: https://www.python.org/downloads/\n\n"
            "Starte Slicer danach neu und versuche es erneut."
        )
    """

    # idea now: let the user install the conda env and pass its python through the input
    # start the conda and run the pipeline
    @classmethod
    def _validate_conda_python(cls, conda_python_path: str) -> str:
        """
        Validates whether the given python-path is valid and whether opensim is available.
        No venv necessary - direct use of conda environment.
        """
        import subprocess
        from pathlib import Path

        path = Path(conda_python_path)

        # does the path exist?
        if not path.exists():
            raise RuntimeError(
                f"Python couldn't be found: {conda_python_path}\n\n"
                "Please create the conda environment:\n"
                "  conda env create -f environment.yml\n"
                "and enter the python path:\n"
                "  ~/anaconda3/envs/slicer_osim/bin/python3"
            )

        # Is opensim installed?
        result = subprocess.run(
            [str(path), '-c', 'import opensim; print("opensim ok")'],
            capture_output=True,
            text=True,
            env=cls._get_clean_env()
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"opensim couldn't be found in the given environment!\n"
                f"path: {conda_python_path}\n\n"
                "Make sure the environment was correctly installed:\n"
                "  conda env create -f environment.yml"
            )

        print(f"[SpinePipeline] conda Python validated: {conda_python_path}")
        return str(path)

    def process(self, data_path: str, conda_path: str) -> None:

        
        import time
        from pathlib import Path
        from lib.utils_main import convert_excel_to_json, create_base_setup, create_patient_setup
        import json
        import shutil
        import subprocess
        import tempfile

        # Pfad zum slicer_pipeline_3d Ordner ins sys.path eintragen
        slicer_pipeline_dir = os.path.join(os.path.dirname(__file__), "lib", "slicer", "slicer_pipeline_3d")
        if slicer_pipeline_dir not in sys.path:
            sys.path.insert(0, slicer_pipeline_dir)

        from lib.slicer.slicer_pipeline_3d.slicer_pipeline_TUM import main as slicer_pipeline_main
        import re

        data_path = Path(data_path)          

        #  create venv
        # python_exe = self._setup_venv()

        # validate conda Python
        python_exe = self._validate_conda_python(conda_path)
    

        # defines paths to pipelines and base model and setup folders
        #source_dir = Path.cwd()
        source_dir = Path(__file__).parent
        preprocessing_pipeline = Path(source_dir)/"lib/preprocessing_pipeline.py"
        osim_pipeline = Path(source_dir)/"lib/opensim_pipeline/opensim_pipeline_3d/Header_CreateModel_3D.py"
        base_model_dir = Path(source_dir)/"lib/opensim_pipeline/base/model"
        base_setup_dir = Path(source_dir)/"lib/opensim_pipeline/base/setup"
        dir_json = None
        base_setup = None
        patient_setup = None

        # Find Subject Statistics json: if Stats in excel format, convert to json. If Stats in json format, read directly.
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith('_Stats.json'):
                    dir_json = Path (root) / file
                elif file.endswith('_Stats.xlsx') and dir_json is None:
                    dir_xlsx = Path (root) / file
                    dir_json = convert_excel_to_json(dir_xlsx)

        
        with open(dir_json, 'r') as f:
            subj_stats = json.load(f)

        
        tmp_dir = Path(tempfile.mkdtemp(prefix="SpinePipeline_"))    

        try:
            # extract all demographic info for each subject -> needed for later pipelines
            for entry in subj_stats:

                patient_id = entry.get('Subject')
                age        = str(entry.get('Age'))
                sex        = str(entry.get('Sex'))
                height     = str(entry.get('Height (cm)'))
                weight     = str(entry.get('Mass'))

                derivatives_path = data_path / 'derivatives'
                patient_deriv_path = derivatives_path / patient_id
                osim_file_path = patient_deriv_path/f"sub-{patient_id}_osim_info.json"


                print("Pipeline gestartet")
                slicer.app.processEvents()

                preproc_result_path = tmp_dir / str(patient_id) / "preproc_result.json"
                
                preproc = subprocess.run(
                    [str(python_exe), 
                    str(preprocessing_pipeline), 
                    data_path, str(preproc_result_path), patient_id],
                    capture_output=False,
                    text=True,
                    env=self._get_clean_env()
                )

                if preproc.returncode != 0:
                    print("Preprocessing failed!")
                    return

                print("Preprocessing finished!")
                slicer.app.processEvents()

                # Read Results from Preprocessing Pipeline

                if not preproc_result_path.exists():
                    raise RuntimeError(
                        f"Cannot find preprocessing result path: {preproc_result_path}\n"
                    )

                with open(preproc_result_path) as f:
                    preproc_result = json.load(f)

                # Extract paths
                volume_filename           = Path(preproc_result["volume_filename"])           if preproc_result["volume_filename"]           else None
                dir_raw                   = Path(preproc_result["dir_raw"])                   if preproc_result["dir_raw"]                   else None
                vb_segmentation_filename  = Path(preproc_result["vb_segmentation_filename"])  if preproc_result["vb_segmentation_filename"]  else None
                muscle_segmentation_filename = Path(preproc_result["muscle_segmentation_clean_filename"]) if preproc_result["muscle_segmentation_clean_filename"] else None
                vertebra_properties_filename = Path(preproc_result["vertebra_properties_filename"])       if preproc_result["vertebra_properties_filename"]       else None
                osim_file                 = Path(preproc_result["osim_file"])                 if preproc_result["osim_file"]                 else None


                ################################################################################
                ######################## Slicer Pipeline #######################################
                ################################################################################
                
                # if all necessary files for Slicer pipeline are present and osim file doesn't exist yet, run Slicer pipeline.
                # Otherwise, skip to next subject (if osim file already exists, we assume that the Slicer pipeline has already been run 
                # and the subject can be further processed in the OpenSim pipeline).

                # Slicer Pipeline: takes segmentations and calculates 3D models and geometric properties -> creates an osim file
                if all([volume_filename, vb_segmentation_filename, muscle_segmentation_filename, vertebra_properties_filename]) and not osim_file:
        
                # ignore muscle segmentation for now (not available)
                #if all([volume_filename, vb_segmentation_filename, vertebra_properties_filename]) and not osim_file:
                    
                    try:
                        print(f"########## Start Slicer Pipeline for {patient_id} ##########")
                        
                        match = re.search(r'\d+', patient_id)
                        patient_id_int = int(match.group()) if match else None
                        slicer_pipeline_main(patient_id, patient_id_int, sex, height, weight, data_path,
                                volume_filename, muscle_segmentation_filename, vb_segmentation_filename, vertebra_properties_filename)
                        #slicer_pipeline_main(patient_id, patient_id_int, age, sex, height, weight, data_path,
                        #    volume_filename, vb_segmentation_filename, vertebra_properties_filename)
                        
                        print(f"########## Completed Slicer Pipeline for {patient_id} ##########")
                    
                    except Exception as e:
                        print(f"########## Slicer Pipeline for {patient_id} failed. Proceeding with the next subject. ##########")
                        print(f"Error: {e}")

                else:
                    if osim_file:
                        print("OpenSim file already exists")
                    print(f"########## \nSkipping {patient_id} \n##########")

                
                ################################################################################
                ############################# OpenSim Pipeline #################################
                ################################################################################

                # generate setup-files for OpenSim model
                # start OpenSim -> creates a biomechanical muscle-skeleton-model of the spine

                    # Only further process the subjects with the necessary files:
                    if osim_file_path.exists():
                        # Create models and results folder if not already existent
                        print(f"########## Start OpenSim Pipeline for {patient_id} ##########")
                        for subdir in ['models', 'results']:
                            path = data_path / subdir / patient_id
                            if not path.exists():
                                path.mkdir(parents=True, exist_ok=True)

                        base_setup = create_base_setup(patient_id, data_path, base_model_dir, base_setup_dir)
                        patient_setup = create_patient_setup(patient_id, data_path)

                        subprocess.run([str(python_exe), osim_pipeline, base_setup, patient_setup],
                                       env=self._get_clean_env())

                        print(f"########## Finished OpenSim Pipeline for {patient_id} ##########")

                    else:
                        print(f"No osim info file found for subject {patient_id}. Can't run opensim pipeline.")



        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            print(f"[SpinePipeline] delete temp-directory: {tmp_dir}")

     
   

#
# SpinePipelineTest
#


class SpinePipelineTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_SpinePipeline1()

    def test_SpinePipeline1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("SpinePipeline1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = SpinePipelineLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
